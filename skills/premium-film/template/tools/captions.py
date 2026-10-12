#!/usr/bin/env python3
"""Subtitles for the captioned cut and the .srt files, timed to what the narrator actually says.
  docker run --rm -v "$PWD":/p -w /p film-asr python tools/captions.py [<lang> …]     (default: every language; VOICE=<name> for a voice version)
Writes src/film/captions.gen.json (drawn by src/components/Captions.tsx when the film's `captions` prop is on) and
out/srt/<lang>[-<voice>].srt.

Style the owner asked for and kept: ALWAYS one line per caption (≤ CAPTION_MAX characters, default 42), on a
see-through black band, each caption appearing as its first word is spoken. Split long lines by hand at phrase
boundaries with " | " in the narration text (src/film/timeline.ts); unsplit lines are split automatically at
punctuation. Times: Whisper word times (cached in audio/vo/.words-cache.json, so only changed lines are heard again),
snapped to the end of the pause before the word (Whisper stretches a word's start back into the pause). A caption
that ends up on screen < 0.6 s is reported: merge it with a neighbour. A line marked `onScreen` in the timeline (its
words are shown as designed type, e.g. the closing slogan) gets no burned-in subtitle; the .srt keeps every line."""
import difflib
import json
import os
import re
import sys
import unicodedata

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
cues = json.load(open("audio/cues.json", encoding="utf-8"))
VOICE = os.environ.get("VOICE", "")
MAX = int(os.environ.get("CAPTION_MAX", "42"))
LANGS = sys.argv[1:] or cues["langs"]
tok = lambda s: [t for t in (re.sub(r"[^\w]", "", w) for w in unicodedata.normalize("NFC", s.lower()).split()) if t]
CACHE = "audio/vo/.words-cache.json"
cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
model = None


