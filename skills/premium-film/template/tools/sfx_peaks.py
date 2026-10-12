#!/usr/bin/env python3
"""Where each recorded sound effect actually peaks: sfx_peaks.py <files or folders...>
Recorded impacts, whooshes and risers peak late (a whoosh's peak can be 0.6–1 s in, a reverse cymbal's 3.4 s), so
place each file at (moment − peak) to land its peak on the picture's hit. Prints duration, peak time, the active
span and the first onsets. Runs in the film-audio image."""
import glob
import os
import sys

import librosa
import numpy as np

files = []
for a in sys.argv[1:]:
    files += sorted(glob.glob(os.path.join(a, "**", "*.*"), recursive=True)) if os.path.isdir(a) else [a]
for f in files:
    if not f.lower().endswith((".mp3", ".wav", ".ogg", ".flac", ".m4a")):
        continue
    y, sr = librosa.load(f, sr=22050, mono=True)
    rms = librosa.feature.rms(y=y, hop_length=256)[0]
    t = np.arange(len(rms)) * 256 / sr
    db = 20 * np.log10(rms + 1e-9)
    above = t[db > db.max() - 30]
    on = librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=True)[:5]
    print(f"{os.path.basename(f)[:60]:60s} dur {len(y) / sr:5.2f}  peak@{t[np.argmax(rms)]:5.2f}  active {above.min():5.2f}–{above.max():5.2f}  onsets {np.round(on, 2).tolist()}")
