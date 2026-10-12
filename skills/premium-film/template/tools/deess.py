#!/usr/bin/env python3
"""Tame harsh sibilants and plosives in narration lines: deess.py <wav...> (in place)
A punchy read can push an "s", "ch" or "t" loud enough to sound harsh (and to look like a glitch to tools/check_vo.py).
Above 4 kHz the line is turned down only where that band itself is loud (10 ms windows, fast attack, 40 ms release);
everything else passes untouched (the band split is zero-phase and sums back exactly).
Runs in the film-audio image: docker run --rm -v "$PWD":/p -w /p film-audio python tools/deess.py …"""
import sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt

CEIL = -18.0  # dBFS: the loudest the band above 4 kHz may be over any 10 ms
for path in sys.argv[1:]:
    x, sr = sf.read(path, dtype="float64")
    m = x if x.ndim == 1 else x.mean(1)
    high = sosfiltfilt(butter(4, 4000, "highpass", fs=sr, output="sos"), m)
    win = int(0.01 * sr)
    env = np.sqrt(np.convolve(np.pad(high ** 2, win, mode="edge"), np.ones(win) / win, mode="same")[win:-win] + 1e-12)
    gain = np.minimum(1.0, 10 ** (CEIL / 20) / env)
    # fast attack, slow release: the gain falls at once and recovers over ≈40 ms
    rel = np.exp(-1 / (0.04 * sr))
    g = np.empty_like(gain)
    cur = 1.0
    for i, v in enumerate(gain):
        cur = v if v < cur else cur * rel + v * (1 - rel)
        g[i] = cur
    k = int(0.002 * sr)
    g = np.convolve(np.pad(g, k, mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    out = m - high + high * g
    if (g < 0.999).any():
        sf.write(path, out.astype(np.float32), sr)
        print(f"{path}: up to {-20 * np.log10(g.min()):.1f} dB off above 4 kHz, {(g < 0.9).mean() * 100:.1f}% of the line")
