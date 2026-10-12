#!/usr/bin/env python3
"""Cuts a narration take into its lines by what was actually SAID (Whisper word times), not by silences, and checks
every line word by word.
  cut_lines.py <lang> <take.wav> <take.prompt> <out_dir> <id,id,...>
  cut_lines.py --jobs <file>     (one job per line, the same five arguments; Whisper loads once for all of them)
The prompt's '#### TRANSCRIPT' paragraphs are the lines, named by the ids in order (tools/vo_prompt.py prints them).
Each line is cut from just before its first sound to the longest pause before the next line (Whisper stretches a
line's first word back over the pause before it; cutting there used to clip the previous line's last word and leave
its tail at the start of the next clip), written as <out_dir>/<id>.wav with short fades, and reported as
OK or DIFF with what was heard and each difference (wanted→heard). A DIFF is a wrong word, a slipped tone in a tonal
language (Vietnamese "lừa→lửa"), a skipped or doubled phrase: use another take for that line. English words and brand
names inside another language's lines are heard that language's way (Vietnamese "link→linh"): that is Whisper, not the
voice — judge the language's own words. <take>.json keeps every line's words and times.
Runs in the film-asr image: docker run --rm -v "$PWD":/p -w /p film-asr python tools/cut_lines.py …"""
import difflib
import json
import os
import re
import sys
import unicodedata

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vo_clean import strip_artifacts  # noqa: E402

tok = lambda s: [re.sub(r"[^\w]", "", w) for w in unicodedata.normalize("NFC", s.lower()).split() if re.sub(r"[^\w]", "", w)]
model = WhisperModel("large-v3", device="cpu", compute_type="int8", download_root="/models", cpu_threads=os.cpu_count() or 8)


