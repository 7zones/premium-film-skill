# Narration

## Contents
1. Choosing the narrator (casting)
2. Access, quotas and costs
3. The prompt (narrator file, director's notes, transcript)
4. Recording: batches, takes, context
5. From take to lines: cut, check, clean, level
6. Keeping one narrator: measurement and the owner's ear
7. Pronunciation
8. Patching a line weeks later
9. Re-timing for a shorter/longer read; per-language timing
10. Voice versions (the whole film in another voice)
11. Pitfalls table

---

## 1. Choosing the narrator (casting)

- Audition before deciding. `tools/providers.py` lists the voice models your keys reach today (ElevenLabs and Gemini TTS through OpenRouter, an ElevenLabs key, or the free Gemini API); `tools/tts.py --voices <model>` lists a model's voices. Record one representative excerpt (5 sentences across the film's moods) with 4–6 candidates, put them on a listening page (`tools/listening_page.py`) and let the owner pick by ear. A blind AI listen can shortlist on naturalness and fit, but run it twice with the order shuffled (its A/B picks follow list position).
- The register clients accepted for brand films and openers: a deep, calm, warm documentary narrator with quiet authority (in all four case-study films a deep Gemini voice, "Charon"; median pitch ~105–125 Hz). Bright, young or salesy voices were rejected even when AI listeners preferred them.
- Then lock it: one voice and one model per language for the whole film and every later patch, written in the README with the exact prompt file. A different model of the "same" voice is a different narrator (higher, faster, brighter); the owner caught it every time.
- "Natural, conversational" directions produced a flat read ("just reading the script without emotion"). For brand films and openers, direct a documentary-trailer read with a per-beat emotional sheet (§3), grounded ("no shouting, nothing salesy").
- "More punchy" ≠ a new voice. A projected direction raised the pitch ~8 semitones (shouty); a brighter voice won blind AI listens and was rejected by the owner: "keep the old voice… more punchy, more emotion". Keep the timbre; get punch from emphasis, rhythm, conviction and short charged pauses.
- Never pitch-shift a take to make it "deeper": a formant-preserving −1.5 st shift dropped speaker similarity 0.78 → 0.65 and sounded processed.

## 2. Access, quotas and costs

Services, keys and money in general: [providers.md](providers.md). For narration specifically:
- The free Gemini API tier allows about 10 voice requests per model per day per Google project (shared by every project on it; a probe counts). Batch all changed lines of a language into one request; one Gemini request can carry two speakers to audition two voices at once.
- Through OpenRouter a batch take costs about one to a few cents; check the key's balance before a batch (`tools/providers.py` prints it).
- When a quota runs out, don't switch models (that changes the narrator) and don't borrow other projects' keys: schedule the recording after the reset and keep working on picture.

## 3. The prompt (narrator file, director's notes, transcript)

Gemini's documented TTS layout, in `audio/vo/narrator-<lang>.md` plus the transcript (`tools/vo_prompt.py` joins them). Through OpenRouter, `tools/tts.py` sends the notes as the speech API's `instructions` and only the transcript as text; ElevenLabs gets only the transcript (its direction comes from the chosen voice, its settings and, on its newest models, inline audio tags such as `[calm]` written into the transcript):

```
# AUDIO PROFILE
A documentary narrator in his forties: a deep, low, resonant and warm voice with quiet authority. <accent and region,
e.g. "neutral international English" / "standard Northern (Hà Nội) Vietnamese, every tone exact">, crisp diction.

## THE SCENE
<where it plays: a premium brand film / the opening film of a national conference on a giant screen>. The narrator
speaks close to the microphone in a quiet studio.

### DIRECTOR'S NOTES
<pace, tone, pauses ("a clear pause of about one second between paragraphs"), "read every paragraph exactly once",
how to read numbers and years in this language ("2025 = twenty twenty-five"), when they could be read two ways>
<optional per-beat sheet, below>

#### TRANSCRIPT
<one paragraph per line, blank line between>
```

One narrator file per language (`narrator-en.md`, `narrator-de.md`, …), each written for a native speaker of that language: its accent or region, its number reading, and for tonal languages "every tone exact".