def ts(t):
    ms = int(round(max(0.0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# words a caption may start with when there is no punctuation to break at (English and Vietnamese so far: add your
# language's conjunctions and prepositions for better automatic breaks)
LINKS = set("""và là của cho với để đi khi trong trên dưới những các đã đang sẽ được bị thì mà nhưng hay hoặc từ đến qua về
vì nên nếu như cùng tại theo giúp bằng rằng ngay chỉ còn cũng vẫn đều này kia ấy đó
and or but to of for with that which who in on at by from into over as than so because while when where""".split())


def auto_split(text):
    """The fewest one-line captions (each ≤ MAX characters), cut where they read best: balanced lengths, breaks after
    punctuation preferred, never a scrap under 12 characters (a 0.6 s flash of "Every day," is worse than a longer
    line). Hand-split anything important with " | " instead."""
    words = text.split()
    n = len(words)
    best = {0: (0.0, [])}  # words consumed → (cost, cut positions)
    for k in range(1, n + 1):
        options = []
        for j in range(k):
            if j not in best:
                continue
            piece = " ".join(words[j:k])
            if len(piece) > MAX:
                continue
            cost = best[j][0] + 100.0  # every extra caption costs
            if len(piece) < 12 and not (j == 0 and k == n):
                cost += 400.0
            if k < n and not re.search(r"[,.:;!?…]$", words[k - 1]):
                # a break that isn't at punctuation: cheap before a linking word (keeps "tín hiệu" / "make up" whole),
                # expensive anywhere else
                cost += 8.0 if words[k].lower().strip(",.") in LINKS else 30.0
            cost += (len(piece) - MAX * 0.7) ** 2 / 50.0  # prefer comfortably full lines
            options.append((cost, best[j][1] + [k]))
        if options:
            best[k] = min(options)
    if n not in best:  # a single word longer than MAX: give up gracefully
        return [text]
    cuts, out, j = best[n][1], [], 0
    for k in cuts:
        out.append(" ".join(words[j:k]))
        j = k
    return out


def read(path, lang):
    """Speech start/end, the pauses inside (s), and the words heard with their times."""
    global model
    y, sr = sf.read(path, dtype="float32")
    y = y if y.ndim == 1 else y.mean(axis=1)
    hop, win = int(sr * 0.01), int(sr * 0.03)
    frames = [np.sqrt(np.mean(y[i:i + win] ** 2) + 1e-12) for i in range(0, max(1, len(y) - win), hop)]
    db = 20 * np.log10(np.array(frames) / (max(frames) + 1e-12))
    on = np.where(db > -38)[0]
    start, end = on[0] * 0.01, on[-1] * 0.01 + 0.03
    pauses, run = [], None
    for k in range(on[0], on[-1] + 1):
        if db[k] <= -38:
            run = k if run is None else run
        elif run is not None:
            if (k - run) * 0.01 >= 0.08:
                pauses.append((run * 0.01, k * 0.01))
            run = None
    key = f"{path}:{os.path.getsize(path)}:{int(os.path.getmtime(path))}"
    if key not in cache:
        model = model or WhisperModel("large-v3", device="cpu", compute_type="int8", download_root="/models", cpu_threads=os.cpu_count() or 8)
        y16 = np.interp(np.arange(0, len(y) / sr, 1 / 16000), np.arange(len(y)) / sr, y).astype(np.float32)
        segs, _ = model.transcribe(y16, language=lang, word_timestamps=True, beam_size=1, vad_filter=False)
        cache[key] = [(t, w.start, w.end) for s in segs for w in s.words for t in tok(w.word)]
    return start, end, pauses, cache[key]


def starts(caps, heard, s0, pauses):
    """When each caption's first word is spoken (seconds into the line)."""
    script = [tok(c) for c in caps]
    flat = [t for c in script for t in c]
    sm = difflib.SequenceMatcher(None, flat, [t for t, _, _ in heard], autojunk=False)
    at = {i: heard[j][1] for blk in sm.get_matching_blocks() for i, j in zip(range(blk.a, blk.a + blk.size), range(blk.b, blk.b + blk.size))}
    known = sorted(at)
    out, i = [], 0
    for n, c in enumerate(script):
        if n == 0:
            out.append(s0)
        elif i in at:
            out.append(at[i])
        else:  # not heard as written (a number read out, a respelled acronym): between the nearest words that were
            lo = max([k for k in known if k < i], default=None)
            hi = min([k for k in known if k > i], default=None)
            if lo is not None and hi is not None:
                out.append(at[lo] + (at[hi] - at[lo]) * (i - lo) / (hi - lo))
            elif lo is not None:
                out.append(at[lo] + 0.3 * (i - lo))
            else:
                out.append(s0 + 0.3 * i)
        i += len(c)
    for n in range(1, len(out)):
        near = [p for p in pauses if abs(p[1] - out[n]) < 0.3]
        if near:
            out[n] = min(near, key=lambda p: abs(p[1] - out[n]))[1]
    return out


gen_path = os.path.join("src", "film", "captions.gen.json")
all_caps = json.load(open(gen_path, encoding="utf-8")) if os.path.exists(gen_path) else {}
os.makedirs(os.path.join("out", "srt"), exist_ok=True)
for lang in LANGS:
    slots = []
    for v in cues["vo"]:
        at = cues["voices"][VOICE][lang]["vo"][v["id"]] if VOICE else v["at"][lang]
        wav = os.path.join("audio", "vo", *([VOICE] if VOICE else []), lang, f"{v['id']}.wav")
        if not os.path.exists(wav):
            print(f"WARNING: narration {wav} is missing; no caption for it")
            continue
        slots.append((v["id"], at, v["text"][lang], v.get("onScreen", False), *read(wav, lang)))
    out, burned, k = [], [], 0
    for n, (vid, at, text, onscreen, s0, s1, pauses, heard) in enumerate(slots):
        caps = [c.strip() for c in text.split(" | ")] if " | " in text else auto_split(text)
        too_long = [c for c in caps if len(c) > MAX]
        assert not too_long, f"{lang} {vid}: captions over {MAX} characters, split them with ' | ': {too_long}"
        t = [at + x - 0.05 for x in starts(caps, heard, s0, pauses)]
        limit = slots[n + 1][1] + slots[n + 1][4] - 0.13 if n + 1 < len(slots) else float("inf")
        t.append(min(at + s1 + 0.4, limit))
        for c, line in enumerate(caps):
            a, b = t[c], t[c + 1] - (0.02 if c + 1 < len(caps) else 0)
            if b - a < 0.6:
                print(f"NOTE {lang} {vid}: '{line}' is up for only {b - a:.2f}s")
            cps = len(line) / max(b - a, 0.01)
            if cps > 20:
                print(f"NOTE {lang} {vid}: '{line}' reads at {cps:.0f} characters/s (over ~20 is hard to follow)")
            k += 1
            out.append(f"{k}\n{ts(a)} --> {ts(b)}\n{line}\n")
            if not onscreen:  # the words are on screen as designed type: no subtitle over them
                burned.append([round(a, 3), round(b, 3), line])
    name = f"{lang}{'-' + VOICE if VOICE else ''}"
    open(os.path.join("out", "srt", f"{name}.srt"), "w", encoding="utf-8").write("\n".join(out))
    all_caps[name] = burned
    print(f"wrote out/srt/{name}.srt: {k} captions")
json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(all_caps, open(gen_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("wrote", gen_path)
