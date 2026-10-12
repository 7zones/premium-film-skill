"""EXAMPLE original score (licence-free), composed in code and locked to the picture: chords change on the film's own
cue moments, the dynamics follow the story, a pulse carries the middle, and the music resolves home on the lockup.
Replace the harmony, parts and dynamics per film (or cut a licensed track instead: see kit.splice/stop_hit/freeze).

  docker run --rm -v "$PWD":/p -w /p film-audio python audio/score.py [<lang>]     → audio/build/score-<lang>.wav

Rules that came from rejected cuts:
  - a build-up must LAND and carry on: put the resolution on the visual climax and keep a sustained chord and the
    groove going under the next line; never let the music empty out just as the picture peaks
  - no "mute then boom" at the end unless the brief asks for it; restraint at the climax reads as premium
  - a sub note alone (C1 ≈ 33 Hz) is inaudible on laptops and phones: double impacts an octave up
  - a change of piece/section must be bridged (hold the last chord, a riser, a reverse swell), never a hard switch
"""
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
from kit import GM, SR, Part, db  # noqa: E402

film = kit.Film(sys.argv[1] if len(sys.argv) > 1 else "", os.environ.get("VOICE", ""))
LANG = film.lang
N, END = film.N, film.duration

# harmony: (bass, voicing) in MIDI notes; A minor colours resolving to C major
AM9 = (45, [57, 60, 64, 67, 71])
FMAJ9 = (41, [53, 57, 60, 64, 67])
CADD9 = (48, [55, 60, 62, 64, 67])
G6 = (43, [55, 59, 62, 64, 67])
CMAJ9 = (36, [55, 59, 62, 64, 67, 71])
t_ignite, t_title = film.cue("opening", "ignite"), film.cue("opening", "title")
t_lift, t_stat, t_line = film.m("lift"), film.cue("proof", "stat"), film.cue("proof", "line")
t_home = film.m("resolve")
# the harmony keeps moving into the scene change (G6 leans toward the lift), so the next section arrives as a
# continuation, not a restart
CH = [(0.0, AM9), (t_ignite, FMAJ9), (t_title, CADD9), (t_lift - 2.0, G6), (t_lift, AM9), (t_stat, FMAJ9), (t_line, G6), (t_home, CMAJ9)]

# "strings" (GM 48) speaks quickly; "strings2" (slow strings) swells in over ~1 s, which leaves a dip at every chord change
strings, low, piano, choir = Part(GM["strings"], 0), Part(GM["contrabass"], 1), Part(GM["piano"], 2), Part(GM["choir"], 3)
for k, (t, (bass, voicing)) in enumerate(CH):
    end = CH[k + 1][0] if k + 1 < len(CH) else END - 1.0
    for p in voicing:  # each chord rings 0.5 s into the next, so changes overlap instead of leaving a gap
        strings.note(t, end - t + 0.5, p, 96, human=False)
    low.note(t, end - t + 0.5, bass - 12 if bass > 40 else bass, 100, human=False)
# dynamics follow the story: a quiet open, a swell as the core ignites, a lift into the middle, home on the lockup
# no dips before a transition and no jump after it: the strings swell INTO the lift and carry through it
DYN = [(0, 0), (0.4, 40), (t_ignite, 60), (t_title + 1.0, 72), (t_lift - 2.0, 76), (t_lift - 0.2, 86), (t_lift + 0.8, 80), (t_line, 84), (t_home - 0.2, 94), (t_home + 0.6, 106), (END - 2.5, 92), (END, 30)]
strings.dynamics(DYN)
low.dynamics([(t, v * 0.92) for t, v in DYN])
# a piano motif answers the title, and again (in the major) on the lockup
for t0, notes in ((t_title + 0.2, [69, 72, 71, 76, 74]), (t_home + 0.5, [72, 76, 74, 79, 76])):
    for k, p in enumerate(notes):
        piano.note(t0 + k * 0.5, 0.5 * (3 if k == len(notes) - 1 else 0.98), p, 78)
# a rising harp figure builds through the last two seconds before the lift, so energy grows INTO the change
harp = Part(GM["harp"], 4)
for k, pch in enumerate([55, 59, 62, 64, 67, 71, 74, 76, 79, 83]):
    harp.note(t_lift - 2.0 + k * 0.19, 1.2, pch, 60 + 5 * k)
# the choir swells into home
for p in (60, 64, 67, 72):
    choir.note(t_home - 0.6, END - t_home - 0.4, p, 64, human=False)
choir.dynamics([(t_home - 0.6, 0), (t_home + 0.3, 80), (END - 1.5, 70), (END, 0)])

orch = np.zeros((N, 2), np.float32)
# measured levels differ a lot between General MIDI programs (piano ≈ 18 dB under strings at the same velocity):
# balance the parts by measurement, not by trust (see the rms printout)
for part, wet, gain in ((strings, 0.36, 3.0), (low, 0.2, -3.0), (piano, 0.3, 6.0), (choir, 0.42, -2.0), (harp, 0.34, 2.0)):
    orch += kit.hall(part.render(N), wet) * db(gain)

# synth layer: a soft pulse through the middle section (on the 120 bpm grid), sub notes and a pad under the lockup
syn = np.zeros((N, 2), np.float32)
beat = 0.5
k = 0
while t_lift + k * beat < t_home - 0.25:
    grow = min(1.0, 0.35 + 0.1 * k)  # the pulse grows in over two bars instead of starting at full level
    kit.place(syn, kit.kick((0.55 if k % 4 == 0 else 0.32) * grow), t_lift + k * beat)
    k += 1
for t, (bass, _v) in CH[4:]:
    kit.place(syn, kit.sub(bass, 1.6), t, -3)
kit.place(syn, kit.pad([60, 64, 67, 71], END - t_home + 0.5, cutoff=2600, level=0.1), t_home - 0.3)
kit.place(syn, kit.sub(36, 4.0, 0.4), t_home)
kit.place(syn, kit.sub(48, 4.0, 0.25), t_home)  # the octave up keeps the landing audible on small speakers

score = orch + kit.hall(syn, 0.18, hpf=40) * db(-15.0)  # the pulse sits UNDER the strings, it does not take over
score *= db(-18.0 - kit.loudness(score))  # a working level; the mix sets the final loudness
os.makedirs(kit.path("audio", "build"), exist_ok=True)
out = kit.path("audio", "build", f"score-{film.suffix()}.wav")
sf.write(out, score.astype(np.float32), SR, subtype="FLOAT")
print(f"wrote {os.path.relpath(out, kit.ROOT)}: {END:.2f} s, home at {t_home:.2f} s")