Delivered directions worth reusing:
- **Calm documentary (brand film v1):** "Speak <language> with a natural <region> accent. Calm, unhurried documentary pacing. Leave a clear pause of about one second between paragraphs. Warm and hopeful, never dramatic or salesy."
- **Deep, punchy, same timbre (conference opener, final):** "Keep the same deep, low register of a documentary narrator the whole time: never raise the pitch, never shout. Inside that deep voice, perform with real emotion and punch: lean into the key word of every phrase with weight and a firm, clean attack; let the feeling swell and recede with the story (awe, pride, gravity, urgency, resolve); take a short, charged pause before the big words, then hit them. The power comes from conviction, rhythm and emphasis, not from loudness or pitch. Keep a brisk, purposeful pace." Per beat: "three escalating hammer blows, the strongest on…"; slogans "like drum hits, each stronger than the last"; the welcome "grand, ceremonial, proud and warm".
- **Dramatic documentary trailer (brand film version 2):** "Perform it like the voice-over of a powerful documentary trailer, never like someone reading a script. Use a wide, expressive range and clear emphasis on the key word of every phrase, and let the energy rise and fall with the story, while every word (and, in a tonal language, every tone) stays exactly right. Vary the pace: slow down and lean in on the moments that matter, carry momentum through lists. Stay human and grounded: no shouting, nothing cartoonish or salesy." + a story-beat list naming the words to stress, carried in EVERY batch prompt.

## 4. Recording: batches, takes, context

- One request per batch of lines (a chapter, or the whole script for a short film: one generation keeps one consistent voice; separate requests drift).
- 2–3 takes per batch (3 for dramatic reads in a tonal language such as Vietnamese, where tones bend more); 6–9 for a single patch line.
- Re-record a line with its real neighbouring lines in the transcript (the line before and after), so the model keeps the film's register and flow; cut out only the line you need. This, not a "deep voice" note, is what made a patch match: the owner's pick came from the plain prompt recorded in context.
- Check every take's length against the expected duration: models sometimes read a batch twice, return two takes in one file, or insert a 5–8 s pause ("the model insists on that pause") — cut silence only, never speech. A second read is a free extra take: `cut_lines.py` says where it starts; cut it off and run the cutter on it too.
- Under a strict request budget set `TTS_TRIES=1` (a retry after a server error is another request).

## 5. From take to lines: cut, check, clean, level

1. `tools/cut_lines.py <lang> <take.wav> <take.prompt> audio/vo/<lang> <ids>` (film-asr image): Whisper word times aligned to the transcript; each line cut from just before its first sound to the longest pause before the next line (never mid-word); prints OK or DIFF per line. `--jobs` loads Whisper once for many takes (~40 s per take instead of minutes). Silence-based splitting mis-splits on short pauses — don't.
2. A DIFF is a wrong word, a doubled or skipped phrase, or in a tonal language a tone slip (Vietnamese examples heard: lửa for lừa, cây for cái, ngàn for nghìn). The cutter lists each difference as wanted→heard. English words and brand names inside another language's line come out spelled that language's way (Vietnamese "link→linh"): Whisper, not the voice — judge the language's own words. If the first or last word wasn't recognised, the cutter takes the unmatched speech next to it into the line and says so: check that note. To tell a real tone slip from a Whisper quirk: on a revision, run Whisper on the original delivered line too (it wrote "linh" for "link" in both — a quirk); on a new film, compare the other take, or ask the reviewer one targeted question ("in the line at 0:12, does the narrator say <word> or <the word heard>?"). Pick each line from a take that reads it right; a targeted note can fix a recurring slip ("Say '<word>' clearly… never '<wrong word>'").
3. `tools/check_vo.py` (film-audio): fails on the English model's end burst (0.12 s full-scale noise after the last word), start clicks, or loud hissy frames. The cutters strip them; the release runs this gate.
4. `tools/deess.py` (punchy reads: band above 4 kHz held ≤ −18 dBFS, calibrated to the original narrator; −24 cut too much), `tools/trim_lines.py` (drops a click/silence before the first word; leading only — a pitch-based trim once cut a word), `tools/level_lines.py` (−20 LUFS per line, so lines from different takes match).
5. Scan line starts for a scrap of the previous line ("…ther" at the start of the next clip, then a pause) and line ends for clipped tails; listen-check the finished soundtrack with an audio-only review prompt that asks for clipped/doubled/cut-off words with times — it caught a "ano-…-ther" splice nothing else did.

## 6. Keeping one narrator: measurement and the owner's ear

- `tools/voice_score.py --ref <the film's original lines> -- <candidates>` (film-voice): speaker similarity (ECAPA) against the original lines' mean (the originals' own leave-one-out median is ~0.77–0.79; a candidate well below it is a different-sounding narrator), pitch in semitones vs the originals (the owner heard +1.4 st as "kinda young, not the correct voice"; −1.2 st was the pick), spectral centre (a dark, muffled take ~800 Hz vs ~1000 Hz), duration. Exclude previously patched lines from the reference.
- Gemini's "same speaker?" verdicts were unreliable both ways (10/10 on rejected takes, 7/10 on the owner's pick). Use it only for concrete flags (a wrong word, a mangled name, a glitch with a time).
- When it's close, build `tools/listening_page.py`: each option played in context (the delivered line before, a ~1.2 s gap, the option, the line after), all at −20 LUFS, plain labels ("1.2 semitones deeper · very close match"), a Pick button and "Copy my picks" → the owner pastes back "My picks · English: B". Open it locally or publish it.

