#!/usr/bin/env python3
"""Builds a Gemini TTS prompt: vo_prompt.py <narrator.md> <lang> [ids...] > take.prompt

<narrator.md> holds the film's narrator as three sections, kept IDENTICAL for every take of the film (re-using the
exact header is how a new line weeks later still sounds like the same narrator):
    # AUDIO PROFILE      who speaks (age, origin, timbre, accent)
    ## THE SCENE         where/how the film is played, how close to the mic
    ### DIRECTOR'S NOTES pace, tone, pauses, per-beat emotion
The transcript comes from audio/cues.json (the narration text in src/film/timeline.ts), one paragraph per line, in
film order, optionally only the given ids. Caption break marks ' | ' are removed.

Pronunciation: the voice follows the TRANSCRIPT far more reliably than the notes (a Vietnamese voice ignored "say AI
as ây-ai" in the notes; writing "ây ai" in the transcript fixed it). So acronyms, foreign words, brand names and
numbers that read wrongly are respelled here, per language, from audio/vo/say.json: {"en": {"SQL": "sequel"},
"vi": {"AI": "ây ai"}}. The captions keep the written form.
To re-record a line in context, pass its id WITH its real neighbours (the lines before and after): the narrator
keeps the film's flow and level; cut only the line you need. Prints the ids in order to stderr (for cut_lines.py)."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
narrator, lang, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
head = open(narrator, encoding="utf-8").read().strip()
assert "#### TRANSCRIPT" not in head, "the narrator file must not contain the transcript"
vo = json.load(open(os.path.join(ROOT, "audio", "cues.json"), encoding="utf-8"))["vo"]
say_path = os.path.join(ROOT, "audio", "vo", "say.json")
say = json.load(open(say_path, encoding="utf-8")).get(lang, {}) if os.path.exists(say_path) else {}


def spoken(s):
    s = " ".join(s.replace(" | ", " ").split())
    for written, said in sorted(say.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(rf"(?<!\w){re.escape(written)}(?!\w)", said, s)
    return s


lines = [v for v in vo if not ids or v["id"] in ids]
print(f"{head}\n\n#### TRANSCRIPT\n" + "\n\n".join(spoken(v["text"][lang]) for v in lines))
print(",".join(v["id"] for v in lines), file=sys.stderr)
