#!/usr/bin/env python3
"""check_vo.py <wav...> : fails if any narration clip still carries a TTS glitch (vo_clean.py: end bursts, start
clicks, hissy frames). Also notes isolated 1 ms ticks (declick.py) without failing: some are a consonant's snap, and
tools/audio_qa.py on the mix flags the ones loud enough to hear — declick those lines."""
import sys
import soundfile as sf
from declick import find_ticks
from vo_clean import find_artifacts

bad = 0
for path in sys.argv[1:]:
    x, sr = sf.read(path)
    issues = find_artifacts(x, sr)
    ticks = find_ticks(x, sr)
    if ticks:
        print(f"{path}: note: {len(ticks)} isolated tick(s) at " + ", ".join(f"{t:.3f}s" for t in ticks[:8]))
    if issues:
        bad += 1
        print(f"{path}: " + "; ".join(issues))
print(f"{len(sys.argv) - 1} narration clips checked, {bad} with glitches")
sys.exit(1 if bad else 0)