def cut(lang, src, prompt, out_dir, ids):
    lines = [p.strip() for p in open(prompt, encoding="utf-8").read().split("#### TRANSCRIPT", 1)[-1].strip().split("\n\n") if p.strip()]
    assert len(lines) == len(ids), f"{len(lines)} lines in the transcript, {len(ids)} ids"
    os.makedirs(out_dir, exist_ok=True)
    x, sr = sf.read(src, dtype="float32")
    x = strip_artifacts(x, sr)
    x = x if x.ndim == 1 else x.mean(1)
    y16 = np.interp(np.arange(0, len(x) / sr, 1 / 16000), np.arange(len(x)) / sr, x).astype(np.float32)
    segs, _ = model.transcribe(y16, language=lang, word_timestamps=True, beam_size=5, vad_filter=False)
    heard = [(t, w.start, w.end) for s in segs for w in s.words for t in tok(w.word)]
    want = [(k, t) for k, line in enumerate(lines) for t in tok(line)]
    sm = difflib.SequenceMatcher(None, [t for _, t in want], [t for t, _, _ in heard], autojunk=False)
    match = {}
    for a, b, n in sm.get_matching_blocks():
        for i in range(n):
            match[a + i] = b + i
    hop = int(0.01 * sr)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x) - hop, hop)]) + 1e-9)
    quiet = db < max(db.max() - 42, -55)

    def snap(t, direction, limit):
        """From t, walk to the nearest 120 ms pause in `direction` (-1 back, +1 forward), never past `limit`."""
        j = int(t * 100)
        while 0 < j < len(quiet) - 12 and (j > limit if direction < 0 else j < limit):
            if quiet[j:j + 12].all() if direction > 0 else quiet[max(0, j - 12):j].all():
                break
            j += direction
        return j / 100

    report, prev_end, prev_h1 = {}, 0.0, -1
    for k, (id_, line) in enumerate(zip(ids, lines)):
        mine = [i for i, (kk, _) in enumerate(want) if kk == k]
        got = [match[i] for i in mine if i in match]
        if not got:
            print(f"{id_:6s} NOT FOUND")
            continue
        h0, h1 = min(got), max(got)
        nxt = [match[i] for i, (kk, _) in enumerate(want) if kk == k + 1 and i in match]
        # Whisper often writes a brand or foreign word as something else ("LinkSafe" → "linh xeo"), so the line's
        # first or last word matches nothing. Take the unmatched words heard right before/after it (close in time)
        # into the line, so the cut never silently drops a word, and say so.
        lead = next(n for n, i in enumerate(mine) if i in match)
        trail = next(n for n, i in enumerate(reversed(mine)) if i in match)
        if lead:
            j = h0
            while j - 1 > prev_h1 and h0 - (j - 1) <= 2 * lead + 1 and heard[h0][1] - heard[j - 1][1] < 1.5:
                j -= 1
            print(f"{id_:6s} note: first word(s) '{' '.join(t for _, t in want[mine[0]:mine[lead]])}' not recognised; "
                  f"{'cut from the unmatched speech before it: ' + ' '.join(t for t, _, _ in heard[j:h0]) if j < h0 else 'NOTHING heard for them: listen'}")
            h0 = j
        if trail:
            stop = min(nxt) if nxt else len(heard)
            j = h1
            while j + 1 < stop and (j + 1) - h1 <= 2 * trail + 1 and heard[j + 1][2] - heard[h1][2] < 1.5:
                j += 1
            print(f"{id_:6s} note: last word(s) '{' '.join(t for _, t in want[mine[-trail]:mine[-1] + 1])}' not recognised; "
                  f"{'cut through the unmatched speech after it: ' + ' '.join(t for t, _, _ in heard[h1 + 1:j + 1]) if j > h1 else 'NOTHING heard for them: listen'}")
            h1 = j
        prev_h1 = h1
        a = snap(heard[h0][1], -1, int(prev_end * 100))
        limit = len(quiet) - 1
        if nxt:  # the longest quiet stretch between this line's last word and the end of the next line's first word
            lo, hi = int(heard[h1][2] * 100), int(heard[min(nxt)][2] * 100)
            runs, r0 = [], None
            for j in range(lo, min(hi, len(quiet))):
                if quiet[j] and r0 is None:
                    r0 = j
                elif not quiet[j] and r0 is not None:
                    runs.append((j - r0, j))
                    r0 = None
            limit = max(runs)[1] if runs else int(heard[min(nxt)][1] * 100)
        b = snap(heard[h1][2], +1, limit)
        voiced = np.flatnonzero(~quiet[int(a * 100):int(b * 100)])
        if len(voiced):
            a, b = a + max(voiced[0] / 100 - 0.06, 0), min(b, a + voiced[-1] / 100 + 0.15)
        a, b = max(a, prev_end), b + 0.05
        seg = x[int(a * sr):int(b * sr)].copy()
        fi, fo = int(0.012 * sr), int(0.07 * sr)
        seg[:fi] *= np.linspace(0, 1, fi)
        seg[-fo:] *= np.linspace(1, 0, fo)
        sf.write(os.path.join(out_dir, f"{id_}.wav"), seg, sr)
        said = [heard[j] for j in range(h0, h1 + 1)]
        ok = "".join(t for t, _, _ in said) == "".join(tok(line))
        diffs = []
        if not ok:  # name each difference: a brand or English word spelled the local way is Whisper, not the voice
            w, h = tok(line), [t for t, _, _ in said]
            for op, i0, i1, j0, j1 in difflib.SequenceMatcher(None, w, h, autojunk=False).get_opcodes():
                if op != "equal":
                    diffs.append(f"{' '.join(w[i0:i1]) or '∅'}→{' '.join(h[j0:j1]) or '∅'}")
        report[id_] = {"dur": round(b - a, 3), "ok": ok, "diff": diffs, "words": [(t, round(s - a, 3), round(e - a, 3)) for t, s, e in said]}
        print(f"{id_:6s} {b - a:5.2f}s  {'OK  ' if ok else 'DIFF'} {' '.join(t for t, _, _ in said)}"
              + (f"\n{'':14s}differs: {', '.join(diffs)}" if diffs else ""))
        prev_end = b
    rest = [w for w in heard[prev_h1 + 1:]] if prev_h1 >= 0 else []
    if len(rest) >= 4:
        print(f"note: the take goes on after the last line ({len(rest)} more words from {rest[0][1]:.1f} s, likely a second "
              f"read): a free extra take — cut it with ffmpeg -ss {max(rest[0][1] - 0.3, 0):.1f} -i {src} <take-b.wav>, then "
              f"cut_lines.py on that file")
    json.dump(report, open(src[:-4] + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


jobs = [l.split() for l in open(sys.argv[2]) if l.strip()] if sys.argv[1] == "--jobs" else [sys.argv[1:6]]
for lang, src, prompt, out_dir, ids in jobs:
    print("###", src, flush=True)
    cut(lang, src, prompt, out_dir, ids.split(","))
