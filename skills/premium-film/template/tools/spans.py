#!/usr/bin/env python3
"""Speech spans and the pauses between them: spans.py [--gap 0.18] <wav...>
For checking breaths between narration lines and phrases (a line that starts too soon after the previous one sounds
rushed; a gap over ~2 s inside a chapter sounds like dead air). Runs anywhere with numpy + soundfile (film-audio)."""
import sys

import numpy as np
import soundfile as sf

args = sys.argv[1:]
gap = 0.18
if args and args[0] == "--gap":
    gap, args = float(args[1]), args[2:]
for p in args:
    y, sr = sf.read(p)
    y = y if y.ndim == 1 else y.mean(1)
    hop = int(sr * 0.01)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, len(y) - hop, hop)]) + 1e-7)
    on = db > max(np.percentile(db, 95) - 38, -60)
    spans, s, last = [], None, None
    for i, v in enumerate(on):
        t = i * 0.01
        if v:
            if s is None:
                s = t
            elif t - last > gap:
                spans.append((s, last))
                s = t
            last = t
    if s is not None:
        spans.append((s, last))
    print(f"{p}  {len(y) / sr:.2f}s  " + "  ".join(f"{a:.2f}–{b:.2f}" + (f" (+{spans[i + 1][0] - b:.2f})" if i + 1 < len(spans) else "") for i, (a, b) in enumerate(spans)))
