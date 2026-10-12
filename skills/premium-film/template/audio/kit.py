"""Shared audio helpers for audio/score.py, audio/sound.py and audio/mix.py.
All signals are 48 kHz stereo float32 arrays shaped (n, 2). Runs in the film-audio image:
  docker run --rm -v "$PWD":/p -w /p film-audio python audio/mix.py en

Contents
  Film            the film's timing for one cut, read from audio/cues.json (exported from src/film/timeline.ts)
  load/place/...  basic I/O and placement
  splice/...      editing a licensed stock track on its own bar grid (cuts, stop-time hits, frozen-chord bridges)
  Part/...        composing a licence-free score: General MIDI parts through FluidSynth, plus synth voices
  voice_chain, duck_curve, lookahead_limit, master   the mix and its loudness targets (−14 LUFS, ≤ −1 dBTP)
"""
import json
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def db(x):
    return 10 ** (x / 20)


def path(*p):
    return os.path.join(ROOT, *p)


# ---------------------------------------------------------------------------------------------------------- timing
def pchip(xs, ys):
    """Monotone cubic (Fritsch–Carlson) through the anchors: the same curve as src/film/voices.ts."""
    n = len(xs)
    h = [xs[k + 1] - xs[k] for k in range(n - 1)]
    s = [(ys[k + 1] - ys[k]) / h[k] for k in range(n - 1)]
    d = []
    for k in range(n):
        if k == 0:
            d.append(s[0])
        elif k == n - 1:
            d.append(s[n - 2])
        elif s[k - 1] * s[k] <= 0:
            d.append(0.0)
        else:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            d.append((w1 + w2) / (w1 / s[k - 1] + w2 / s[k]))

    def f(x):
        if x <= xs[0]:
            return ys[0] + (x - xs[0]) * d[0]
        if x >= xs[-1]:
            return ys[-1] + (x - xs[-1]) * d[-1]
        lo = int(np.searchsorted(xs, x, side="right")) - 1
        t = (x - xs[lo]) / h[lo]
        return (2 * t**3 - 3 * t**2 + 1) * ys[lo] + (t**3 - 2 * t**2 + t) * h[lo] * d[lo] + (-2 * t**3 + 3 * t**2) * ys[lo + 1] + (t**3 - t**2) * h[lo] * d[lo + 1]

    return f


class Film:
    """One cut's timing (a language code from the timeline, optionally a voice version) from audio/cues.json.
    Every time it returns is a global film second in THIS cut, so sound lands where the picture puts the moment."""

    def __init__(self, lang="", voice=""):
        c = json.load(open(path("audio", "cues.json"), encoding="utf-8"))
        lang = lang or c["langs"][0]
        self.lang, self.voice, self.raw = lang, voice, c
        self.scenes = c["scenes"][lang]
        self.order = c["order"]
        self.cues = c.get("cues", {})
        self.music = c.get("music", {})
        if voice:
            table = c["voices"][voice][lang]
            self.T = pchip([a for a, _ in table["anchors"]], [b for _, b in table["anchors"]])
            self.duration = float(table["duration"])
            self.vo = [(v["id"], float(table["vo"][v["id"]]), v.get("text", {}).get(lang, "")) for v in c["vo"]]
        else:
            self.T = lambda t: t
            self.duration = float(c["duration"][lang])
            self.vo = [(v["id"], float(v["at"][lang]), v.get("text", {}).get(lang, "")) for v in c["vo"]]
        self.N = int(round(self.duration * SR))

    def at(self, scene, local):
        """Global time of a scene-local moment."""
        return self.T(self.scenes[scene]["start"] + local)

    def cue(self, scene, name, default=None):
        """A named cue (src/film/timeline.ts CUES) as a global time; a language's override map applies to its cut."""
        sc = self.cues.get(scene, {})
        v = sc.get(self.lang, {}).get(name, sc.get(name, default)) if isinstance(sc.get(self.lang), dict) else sc.get(name, default)
        if v is None:
            raise KeyError(f"no cue {scene}.{name}")
        return self.at(scene, float(v))

    def m(self, name):
        """A music landmark (timeline M: [scene, scene-local seconds]) as a global time in this cut."""
        scene, local = self.music[name]
        return self.at(scene, float(local))

    def vo_file(self, vid):
        return path("audio", "vo", *([self.voice] if self.voice else []), self.lang, f"{vid}.wav")

    def suffix(self):
        return f"{self.lang}{'-' + self.voice if self.voice else ''}"


