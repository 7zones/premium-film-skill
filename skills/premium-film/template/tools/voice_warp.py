#!/usr/bin/env python3
"""Re-time the film to another narrator: voice_warp.py <voice>
Reads the original narration (audio/vo/<lang>/<id>.wav at the slots in audio/cues.json) and the new voice's lines
(audio/vo/<voice>/<lang>/<id>.wav) and writes src/film/voices.gen.json[<voice>][<lang>]:
  vo        each line's new start: the silence after every line keeps its original length, so the film grows or
            shrinks by what the new reads add up to
  anchors   [original s, new s] pairs at every line's first sound, and where the speed it implies stays gentle, at
            each phrase both reads begin after a pause (found by the words around it). src/film/voices.ts and
            audio/film_mix.py draw one smooth monotone curve through them, so each line's difference is spread over
            the line and the breath after it and the picture never visibly speeds up or slows down
  duration  the new running time (a multiple of 1/30 s)
Runs in the film-asr image: docker run --rm -v "$PWD":/p -w /p film-asr python tools/voice_warp.py <voice>
After it: npm run cues, then VOICE=<voice> for audio/score.py, audio/mix.py, tools/captions.py and tools/release.sh."""
import difflib, json, os, re, sys, unicodedata
import numpy as np, soundfile as sf
from faster_whisper import WhisperModel

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
voice = sys.argv[1]
cues = json.load(open("audio/cues.json", encoding="utf-8"))
model = WhisperModel("large-v3", device="cpu", compute_type="int8", download_root="/models", cpu_threads=os.cpu_count() or 8)
tok = lambda s: [t for t in (re.sub(r"[^\w]", "", w) for w in unicodedata.normalize("NFC", s.lower()).split()) if t]
PAUSE = 0.18  # shortest silence that counts as a pause inside a line
SPEED = (0.75, 1.35)  # the gentlest re-timing a phrase anchor may ask of the picture
CACHE = "audio/vo/.words-cache.json"  # transcripts by file, so a changed line is the only one heard again
cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def read(path, lang):
    """Speech onset and offset, the pauses inside, and the words (with times) of one line."""
    x, sr = sf.read(path, dtype="float32")
    x = x if x.ndim == 1 else x.mean(1)
    hop = int(0.01 * sr)
    db = 20 * np.log10(np.array([np.sqrt(np.mean(x[i:i + hop] ** 2) + 1e-12) for i in range(0, len(x) - hop, hop)]) + 1e-9)
    loud = db > db.max() - 38
    a = next(k for k in range(len(loud)) if loud[k:k + 10].all())  # first sustained sound (as tools/trim_lines.py)
    b = np.flatnonzero(db > db.max() - 40)[-1]
    pauses, run = [], None
    for k in range(a, b + 1):
        if db[k] <= db.max() - 40:
            run = k if run is None else run
        else:
            if run is not None and (k - run) / 100 >= PAUSE:
                pauses.append((run / 100, k / 100))
            run = None
    key = f"{path}:{os.path.getsize(path)}:{int(os.path.getmtime(path))}"
    if key not in cache:
        y16 = np.interp(np.arange(0, len(x) / sr, 1 / 16000), np.arange(len(x)) / sr, x).astype(np.float32)
        segs, _ = model.transcribe(y16, language=lang, word_timestamps=True, beam_size=1, vad_filter=False)
        cache[key] = [(t, w.start, w.end) for s in segs for w in s.words for t in tok(w.word)]
    return a / 100, b / 100, pauses, cache[key]


def gap_index(pause, words):
    """How many words come before a pause."""
    mid = (pause[0] + pause[1]) / 2
    return sum(1 for _, s, e in words if (s + e) / 2 < mid)


out_path = "src/film/voices.gen.json"
data = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
data[voice] = data.get(voice, {})
for lang in [l for l in cues["langs"] if os.path.isdir(f"audio/vo/{voice}/{l}")]:
    anchors, vo, lines = [(0.0, 0.0)], {}, []
    prev_old_end = prev_new_end = None
    print(f"\n== {lang}")
    for v in cues["vo"]:
        at = v["at"][lang]
        o_on, o_off, o_p, o_w = read(f"audio/vo/{lang}/{v['id']}.wav", lang)
        n_on, n_off, n_p, n_w = read(f"audio/vo/{voice}/{lang}/{v['id']}.wav", lang)
        old_on = at + o_on
        new_on = old_on if prev_old_end is None else prev_new_end + (old_on - prev_old_end)
        new_at = new_on - n_on
        vo[v["id"]] = round(new_at, 3)
        # phrases both reads begin after a pause at the same place in the sentence
        sm = difflib.SequenceMatcher(None, [t for t, _, _ in o_w], [t for t, _, _ in n_w], autojunk=False)
        same = {i: j for blk in sm.get_matching_blocks() for i, j in zip(range(blk.a, blk.a + blk.size), range(blk.b, blk.b + blk.size))}
        n_by_gap = {gap_index(p, n_w): p for p in n_p}
        phrases = []
        for p in o_p:
            k = gap_index(p, o_w)
            if k > 0 and (k - 1) in same and (same[k - 1] + 1) in n_by_gap:
                phrases.append((at + p[1], new_at + n_by_gap[same[k - 1] + 1][1]))
        lines.append((v["id"], old_on, new_on, sorted(phrases), o_off - o_on, n_off - n_on))
        prev_old_end, prev_new_end = at + o_off, new_at + n_off
    end_old = float(cues["duration"][lang])
    end_new = round((prev_new_end + (end_old - prev_old_end)) * 30) / 30
    for n, (id_, o_on, n_on, phrases, o_d, n_d) in enumerate(lines):
        anchors.append((o_on, n_on))
        nxt = lines[n + 1][1:3] if n + 1 < len(lines) else (end_old, end_new)
        kept = 0
        for o, w in phrases:  # a phrase anchor only where the picture's speed stays gentle on both sides
            s1 = (w - anchors[-1][1]) / (o - anchors[-1][0])
            s2 = (nxt[1] - w) / (nxt[0] - o)
            if SPEED[0] <= s1 <= SPEED[1] and SPEED[0] <= s2 <= SPEED[1]:
                anchors.append((o, w)); kept += 1
        print(f"{id_:6s} {o_d:5.2f}s → {n_d:5.2f}s  start {o_on:7.2f} → {n_on:7.2f}  {kept}/{len(phrases)} phrase anchors")
    anchors.append((end_old, end_new))
    sl = [(b1 - b0) / (a1 - a0) for (a0, b0), (a1, b1) in zip(anchors, anchors[1:])]
    print(f"picture speed {min(sl):.2f}–{max(sl):.2f} (1 = as cut)")
    clean = [anchors[0]]
    for a, b in anchors[1:]:
        if a > clean[-1][0] + 0.02 and b > clean[-1][1] + 0.02:
            clean.append((round(a, 4), round(b, 4)))
    data[voice][lang] = {"vo": vo, "anchors": clean, "duration": end_new}
    print(f"running time {end_old:.2f}s → {end_new:.2f}s")
json.dump(data, open(out_path, "w", encoding="utf-8"), indent=1)
json.dump(cache, open(CACHE, "w", encoding="utf-8"))
print("wrote", out_path)