## 7. Pronunciation

- The voice follows the TRANSCRIPT, not the notes: "say AI as ây-ai" sat in a Vietnamese prompt's notes for days and was ignored; writing "ây ai" in the transcript fixed it. Respell acronyms, loanwords and brand names per language in `audio/vo/say.json` (`tools/vo_prompt.py` applies it; captions keep the written form), e.g. English "nginx" → "engine-x", Vietnamese "AI" → "ây ai", "deepfake" → "đíp-phếch".
- Verifying a pronunciation fix: Whisper writes the same text either way; the newer Gemini Flash told "a-i" from "ây-ai" (an older one couldn't); LPC formant tracks confirmed it ("ây": F1 ~450→250 Hz with F2 rising).
- Names from another language: even spelled out in the notes, an English voice anglicised Vietnamese names, and the owner said "it pronounces them so bad". Don't make a voice say names from a language it doesn't speak (beyond what the owner allows); name people on screen and introduce them by role. Act on a reviewer's pronunciation flag before the owner has to.
- Brand names: a Vietnamese voice read an English product name as a local word — check every brand word in every language, respell if needed.

## 8. Patching a line weeks later

1. Find exactly which takes and prompts produced the delivered lines (prove it by waveform: normalised cross-correlation of a 0.6 s slice = 1.000) — "check the past conversation to get the exact voice setting".
2. Reuse that prompt header verbatim, same model and voice; put the new sentence between its real neighbours.
3. 6–9 takes; cut by Whisper; score against the original lines and the adjacent delivered lines; check length fits the slot (≥ 1.2 s before the next line); listening page if close; tell the owner if anything else changed (e.g. a neighbouring line swapped to the same batch's take for consistency) and offer to revert.

## 9. Re-timing for a shorter/longer read; per-language timing

- Never time-stretch or squeeze pauses. To shorten: cut words, re-record, remove dead air in the picture.
- Breaths: ~1.3–1.7 s between lines in a list-like section, ~1 s more at a chapter turn, ~0.5 s inside one thought.
- When one language's lines are shorter (English without names), give that language its own scene times: trim the section that holds them, shift every later scene and narration slot, and absorb the difference inside a slow camera move (an eased local time-warp) rather than speeding visible action. Re-cue portraits and beats to that language's own words. Verify the other language's outputs are bit-identical.

## 10. Voice versions (the whole film in another voice)

"Try some, I want to have options": record the whole narration in the new voice (audition first), cut and check it like the original, then `tools/voice_warp.py <voice>` (film-asr) measures a smooth, monotone re-timing from the original timeline to the new read (anchors at every line's first sound and at pauses both reads share, picture speed kept within 0.75–1.35×, the silence after each line kept) into `src/film/voices.gen.json`. Then `npm run cues` and `VOICE=<voice>` for score, mix, captions and `tools/release.sh`: picture, music and subtitles follow the new read; the narration is never stretched. Outputs get a `-<Voice>` suffix and their own zip; the original version stays the main deliverable unless the owner says otherwise. Rerun the warp whenever the master timing or a line changes.

## 11. Pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| The voice reads the instructions aloud or repeats lines | Instructions prepended as plain text | The structured prompt; transcribe every take |
| A patch "sounds younger / higher / faster" | A different model, or generation drift | Same model + header, record in context, measure, owner picks |
| Loud noise at sentence ends | a model's end-of-take noise burst + start click (Gemini's English TTS in these films) | `vo_clean.strip_artifacts` in cutters; `check_vo.py` gate |
| A word clipped across two clips | Whisper stretched the next word back over the pause | Cut at the longest pause before the next line (`cut_lines.py`) |
| Two Whisper containers killed | Out of memory | One Whisper at a time; `--jobs` |
| faster-whisper can't open a file | Its PyAV can't read some WAVs | Load with soundfile, pass a 16 kHz array (the tools do) |
| A "deep" direction made the voice grave and slow | Over-direction | Plain header + context; or "keep the register, punch from emphasis" |
| Reviewer prefers whichever take is listed second | Position bias | Shuffle, two passes, decide by measurement + owner |
| Quota 429 mid-session | Free tier 10/day/model | Batch; schedule after reset; never switch models |