# ----------------------------------------------------------------------------------------------------------- basics
def load(p, sr=SR):
    """Any audio file as (n, 2) float32 at 48 kHz (mp3 via ffmpeg)."""
    if p.lower().endswith((".mp3", ".m4a", ".aac", ".ogg")):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    x, r = sf.read(p, dtype="float32", always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, 1)
    x = x[:, :2]
    if r != sr:
        g = np.gcd(r, sr)
        x = signal.resample_poly(x, sr // g, r // g, axis=0).astype(np.float32)
    return x


def place(buf, x, t, gain_db=0.0):
    """Adds x into buf starting at t seconds (clipped to the buffer)."""
    i = int(round(t * SR))
    x = x * db(gain_db)
    if i < 0:
        x, i = x[-i:], 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[: j - i]


def fade(x, fin=0.006, fout=0.006):
    """Short fades so nothing starts or stops on a hard edge (a hard edge clicks)."""
    x = x.copy()
    a, b = min(len(x) // 4, int(fin * SR)), min(len(x) // 4, int(fout * SR))
    if a > 0:
        x[:a] *= np.linspace(0, 1, a)[:, None]
    if b > 0:
        x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def loudness(x):
    import pyloudnorm as pyln

    return pyln.Meter(SR).integrated_loudness(x) if np.abs(x).max() > 1e-6 else -99.0


def true_peak_db(x):
    """True peak on a 4× oversampled copy (inter-sample peaks clip on playback even when samples don't)."""
    peak = 0.0
    for i in range(0, len(x), SR * 10):
        seg = x[max(0, i - 64): i + SR * 10 + 64].astype(np.float64)
        peak = max(peak, float(np.abs(signal.resample_poly(seg, 4, 1, axis=0)).max()))
    return 20 * np.log10(peak + 1e-12)


# --------------------------------------------------------------------------- editing a licensed stock track
def bar_grid(t0, bpm, beats_per_bar=4):
    """bar(k) = time of the k-th downbeat of a track whose first downbeat is at t0 (measure with tools/music_scan.py)."""
    bar = 60.0 / bpm * beats_per_bar
    return (lambda k: t0 + k * bar), bar


def splice(track, pieces, out_len, xf=0.03, pre=0.012):
    """Re-cuts a track. pieces = [(src_from, src_to, dst_at), ...] in seconds, normally whole bars of the track's
    grid. Each cut is made `pre` before the downbeat (keeps the attack) with equal-power crossfades of `xf`."""
    out = np.zeros((int(out_len * SR), 2), np.float32)
    for i, (a, b, at) in enumerate(pieces):
        s, e = int((a - pre) * SR), int((b - pre) * SR) + int(xf * SR)
        seg = track[max(0, s):e].copy()
        n = int(xf * SR)
        if i > 0:
            seg[:n] *= np.sin(np.linspace(0, np.pi / 2, n))[:, None]
        if i < len(pieces) - 1:
            seg[-n:] *= np.cos(np.linspace(0, np.pi / 2, n))[:, None]
        place(out, seg, at - pre)
    return out


def stop_hit(track, src_at, dur=2.4, hold=0.14, decay=0.32, wet=0.55):
    """A stop-time hit: the chord at src_at struck once, then the rhythm breaks off and only its reverb rings."""
    from pedalboard import Pedalboard, Reverb

    seg = track[int(src_at * SR): int((src_at + dur) * SR)].copy()
    tt = np.arange(len(seg)) / SR
    env = np.where(tt < hold, 1.0, np.exp(-(tt - hold) / decay))
    dry = seg * env[:, None]
    head = np.ascontiguousarray((seg[: int(0.5 * SR)] * env[: int(0.5 * SR), None]).T)
    verb = Pedalboard([Reverb(room_size=0.88, damping=0.35, wet_level=0.5, dry_level=0.0, width=1.0)])(head, SR, reset=True).T
    tail = np.zeros_like(seg)
    tail[: len(verb)] += verb[: len(seg)]
    out = dry * 1.05 + tail * wet
    fo = int(0.25 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return out


def freeze(track, src_at, length, swell_at=None, level_db=-7.0, seed=54):
    """A frozen chord: 0.4 s of the track at src_at held as a sustained pad for `length` seconds (spectral freeze).
    Use it to hand one piece of music to another: hold the last chord across the gap and let it swell into the new
    track's first downbeat (swell_at, seconds from the start) and fade under it, instead of stopping and starting."""
    import librosa

    src = track[int((src_at + 0.0) * SR): int((src_at + 0.4) * SR)].T
    NF, HOP = 4096, 1024
    mag = np.abs(librosa.stft(src, n_fft=NF, hop_length=HOP)).mean(-1)
    nfr = int(length * SR / HOP) + 4
    k = np.arange(mag.shape[-1])
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 2 * np.pi, (2, len(k)))[..., None] + 2 * np.pi * k[None, :, None] * HOP / NF * np.arange(nfr)[None, None, :]
    pad = librosa.istft(mag[..., None] * np.exp(1j * ph), hop_length=HOP).T[: int(length * SR)]
    tt = np.arange(len(pad)) / SR
    peak = swell_at if swell_at is not None else length * 0.7
    env = np.where(tt < peak, np.clip(tt / 0.35, 0, 1) * (0.55 + 0.45 * tt / max(peak, 1e-3)), np.cos(np.clip((tt - peak) / max(length - peak, 1e-3), 0, 1) * np.pi / 2) ** 2)
    pad *= env[:, None]
    ref = np.sqrt(np.mean(track[int(src_at * SR): int((src_at + 0.4) * SR)] ** 2))
    pad *= ref / (np.sqrt(np.mean(pad[pad.any(1)] ** 2)) + 1e-9) * db(level_db)
    return pad.astype(np.float32)


def open_filter(x, f0=6000.0, f1=20000.0, gain_db=(-2.0, 0.0)):
    """Accumulation: a low-pass that opens from f0 to f1 while the level climbs, across the whole of x (a build)."""
    import librosa

    D = librosa.stft(np.ascontiguousarray(x.T), n_fft=4096, hop_length=1024)
    freqs = librosa.fft_frequencies(sr=SR, n_fft=4096)
    u = np.linspace(0, 1, D.shape[-1])
    cutoff = f0 * (f1 / f0) ** (u**1.3)
    mask = 1 / (1 + (freqs[:, None] / cutoff[None, :]) ** 2)
    gain = db(gain_db[0] + (gain_db[1] - gain_db[0]) * u**1.2)
    y = librosa.istft(D * (mask * gain)[None], hop_length=1024, length=len(x)).T
    return y.astype(np.float32)


# ------------------------------------------------------------------------- composing a licence-free score
SF2 = next((p for p in ("/usr/share/sounds/sf2/MuseScore_General_Full.sf2", "/usr/share/sounds/sf2/MuseScore_General.sf2", "/usr/share/sounds/sf2/FluidR3_GM.sf2") if os.path.exists(p)), None)
# General MIDI programs that sound good through MuseScore General
GM = {"piano": 0, "celesta": 8, "glock": 9, "bells": 14, "cello": 42, "contrabass": 43, "pizz": 45, "harp": 46, "timpani": 47,
      "strings": 48, "strings2": 49, "choir": 52, "oohs": 53, "horn": 60, "brass": 61, "warm_pad": 89, "halo_pad": 94}
HUMAN = np.random.default_rng(57)


class Part:
    """Notes and controller moves for one General MIDI program, rendered through FluidSynth. Times are in film
    seconds; place chords on the film's cue times so the harmony moves with the picture."""

    def __init__(self, program, channel=0):
        self.program, self.channel, self.events = program, channel, []

    def note(self, t0, dur, pitch, vel=90, human=True):
        import mido

        if human:  # players are never exactly on the grid: a few ms of timing and a little velocity variation
            dt = float(np.clip(HUMAN.normal(0, 0.007), -0.018, 0.018))
            t0, dur = t0 + dt, max(0.03, dur - dt)
            vel = vel * (1 + float(np.clip(HUMAN.normal(0, 0.07), -0.15, 0.15)))
        self.events.append((t0, mido.Message("note_on", channel=self.channel, note=int(pitch), velocity=int(np.clip(vel, 1, 127)))))
        self.events.append((t0 + dur, mido.Message("note_off", channel=self.channel, note=int(pitch), velocity=0)))

    def chord(self, t0, dur, pitches, vel=80, spread=0.0):
        for k, p in enumerate(pitches):
            self.note(t0 + k * spread, max(0.05, dur - k * spread), p, vel)

    def cc(self, t0, num, val):
        import mido

        self.events.append((t0, mido.Message("control_change", channel=self.channel, control=num, value=int(np.clip(val, 0, 127)))))

    def dynamics(self, points, num=11):
        """Expression (CC11) through [(t, value 0–127), ...]: the score swells and settles with the story."""
        for (ta, va), (tb, vb) in zip(points, points[1:]):
            steps = max(2, int((tb - ta) * 10))
            for k in range(steps + 1):
                u = k / steps
                self.cc(ta + (tb - ta) * u, num, va + (vb - va) * u)

    def render(self, n):
        import mido

        assert SF2, "no General MIDI soundfont found (build the film-audio image)"
        mid = mido.MidiFile(ticks_per_beat=480)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))  # 120 bpm: 960 ticks per second
        tr.append(mido.Message("program_change", channel=self.channel, program=self.program, time=0))
        tr.append(mido.Message("control_change", channel=self.channel, control=91, value=0, time=0))  # no built-in reverb
        tr.append(mido.Message("control_change", channel=self.channel, control=93, value=0, time=0))
        last = 0
        for t0, msg in sorted(self.events, key=lambda e: (e[0], 0 if e[1].type == "note_off" else 1)):
            tick = int(round(max(0.0, t0) * 960))
            tr.append(msg.copy(time=tick - last))
            last = tick
        with tempfile.TemporaryDirectory() as d:
            mp, wp = os.path.join(d, "p.mid"), os.path.join(d, "p.wav")
            mid.save(mp)
            subprocess.run(["fluidsynth", "-ni", "-q", "-R", "0", "-C", "0", "-g", "0.7", "-r", str(SR), "-F", wp, SF2, mp], check=True)
            x, sr = sf.read(wp, dtype="float32", always_2d=True)
        out = np.zeros((n, 2), np.float32)
        m = min(n, len(x))
        out[:m] = x[:m, :2]
        return out


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def sine(freq, n):
    return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(np.asarray(freq, np.float64), (n,))) / SR)


