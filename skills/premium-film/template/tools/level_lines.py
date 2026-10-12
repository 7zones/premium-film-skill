#!/usr/bin/env python3
"""Levels narration lines to the same loudness (in place): level_lines.py [--lufs -20] <wav...>
Lines picked from different takes (or recorded on different days) differ by a few dB; levelling each line to −20 LUFS
before the mix makes them sit together. Runs in the film-audio image."""
import sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

args = sys.argv[1:]
target = -20.0
if args and args[0] == "--lufs":
    target, args = float(args[1]), args[2:]
for p in args:
    y, sr = sf.read(p, dtype="float32")
    lv = pyln.Meter(sr).integrated_loudness(y)
    y = y * 10 ** ((target - lv) / 20)
    peak = float(np.abs(y).max())
    if peak > 0.98:
        y *= 0.98 / peak
    sf.write(p, y, sr, subtype="PCM_16")
    print(f"{p}: {lv:.1f} → {target:.1f} LUFS" + (" (peak-limited)" if peak > 0.98 else ""))
