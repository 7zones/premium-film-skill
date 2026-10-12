#!/usr/bin/env python3
"""Removes the isolated sub-millisecond ticks Gemini TTS sometimes leaves inside narration (in place):
  docker run --rm -v "$PWD":/p -w /p film-audio python tools/declick.py audio/vo/en/*.wav
A tick is a 1 ms block whose level above 9 kHz stands RATIO (default 4) times above everything within ±2–10 ms: the
rule tools/audio_qa.py uses for clicks in the mix, so consonants and breaths (bursts tens of ms long) are never
touched. Each tick's ±1.5 ms is replaced by the line's own low-passed (6 kHz) signal with 1 ms crossfades, keeping the
speech under it. Use it on the lines where tools/audio_qa.py flags clicks in the mix (find them in the voice stem,
audio/build/stems-<cut>/); tools/check_vo.py notes ticks per line. If it reports dozens of spots in one line, stop and
listen-check: that is not a tick problem."""
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d


def find_ticks(x, sr, ratio=6.0):
    """Start times (s) of isolated high-frequency ticks in a clip."""
    mono = x if x.ndim == 1 else x.mean(1)
    peak = np.abs(mono).max() + 1e-9
    hp = signal.sosfilt(signal.butter(4, min(9000, 0.45 * sr), "high", fs=sr, output="sos"), mono)
    w = max(1, int(0.001 * sr))
    env = np.abs(hp[: len(hp) // w * w]).reshape(-1, w).max(1)
    if len(env) < 12:
        return []
    around = np.maximum(maximum_filter1d(np.concatenate([[0.0] * 2, env[:-2]]), size=9, origin=4),
                        maximum_filter1d(np.concatenate([env[2:], [0.0] * 2]), size=9, origin=-4))
    idx = np.flatnonzero((env > ratio * (around + 1e-4 * peak)) & (env > 0.004 * peak))
    return [i * w / sr for i in idx]


def declick(x, sr, ratio=4.0):
    ticks = find_ticks(x, sr, ratio)
    if not ticks:
        return x, ticks
    low = signal.sosfiltfilt(signal.butter(4, 6000, "low", fs=sr, output="sos"), x, axis=0)
    pad, fade, w = int(0.0015 * sr), max(2, int(0.001 * sr)), max(1, int(0.001 * sr))
    y = x.copy()
    for t in ticks:
        i = int(round(t * sr))
        s, e = max(0, i - pad), min(len(y), i + w + pad)
        g = np.ones(e - s)
        g[:fade] = np.linspace(0, 1, fade)[: e - s]
        g[-fade:] = np.minimum(g[-fade:], np.linspace(1, 0, fade)[-(e - s):])
        g = g[:, None] if y.ndim > 1 else g
        y[s:e] = y[s:e] * (1 - g) + low[s:e] * g
    return y, ticks


if __name__ == "__main__":
    ratio = float(os.environ.get("RATIO", "4"))
    for path in sys.argv[1:]:
        x, sr = sf.read(path, dtype="float64")
        y, ticks = declick(x, sr, ratio)
        if not ticks:
            print(f"{path}: no ticks")
            continue
        sf.write(path, y, sr, subtype=sf.info(path).subtype)
        print(f"{path}: {len(ticks)} tick(s) smoothed at " + ", ".join(f"{t:.3f}s" for t in ticks[:12]))