def saw(freq, n, seed=0):
    """Band-limited sawtooth (polyBLEP)."""
    f = np.broadcast_to(np.asarray(freq, np.float64), (n,))
    dt = f / SR
    ph = (np.cumsum(dt) + np.random.default_rng(seed).random()) % 1.0
    blep = np.zeros(n)
    m1 = ph < dt
    x = ph[m1] / dt[m1]
    blep[m1] = x + x - x * x - 1
    m2 = ph > 1 - dt
    x = (ph[m2] - 1) / dt[m2]
    blep[m2] = x * x + x + x + 1
    return 2 * ph - 1 - blep


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "high", fs=SR, output="sos"), x, axis=0)


def stereo(m, width_ms=9.0):
    d = int(width_ms * SR / 1000)
    return np.stack([m, np.concatenate([np.zeros(d), m[:-d]]) if d else m], 1).astype(np.float32)


def env_ar(n, attack, release):
    t = np.arange(n) / SR
    total = n / SR
    return np.clip(t / max(attack, 1e-4), 0, 1) ** 2 * np.clip((total - t) / max(release, 1e-4), 0, 1) ** 2


def pad(pitches, dur, cutoff=2400, level=0.12, seed=0):
    """A soft synth pad (detuned saws, low-passed) for a chord held `dur` seconds."""
    n = int(dur * SR)
    m = np.zeros(n)
    for k, p in enumerate(pitches):
        for det in (-0.08, 0.0, 0.08):
            m += saw(midi_hz(p + det), n, seed + k) / (len(pitches) * 3)
    m = lp(m, cutoff, 2) * env_ar(n, min(0.8, dur / 3), min(1.2, dur / 3))
    return stereo(m * level)


