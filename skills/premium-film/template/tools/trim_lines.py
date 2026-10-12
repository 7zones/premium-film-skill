#!/usr/bin/env python3
"""Trim what comes before the first word of a narration line: trim_lines.py <wav...> (in place)
A cut line can begin with a click and a stretch of silence before the voice starts. The line now starts 80 ms before
its first sustained sound (at least 100 ms within 38 dB of the line's peak), with a short fade in.
Runs in the film-audio image: docker run --rm -v "$PWD":/p -w /p film-audio python tools/trim_lines.py …"""
import sys
import numpy as np, soundfile as sf

for path in sys.argv[1:]:
    x, sr = sf.read(path, dtype="float32")
    mono = x if x.ndim == 1 else x.mean(1)
    hop = int(0.01 * sr)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(mono[i:i + hop] ** 2) + 1e-12) for i in range(0, len(mono) - hop, hop)]) + 1e-9)
    loud = db > db.max() - 38
    k = 0
    while k < len(loud):
        if loud[k] and loud[k:k + 10].all():
            break
        k += 1
    a = max(0, k - 8) * hop
    if a < int(0.05 * sr):
        continue
    seg = mono[a:].copy()
    fi = int(0.012 * sr)
    seg[:fi] *= np.linspace(0, 1, fi)
    sf.write(path, seg, sr)
    print(f"{path}: dropped the first {a / sr:.2f}s")
