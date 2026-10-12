#!/usr/bin/env python3
"""Measures a soundtrack the way a picky listener hears it: audio_qa.py <mix.wav | video.mp4> [--sync t1,t2,...]

  loudness   integrated LUFS (target −14), true peak (≤ −1 dBTP), short-term range
  clicks     sharp high-frequency spikes against their surroundings (an effect starting on a hard edge, a bad splice)
  hiss       sustained energy above 9 kHz per 3 s window (a 99-second rising "fan" hiss once came from a reused
             variable that dragged the finale's riser into the middle of the film)
  holes      stretches quieter than −50 dBFS for over 1.5 s (dead air), and sudden level drops between sections
  --sync     for each given time (s), the distinct onsets within ±150 ms with their strength (the strongest = 100%):
             big visual hits should have an audible hit within a frame or two (+30–40 ms is encoder delay)
The assistant cannot hear: these numbers plus a reviewer's concrete flags stand in for ears, and the owner's ears
decide. Runs in the film-audio image."""
import subprocess
import sys

import numpy as np
import pyloudnorm as pyln
from scipy import signal

args = sys.argv[1:]
src = args[0]
SR = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
dur = len(x) / SR
meter = pyln.Meter(SR)
lufs = meter.integrated_loudness(x)
tp = 20 * np.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)
st = np.array([meter.integrated_loudness(x[i:i + 3 * SR]) for i in range(0, len(x) - 3 * SR, SR)])
st = st[st > -70]
print(f"{src}: {dur:.2f} s")
print(f"  loudness  {lufs:.1f} LUFS (target −14), true peak {tp:.2f} dBTP (≤ −1), short-term p10–p95 {np.percentile(st, 10):.1f}…{np.percentile(st, 95):.1f} LUFS")
flags = 0
# the delivery spec: −14 LUFS ±1, true peak ≤ −1 dBTP (measure the MP4: AAC raises peaks by up to ~1 dB)
if abs(lufs + 14) > 1:
    flags += 1
    print(f"  LOUDNESS  {lufs:.1f} LUFS is outside −14 ±1")
if tp > -1.0:
    flags += 1
    print(f"  PEAK      true peak {tp:.2f} dBTP is above −1 dBTP")
# clicks: an isolated spike in the band above 9 kHz that stands far above everything within ±10 ms (a hard edge, a bad
# splice, a sample jump). Consonants and noisy effects are bursts tens of ms long, so they don't qualify.
for ch in range(2):
    hp = signal.sosfilt(signal.butter(4, 9000, "high", fs=SR, output="sos"), x[:, ch])
    w = int(0.001 * SR)
    env = np.abs(hp[: len(hp) // w * w]).reshape(-1, w).max(1)
    from scipy.ndimage import maximum_filter1d
    around = np.maximum(maximum_filter1d(np.concatenate([[0.0] * 2, env[:-2]]), size=9, origin=4),
                        maximum_filter1d(np.concatenate([env[2:], [0.0] * 2]), size=9, origin=-4))
    idx = np.flatnonzero((env > 6 * (around + 1e-4)) & (env > 0.02))
    if len(idx):
        flags += len(idx)
        print(f"  clicks    ch{ch}: " + ", ".join(f"{i * w / SR:.3f}s" for i in idx[:20]))
# hiss
m = x.mean(1)
hpm = signal.sosfilt(signal.butter(4, 9000, "high", fs=SR, output="sos"), m)
w = 3 * SR
hiss = [(i / SR, 20 * np.log10(np.sqrt(np.mean(hpm[i:i + w] ** 2)) + 1e-9)) for i in range(0, len(m) - w, w)]
loud = [(t, v) for t, v in hiss if v > -30]
if loud:
    flags += len(loud)
    print("  hiss      >9 kHz above −30 dBFS at " + ", ".join(f"{t:.0f}s ({v:.0f})" for t, v in loud[:12]))
# holes and drops (1 s windows)
sec = np.array([20 * np.log10(np.sqrt(np.mean(m[i:i + SR] ** 2)) + 1e-9) for i in range(0, len(m) - SR, SR)])
run = 0
for i, v in enumerate(list(sec) + [0]):
    if v < -50:
        run += 1
        continue
    if run >= 2 and i - run > 0 and i < len(sec):
        flags += 1
        print(f"  hole      {i - run:.0f}–{i:.0f} s below −50 dBFS (dead air?)")
    run = 0
for i in range(2, len(sec) - 3):  # the last seconds are the ending fade
    if sec[i - 2] - sec[i] > 10 and sec[i] > -50 and sec[i + 1] < sec[i - 2] - 8:
        print(f"  drop      {i:.0f} s: level falls {sec[i - 2] - sec[i]:.0f} dB in 2 s (intended? a build that 'drops weirdly' at a section change)")
# sync
if "--sync" in args:
    times = [float(v) for v in args[args.index("--sync") + 1].split(",")]
    env = np.sqrt(np.convolve(m ** 2, np.ones(240) / 240, mode="same"))  # 5 ms RMS
    flux = np.maximum(0, np.diff(np.log(env[::48] + 1e-6)))  # 1 ms hop
    for t in times:
        a, b = int((t - 0.15) * 1000), int((t + 0.15) * 1000)
        if a < 0 or b >= len(flux):
            continue
        # every distinct onset, not just the strongest: a reverse swell's last rise, a hit's front edge and a boom's
        # body each make one, and the one that reads as "the hit" is for you to pick
        w = flux[a:b]
        pk, _ = signal.find_peaks(w, height=0.3 * w.max(), distance=20)
        pk = sorted(pk, key=lambda i: -w[i])[:3]
        print(f"  sync      {t:8.3f} s → onsets " + ", ".join(
            f"{(a + i) / 1000:.3f} s ({((a + i) / 1000 - t) * 1000:+.0f} ms, {w[i] / w.max():.0%})" for i in sorted(pk)))
print(f"  {flags} flags" + ("" if flags else " — clean"))