def kick(level=0.9):
    """A soft cinematic kick: a pitch-dropping sine body and a short, band-limited click (nothing above ~6 kHz, so it
    never reads as a click artefact), with a 1 ms fade-in."""
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-t * 28)) / SR) * np.exp(-t * 7)
    nz = np.random.default_rng(3).standard_normal(n)
    click = signal.sosfilt(signal.butter(2, [900, 5000], "bandpass", fs=SR, output="sos"), nz) * np.exp(-t * 160) * 0.3
    m = np.tanh((body + click) * 1.5) * level
    f = int(0.001 * SR)
    m[:f] *= np.linspace(0, 1, f)
    return stereo(m, 0)


def sub(pitch, dur, level=0.35):
    n = int(dur * SR)
    return stereo(sine(midi_hz(pitch), n) * env_ar(n, 0.02, min(0.4, dur / 2)) * level, 0)


def hall(x, wet=0.32, hpf=120):
    from pedalboard import HighpassFilter, Pedalboard, Reverb

    return Pedalboard([HighpassFilter(hpf), Reverb(room_size=0.9, damping=0.5, wet_level=wet, dry_level=0.8, width=1.0)])(np.ascontiguousarray(x.T), SR).T


# ---------------------------------------------------------------------------------------------------- the mix
def voice_chain(x):
    """The narrator: rumble out, a little chest warmth and presence, sibilance tamed, firm compression that still
    lets each stressed syllable's attack through."""
    from pedalboard import Compressor, HighpassFilter, HighShelfFilter, LowShelfFilter, Pedalboard, PeakFilter

    chain = Pedalboard([
        HighpassFilter(75),
        LowShelfFilter(cutoff_frequency_hz=160, gain_db=1.5),
        PeakFilter(cutoff_frequency_hz=320, gain_db=-1.5, q=1.0),
        PeakFilter(cutoff_frequency_hz=3200, gain_db=1.8, q=0.9),
        PeakFilter(cutoff_frequency_hz=6800, gain_db=-3.0, q=2.2),
        HighShelfFilter(cutoff_frequency_hz=10000, gain_db=-0.5),
        Compressor(threshold_db=-22, ratio=3.0, attack_ms=9, release_ms=110),
    ])
    return chain(np.ascontiguousarray(x.T), SR).T


