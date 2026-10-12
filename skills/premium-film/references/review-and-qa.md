# Review and QA

You can't watch or hear the film. These checks are how the four films reached "extremely good now" and "everything else is perfect" — and the gaps in them are how glitches reached the owner. Run them on every round, before anything is shown, and report which ones you ran.

## Contents
1. The loop
2. Looking: sheets, strips, stills
3. Automatic scans
4. Listening by numbers
5. The independent reviewer (the newest Gemini Flash)
6. Checklist before you say "done"

---

## 1. The loop

1. Change something → `npm run cues` if timing moved → score/mix if sound moved.
2. `tools/preview.sh <name> <from> <to> [lang]` for the changed stretch (half size, 30 fps, with sound) → look at its contact sheet, then at full-size stills of every text moment (every language; the captioned cut if captions exist).
3. Scan the preview (`tools/qa_scan.py`) and the mix (`tools/audio_qa.py`).
4. When a draft of the whole film exists: `tools/sheet.sh` of the whole cut in each language (read every sheet), strips across every transition, the scans, and an independent review of a small whole-film copy.
5. Fix, then re-run only what the fix touches; final scans on the masters after the release. Compare against the previous version when you can: run the scans on both and look only at what's new.

## 2. Looking: sheets, strips, stills

- **Whole-cut sheets:** `tools/sheet.sh out/<film>.mp4 2` (one frame every 2 s, 6×5 per sheet). Look for: missing or repeated layouts, dark or empty stretches, text too small, anything cut by the frame edge, inconsistent grade.
- **Transition strips:** `tools/strip.sh <video> <time> 1.0` (every frame across 1 s) at every scene change and every big move. A reviewer's "hard cut" may be a smooth move it sampled at 1 fps; a real pop is only visible here.
- **Stills of text moments:** `npx remotion still src/index.ts Film-<lang> tmp/x.png --frame=<f> --props='{"lang":"<lang>","withAudio":false}'` (and `"captions":true`). Check at FULL size: diacritics, wraps, truncation ("only 'Thương hiệu của bạn' showed"), overlaps (a photo over a card border), title-safe margins, and that settled text is crisp.
- **Phone check:** view a frame at ~640 px wide — anything unreadable there is too small.
- **Every language, always.** Translated text runs longer and breaks layouts the master language doesn't.

## 3. Automatic scans (`tools/qa_scan.py <video> [--chunk 150] [--strips tmp/qa]`)

Flags, with timestamps and a strip per finding:
- **black / dip:** a frame much darker than both neighbours (one NaN pixel through bloom blacks a whole frame — the bug is deterministic, so it reproduces); bisect with bloom off, then remove elements one at a time.
- **jump:** a one-frame spike in change (a pop, an instant flash, something appearing with no animation).
- **cut:** a single huge change — fine if intended; confirm each one is.
- **flicker:** the same spots flipping back and forth (render-tab text flicker; also blinking lights — confirm on a crop of the text before believing it).
- **dead:** stretches where nothing moves ≥ 0.8 s (a client called 1–2 s of still picture "dead" and a drop in emotion; only the final logo/title may hold still, ~4 s).
- **join:** a change across a chunk boundary unlike its neighbours (a bad join). Also check: exposed edges of depth photos (brighten the frame and look at the borders), every beat's screen time (a slogan flew by in 0.6 s), and that every animation settles.

## 4. Listening by numbers

- `tools/audio_qa.py`: loudness −14 LUFS, true peak ≤ −1 dBTP, clicks, hiss, holes, drops; `--sync` for big hits. Run it on the delivered MP4 too: AAC encoding raises peaks (a clean −1.2 dBTP mix measured −0.3 in its MP4).
- The mix's per-line table: voice ≥ 6 dB (aim 8.5–9) over music on every line.
- Narration: `cut_lines.py` OK on every line; `check_vo.py` clean; `voice_score.py` within the narrator's range for patched lines; pauses measured (`tools/spans.py`): ~1.2–1.7 s between lines, ~1 s more at chapter turns, ~0.5 s inside a thought, never 2.4–3.7 s of dead air.
- Loudness envelopes across changed transitions (no dip before, no jump after a section change).
- Pronunciation: Whisper confirms words, not accents; for loanwords, ask a reviewer a targeted question (the newest Gemini Flash told two close Vietnamese readings of "AI" apart; an older one couldn't) or look at formants.

## 5. The independent reviewer (the newest Gemini Flash)

- **Model:** `tools/review.py` uses the newest Gemini Flash that takes video and audio (picked by `tools/providers.py`; OpenRouter preferred, the free Gemini API works). Pin it for the round so scores compare between versions; ask it about picture and sound in the same call.
- **Media:** `tools/excerpt.sh <video> whole` (640 px, 24 fps, ≈5 MB for 3 min; a whole-film review cost ≈ $0.03 via OpenRouter) or `tools/excerpt.sh <video> <from> <to>` (frames every 0.5 s named by time + mp3) when video upload is refused. A 4×-slowed reel of all transitions is a good way to have transitions judged.
- **Prompt shape that worked:** a role ("a demanding creative director at a top motion studio; a film-music supervisor and re-recording mixer"), the bar ("as premium as an Apple or Stripe launch film"), the chapters with times, the brand rules, what changed since last time only if you want it checked (it primes higher scores), and the ask: "a numbered list, most important first, each with an exact mm:ss timestamp, what is wrong and a concrete fix — text hard to read or too brief; rushed, slow or empty moments; transitions that jar, flash or pop; glitches (cropped UI, overlaps, flicker, blur); narration cut off, overlapping or mispronounced; music too loud, abrupt or flat; anything cheap or template-like. Only report real problems; say 'none' if none. Do not praise. Score out of 10." For an agentic CLI reviewer add "Do NOT run any shell commands; do not edit files".
- **Trust:** act on concrete, checkable flags (a clipped word at a time, a mis-said name, text cut off, a glitch) after confirming each on frames/measurements. Ignore or test: A/B preferences (position bias — the second-listed clip wins), voice-identity judgments, small-text "typos" at low resolution (usually mid-animation frames), music "jumps", "hard cuts" between its samples, its own taste (it asked for faster typing the owner had rejected; it proposed recolouring partner logos). AI reviewers rated AI footage 9/10 that the human client called fake: the owner is the judge, the reviewer is a flagger.
- Act on pronunciation flags without waiting for the owner to complain (two reviews flagged anglicised names before the owner did).

## 6. Checklist before you say "done"

- [ ] Every scene viewed in every language (sheets) and every text moment at full size
- [ ] The poster test: a mid-frame of every beat is full and rich (depth layers, light, the hero filling the frame), not a small element in a dark void; every text moment readable at 640 px wide
- [ ] Every transition stripped; no pops, flashes, blocky dissolves, hard horizon lines, glows cut by floors
- [ ] `qa_scan` clean (or every finding confirmed intended) on each master
- [ ] `audio_qa` clean on each mix and each delivered MP4; per-line table ≥ 6 dB; narration OK on every line
- [ ] Captioned cut: one line, nothing overlapping, no duplicated words, subtitles step aside for picture-type
- [ ] Facts: every on-screen claim/name/number in the fact sheet; logos are the official files
- [ ] Deliverables: durations and frame counts right, the zip rebuilt and tested, thumbnails current
- [ ] Previous version kept if this is a new version; README and memory updated; test files deleted
