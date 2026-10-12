"""Narration clean-up shared by the cutting tools and the release check.

Gemini's English TTS model (3.8-flash-lite-tts) ends every generation with ~0.12 s of full-scale noise right after
the room tone, and often puts a click on the very first samples; listeners hear it as "a super loud weird sound at
the end of a sentence". strip_artifacts() removes both; find_artifacts() reports any that remain (and any frame louder
than speech that is mostly hiss), so a release never ships one."""
import numpy as np

FRAME = 0.01  # s


def _frames_db(x, sr):
    m = x if x.ndim == 1 else x.mean(1)
    w = int(FRAME * sr)
    n = len(m) // w
    fr = m[: n * w].reshape(n, w)
    return w, 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)


def end_burst(x, sr):
    """Sample where a loud burst after near-silence ends the file, or None."""
    w, db = _frames_db(x, sr)
    n = len(db)
    k = n - 1
    while k > 0 and db[k] > -30 and n - 1 - k < 25:
        k -= 1
    if k == n - 1 or n - 1 - k >= 25:
        return None  # ends quietly, or ends in speech (no burst)
    if db[max(0, k - 2): k + 1].max() > -45:
        return None  # the loud ending follows speech, not silence
    return (k + 1) * w


def strip_artifacts(x, sr):
    """Silence the first samples (start click) and cut a trailing burst, with short fades."""
    x = x.copy()
    z, r = int(0.006 * sr), int(0.012 * sr)
    x[:z] = 0
    x[z: z + r] = (x[z: z + r].T * np.linspace(0, 1, r)).T
    b = end_burst(x, sr)
    if b is not None:
        x = x[: max(0, b - int(0.005 * sr))]
        fo = int(0.02 * sr)
        x[-fo:] = (x[-fo:].T * np.linspace(1, 0, fo)).T
    return x


def find_artifacts(x, sr):
    """Problems a listener would hear as a glitch: a trailing burst, or a frame louder than any speech."""
    issues = []
    b = end_burst(x, sr)
    if b is not None:
        issues.append(f"burst at the end ({b / sr:.2f} s)")
    m = x if x.ndim == 1 else x.mean(1)
    w, db = _frames_db(x, sr)
    f = np.fft.rfftfreq(w, 1 / sr)
    noisy = []
    for i in np.nonzero(db > -12)[0]:
        p = np.abs(np.fft.rfft(m[i * w: (i + 1) * w] * np.hanning(w))) ** 2
        if p[f > 4000].sum() / (p.sum() + 1e-12) > 0.3:  # loud and hissy: noise, not a voiced vowel
            noisy.append(i)
    if noisy:
        issues.append("loud noise at " + ", ".join(f"{i * FRAME:.2f} s" for i in noisy[:4]))
    return issues
