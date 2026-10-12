"""The final mix of one cut: narration + score + sound design → public/audio/mix-<lang>[-<voice>].wav (48 kHz, 24-bit,
−14 LUFS integrated, true peak ≤ −2 dBTP in the WAV, so the AAC in the MP4 stays ≤ −1), with stems in audio/build/stems-<cut>/ and a per-line balance table.

  docker run --rm -v "$PWD":/p -w /p film-audio python audio/mix.py [<lang>]       (default: the master language; VOICE=<name> for a voice version)

Reads audio/cues.json (export it first: npm run cues), the narration lines audio/vo[/<voice>]/<lang>/<id>.wav, the
score audio/build/score-<lang>[-<voice>].wav (audio/score.py) and the sound design in audio/sound.py.

How the balance works (each rule came from a mix that failed review):
  - the narrator goes through one voice chain, so lines recorded on different days sit together
  - the score is ducked PER LINE until it sits ~9 dB under that line (a fixed −7.5 dB duck left a dense trailer score
    1–9 dB LOUDER than the voice on some lines); short gaps between lines are bridged so the music doesn't pump
  - under the voice the score is also EQ-carved (260 Hz, 2.5 kHz) to make room for the words
  - sound effects get 6 ms fades (no clicks), tamed highs, and follow the duck a little less deeply
  - the master uses a look-ahead limiter without makeup gain (pedalboard's Limiter adds makeup gain: +3 dB surprise)
"""
import importlib.util
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
from kit import SR, db  # noqa: E402

VOICE = os.environ.get("VOICE", "")
film = kit.Film(sys.argv[1] if len(sys.argv) > 1 else "", VOICE)
LANG = film.lang
N = film.N
cut = film.suffix()


def film_module(name):
    p = kit.path("audio", f"{name}.py")
    if not os.path.exists(p):
        return None
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sound = film_module("sound")
DUCK = getattr(sound, "DUCK", {}) if sound else {}  # per-line voice-over-music margins, e.g. {"l15": 10.5}
LINE_GAIN = getattr(sound, "LINE_GAIN", {}) if sound else {}  # per-line narration gain in dB, e.g. a slogan riding a hit

# ------------------------------------------------------------------------------------------------- narration
vo = np.zeros((N, 2), np.float32)
lines = []
for vid, at, _text in film.vo:
    p = film.vo_file(vid)
    if not os.path.exists(p):
        print(f"WARNING: narration {os.path.relpath(p, kit.ROOT)} is missing; this mix leaves it out (a release refuses to ship without it)")
        continue
    x = kit.voice_chain(kit.load(p)) * db(LINE_GAIN.get(vid, 0.0))
    kit.place(vo, x, at)
    lines.append((vid, at, len(x) / SR))
vo *= db(-1.0)

# ----------------------------------------------------------------------------------------------------- score
score = np.zeros((N, 2), np.float32)
for name in (f"score-{cut}.wav", f"score-{LANG}.wav", "score.wav"):
    p = kit.path("audio", "build", name)
    if os.path.exists(p):
        s = kit.load(p)[:N]
        score[: len(s)] = s
        print("score:", os.path.relpath(p, kit.ROOT))
        break
else:
    print("WARNING: no score in audio/build/ (run audio/score.py); mixing without music")

# adaptive ducking: under each line the score comes down until it sits DUCK[id] (default 9) dB under the voice
target = np.zeros(N, np.float32)
spans = []
for vid, at, dur in lines:
    a, b = int((at + 0.1) * SR), int((at + dur - 0.25) * SR)
    lv, lm = kit.loudness(vo[a:b]), kit.loudness(score[a:b] * db(-3.0))
    need = float(np.clip(lm - (lv - DUCK.get(vid, 9.0)), 2.0, 20.0)) if lm > -70 else 0.0
    i0, i1 = int(max(0, at - 0.25) * SR), int(min(film.duration, at + dur + 0.15) * SR)
    target[i0:i1] = np.maximum(target[i0:i1], need)
    spans.append((at - 0.25, at + dur + 0.15))
# a gap shorter than 3.5 s between lines keeps 70% of the duck, so the music doesn't surge up and back down
for (a0, b0), (a1, b1) in zip(spans, spans[1:]):
    if 0 < a1 - b0 < 3.5:
        i0, i1 = int(b0 * SR), int(a1 * SR)
        target[i0:i1] = np.maximum(target[i0:i1], 0.7 * min(target[max(0, i0 - 1)], target[min(N - 1, i1 + 1)]))
duck = kit.smooth_gain(target)
from pedalboard import Compressor, HighShelfFilter, Pedalboard, PeakFilter  # noqa: E402

carve = Pedalboard([PeakFilter(cutoff_frequency_hz=260, gain_db=-3.0, q=0.9), PeakFilter(cutoff_frequency_hz=2500, gain_db=-3.5, q=0.8)])
score_eq = carve(np.ascontiguousarray(score.T), SR).T
w = np.clip(duck / 6.0, 0, 1)[:, None]
music = (score * (1 - w) + score_eq * w) * db(-duck)[:, None] * db(-3.0)
# even out the score's own loudest passages (they play without narration)
music = Pedalboard([Compressor(threshold_db=-24, ratio=2.6, attack_ms=60, release_ms=500)])(np.ascontiguousarray(music.T), SR).T * db(2.0)

# ---------------------------------------------------------------------------------------------- sound design
sfx = np.zeros((N, 2), np.float32)
events = sound.events(film) if sound and hasattr(sound, "events") else []
for t, x, g in events:
    kit.place(sfx, kit.fade(np.asarray(x, np.float32)), t, g)
sfx = Pedalboard([HighShelfFilter(cutoff_frequency_hz=6000, gain_db=-3.0), PeakFilter(cutoff_frequency_hz=9000, gain_db=-2.0, q=1.0)])(np.ascontiguousarray(sfx.T), SR).T
sfx *= db(-np.clip(duck - 2.0, 0, 14.0))[:, None]

# ---------------------------------------------------------------------------------------------------- master
mix = kit.master(vo + music + sfx)
os.makedirs(kit.path("public", "audio"), exist_ok=True)
stems = kit.path("audio", "build", f"stems-{cut}")
os.makedirs(stems, exist_ok=True)
out = kit.path("public", "audio", f"mix-{cut}.wav")
sf.write(out, mix, SR, subtype="PCM_24")
for name, x in (("vo", vo), ("music", music), ("sfx", sfx)):
    sf.write(os.path.join(stems, f"{name}.wav"), x.astype(np.float32), SR, subtype="PCM_24")

print(f"wrote {os.path.relpath(out, kit.ROOT)}: {film.duration:.2f} s, {kit.loudness(mix):.1f} LUFS, true peak {kit.true_peak_db(mix):.2f} dBTP, {len(lines)} lines, {len(events)} effects")
# per-line balance: the voice should sit ≥ 6 dB over the music on every line (≈ 9 dB is the target)
print(" line     at    voice  music  voice-music")
for vid, at, dur in lines:
    a, b = int((at + 0.15) * SR), int((at + dur - 0.3) * SR)
    lv, lm = kit.loudness(vo[a:b]), kit.loudness(music[a:b])
    flag = "  << music too loud" if lv - lm < 6 else ""
    print(f" {vid:6s} {at:6.1f}  {lv:6.1f} {lm:6.1f}  {lv - lm:6.1f}{flag}")