def smooth_gain(target_db, attack=0.18, release=1.1, block=64):
    """One-pole smoothing of an attenuation curve (dB, positive = down): fast-ish attack, slower release."""
    out = np.zeros(len(target_db), np.float32)
    y = 0.0
    ka, kr = np.exp(-block / (attack * SR)), np.exp(-block / (release * SR))
    for k in range(0, len(target_db), block):
        tg = target_db[k]
        c = ka if tg > y else kr
        y = c * y + (1 - c) * tg
        out[k:k + block] = y
    return out


def lookahead_limit(x, ceiling_db=-1.2, look=0.003, release=0.08):
    """Brick-wall limiter WITHOUT makeup gain (pedalboard's Limiter adds makeup gain and pushes the master up
    ~3 dB): the gain is already down when each 4×-oversampled peak arrives, then recovers smoothly."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d

    ceiling = db(ceiling_db)
    peak = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(1).reshape(-1, 4).max(1)[: len(x)]
    if len(peak) < len(x):
        peak = np.pad(peak, (0, len(x) - len(peak)), mode="edge")
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    L = int(look * SR)
    g = minimum_filter1d(need, size=2 * L + 1)
    r = np.exp(-1 / (release * SR))
    out = np.empty_like(g)
    y = 1.0
    for k in range(0, len(g), 32):
        m = g[k:k + 32].min()
        y = m if m < y else r**32 * y + (1 - r**32) * m
        out[k:k + 32] = np.minimum(y, g[k:k + 32])
    sm = np.minimum(uniform_filter1d(out, size=int(0.0015 * SR) | 1), need)
    return (x * sm[:, None]).astype(np.float32)


def master(mix, lufs=-14.0, ceiling_db=-2.0, tail=2.0):
    """Gentle glue, loudness to `lufs` (−14 LUFS suits YouTube, social and event playback) and a true-peak ceiling.
    Limiting lowers loudness a hair, so it normalises and limits a few times. The ceiling is −2 dBTP because AAC
    encoding raises peaks by up to ~1 dB: a −1.2 dBTP WAV measured −0.3 dBTP in the delivered MP4 (the release
    measures the MP4 and trims the gain if it still lands above −1)."""
    import warnings

    import pyloudnorm as pyln
    from pedalboard import Compressor, LowShelfFilter, Pedalboard

    warnings.filterwarnings("ignore", message="Possible clipped samples")  # the limiter right after takes care of it
    x = Pedalboard([LowShelfFilter(cutoff_frequency_hz=45, gain_db=-1.0), Compressor(threshold_db=-20, ratio=2.0, attack_ms=30, release_ms=300)])(np.ascontiguousarray(mix.T), SR).T
    meter = pyln.Meter(SR)
    for _ in range(3):
        x = pyln.normalize.loudness(x, meter.integrated_loudness(x), lufs)
        x = lookahead_limit(x, ceiling_db)
    if tail > 0:
        fo = int(tail * SR)
        x[-fo:] *= (np.linspace(1, 0, fo) ** 1.6)[:, None]
    return x.astype(np.float32)
