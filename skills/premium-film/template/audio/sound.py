"""EXAMPLE sound design for the film. Every effect hits a NAMED moment from src/film/timeline.ts (film.cue / film.m),
so when the picture moves, its sound moves with it. audio/mix.py calls events(film) and mixes the list.

events(film) → [(time_s, signal (n, 2) float32, gain_db), ...]
DUCK         → per-line voice-over-music margin in dB (default 9; 10.5–12 for lines over a dense climax)
LINE_GAIN    → per-line narration gain in dB (e.g. +2.5 for slogans riding stop-time hits)

Design rules: effects underline what the picture does (a core ignites → a boom with a reverse swell into it; a card
lands → a soft whoosh; numbers count → fine ticks), they never fight the narration, and nothing is shrill or
constant (a high, steady "fan" tone under an ending was called "weird and annoying"). Put an effect's PEAK on the
moment: recorded files peak late (measure with tools/sfx_peaks.py) — place them at moment − peak offset.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfx as S  # noqa: E402
from kit import load, path  # noqa: E402

DUCK: dict = {}
LINE_GAIN: dict = {}


def rec(name, trim=None, start=0.0, fallback=None):
    """A recorded effect from assets/sfx/<name> (licence in assets/SOURCES.md), normalised to a common peak."""
    p = path("assets", "sfx", name)
    if not os.path.exists(p):
        return fallback if fallback is not None else np.zeros((1, 2), np.float32)
    x = load(p)[int(start * 48000):]
    if trim:
        x = x[: int(trim * 48000)].copy()
        f = int(0.05 * 48000)
        x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x / max(1e-6, float(np.abs(x).max())) * 0.7


def events(f):
    ignite, title = f.cue("opening", "ignite"), f.cue("opening", "title")
    card, stat, line = f.cue("proof", "card"), f.cue("proof", "stat"), f.cue("proof", "line")
    home, mark = f.m("resolve"), f.cue("closing", "mark")
    return [
        # the opening: a low bed, a breath in, the core ignites
        (0.0, S.drone(ignite + 3.0, 1, 41, 0.45), -13),
        (ignite - 1.6, S.reverse_swell(1.6, 2), -15),
        (ignite - 0.02, S.boom(3.5, 58, 30, 3, 0.2), -9),
        (ignite + 0.02, S.shimmer(3.0, 4, 1320, 0.14), -17),
        (title - 0.35, S.whoosh(1.1, 5, 300, 3600, 0.5), -17),
        # a breath into the scene change: a reverse swell lands on the lift, so the cut is carried, not heard
        (f.m("lift") - 1.4, S.reverse_swell(1.4, 12), -17),
        # the card arrives, the number resolves (fine ticks while it focuses), lands with a soft hit
        (card - 0.35, S.whoosh(0.9, 6, 500, 5000, 0.6, (0.5, -0.2)), -18),
        *[(stat + 0.08 * k, S.blip(1500 + 110 * k, 0.07, 20 + k, 0.28), -24) for k in range(11)],
        (stat + 0.95, S.hit(2.2, 7, 0.35), -17),
        (line - 0.1, S.shimmer(1.6, 8, 1760, 0.1), -21),
        # into the lockup: a riser that stops on the resolve, an impact doubled an octave up, a gold sparkle
        (home - 2.4, S.riser(2.4, 9, 200, 2600), -18),
        (home - 0.05, S.boom(4.0, 62, 31, 10, 0.25), -10),
        (mark + 0.25, S.shimmer(3.2, 11, 1320, 0.2), -15),
    ]
