---
name: premium-film
description: Makes premium, fact-checked videos that follow a brand's guidelines, in code with Remotion — brand films, product showcases, event or conference openers, teasers and promos — with motion design, 3D, real photos, AI narration in any language, generated images, music, sound effects, captions and 1080p60 exports. Uses whichever AI services the person has (OpenRouter, Gemini, ElevenLabs, GPT Image; all optional). Includes a quality checklist, a fact-checking workflow, review tools and a starter project. Use when someone asks to create, script, voice, score, render, revise or fix a video, film, promo, motion-graphics piece, intro/outro, opening film or product showcase, or gives feedback on one ("the transition feels weird", "the voice sounds different", "make it more premium", "add captions", "another version with a different voice"), even if they never mention Remotion.
compatibility: Best with Claude Opus 5.5 in Claude Code. Tested on macOS (Apple Silicon) with Node 22+, Docker Desktop or Colima, ffmpeg and zsh. AI services are optional - an OpenRouter key is preferred, a free Gemini API key alone covers narration and reviews, ElevenLabs and the Codex CLI add voices and images.
---

# Premium Film

Make videos in code that follow the brand's guidelines, state only checked facts, and look and sound professionally produced. "The owner" below is the person you make the film for, often passing on a client's feedback. The examples come from real client films ([case-studies.md](references/case-studies.md)).

The bar is "premium, polished… pixel perfect". What failed it, in the owner's words: "those pills look cheap", "kinda basic… merely following the script", "transition so weird", "too fast I can't read", "drops weirdly", "the voice is kinda young", "images look so fake", "a mute then boom is a bit too much".

## The rules

1. **Correct information above everything.** Every fact, name, title, number, date, quote, logo and pronunciation is checked against a primary source before it goes on screen or into the narration, and checked again when anything changes. Never invent or guess; when a source is missing, verify it or ask. Official titles are copied verbatim, logos come only from the owner's own files, real organisations get their real photos (whole heads, no halos, no generated faces). Product demos use only clearly fictional data (non-resolving domains, documentation IPs, invented names). One wrong claim undoes everything else in the film.
2. **Premium in every component.** Type, cards, icons, UI, charts, transitions, light, voice, music and sound are each designed for this film to a high-end standard — nothing stock, templated or "good enough". Build every idea as a large, purpose-designed motion piece with negative space; real screenshots and screen recordings read as "cheap" even with a camera moving over them. No pill labels, numbered chips, tracked all-caps tags or dot-joined metadata. Generated images serve only as plates or assets and are checked at 100%.
3. **Depth, light, a moving camera — and full frames.** Flat layouts (text left, card right, plain background) read as "bland". Hero moments get a lit set: a floor that reflects, objects turned in 3D, light that travels, dust in the air, a camera that never fully stops. Every frame should work as a poster: layers of depth, a light source, the hero filling the frame (text readable on a phone), never a small element in a dark void. The brief's bullet points are a minimum, not the design.
4. **Every transition is a real move.** A camera move, a light, or an element that travels from one scene into the next. Never a flat white flash, never a pop; hits get a few frames of attack.
5. **Readable, even pacing.** Headlines stay ≥ 2 s, results ≥ 3 s after their line; lists reveal one item at a time; energy stays even across chapters. Never cram content to hit a length.
6. **Narration is sacred.** Never time-stretch it or squeeze its pauses: cut words and re-record instead. Breathe between lines, a little longer at chapter turns. Every chapter opens with a line that links to the one before. One voice and one model per language for the whole film and every patch; let the owner pick by ear.
7. **Music lands and carries.** The resolution falls exactly on the visual climax and the music keeps going under the next line; it never empties out as the picture peaks, never switches pieces with a hard cut, and stays restrained at the very end.
8. **Verify like an editor.** You can't watch or hear the film, so stand in for your senses: contact sheets of every scene in every language, frame strips across every transition, full-size stills of every text moment, the automatic glitch and audio scans, loudness per line, and an AI review whose claims you confirm on frames before acting. A cut not checked this way is not done.
9. **Own the loop, report plainly.** Decide sensible defaults and say what you decided; ask only for what is truly outside your control (a missing photo, a key, money). Report without file or code names: what changed, what was checked, what wasn't, where the files are, which one to send.

The full taste guide, with the reason behind each rule, is [quality-bar.md](references/quality-bar.md). Read it before designing.

## What you are making

Choose the film type first; it decides the shape (details and timings in [case-studies.md](references/case-studies.md)):

| Type | Typical | Narration | Pictures |
|---|---|---|---|
| Product showcase | 60–100 s, one cut per language | usually none; on-screen lines, optional captions | custom-designed motion pieces of the product's key ideas; fictional data only |
| Brand / organisation film | 2–4 min, a master language + other cuts | one narrator | the organisation's real photos, people and events + motion design; every claim fact-checked |
| Event / conference opener | 1.5–3 min, client's script | deep and punchy | cinematic 3D sets, depth-rebuilt photos, official names and logos, a climax that lands the event title |
| Teaser / short promo | 15–45 s | one short line per beat, or none | one idea in three beats: hook, turn (the hero moment), name |

The machinery is the same for every type: Remotion (React) renders the picture at 1080p60; one timeline file drives picture, narration, music and captions; Python in Docker makes the narration, score, sound and mix; measurements and an AI review check the result; a release script renders in chunks and packages the deliverable.

## Start: find out what's available

Run `tools/setup.sh` in the new project. It ends with `tools/providers.py`, which checks the keys in `.env` (never printing them), asks each service what it offers today, and picks the best per job: the newest Gemini Flash to review picture and sound, voices to audition (ElevenLabs and Gemini TTS), and the newest GPT Image for plates. OpenRouter is preferred (one key, many models, a visible spend cap); a free Gemini API key alone still covers narration and review; with no key the film still gets designed type, composed music, every check and the release. If a missing key would raise the quality, ask the person once — the wording, fallbacks and money rules are in [providers.md](references/providers.md). Trust the tool's current picks over any model name in these docs.

## Workflow

Work through the phases in order on a new film; on a revision, jump to the phase the feedback touches, then run review and release again. Copy this checklist into your notes and tick it off:

```
Film progress:
- [ ] 0 Setup: tools available, keys checked, budget agreed
- [ ] 1 Intake: brief quoted, brand files, deliverables agreed, machine checked
- [ ] 2 Facts: fact sheet with a source and status for every claim, avoid list
- [ ] 3 Script: languages set, narration in the timeline, every on-screen word in every language
- [ ] 4 Storyboard: one idea per chapter, hand-offs planned, one look sample shown
- [ ] 5 Build: scenes from cues, stills checked in every language
- [ ] 6 Narration: voice auditioned and locked, every line cut OK, cleaned, measured
- [ ] 7 Sound: score, effects, mix (voice ≥ 6 dB over music on every line)
- [ ] 8 Review: sheets, strips, scans, AI review; every finding fixed or explained; facts re-checked
- [ ] 9 Release: outputs verified, zip tested, delivered state committed, owner told where and what to send
```

### 1. Intake

- Read everything the owner sent (brief, script, report PDF, chat screenshots, earlier films). Quote their words into `docs/brief.md` with the round log; note mandatory wording and official names.
- Collect brand truth from the source: official logo files, palette from the site's CSS or the brand PDF, fonts that cover every language of the film (accents, diacritics, other scripts), product names and UI wording in each language.
- Settle the languages and deliverables up front (masters per language, captioned cuts, .srt, thumbnails, the zip); if the owner already has a package from an earlier round, mirror it exactly.
- Check the machine: free disk, Docker running, other renders or sessions on the same film (two agents on one film overwrote each other's work; if you find one, stop and ask who owns it).

### 2. Research and facts

- Read the real sources: `tools/webpage.sh <url> <name>` renders a page in a real browser and saves its text and a screenshot; when a site is down, follow the fallback list in [story-and-research.md](references/story-and-research.md) (an archive copy, other public sources, then the owner) rather than guessing.
- Run a research subagent with the brief in [story-and-research.md](references/story-and-research.md): every fact gets dated sources and a status (VERIFIED / SINGLE-SOURCE / SELF-REPORTED / UNVERIFIED / OWNER-STATED), plus an avoid list. Product films: read the real product's code and wording so every label, number and flow on screen exists in the product.
- Write `docs/factsheet.md`. Nothing goes on screen or into the narration unless it is there with a status; self-reported figures are attributed.

### 3. Story and script

- Pick the structure for the film type, then write the narration as one spoken piece: linking lines at every chapter turn, lists folded into sentences, numbers written the way they are spoken. Write each language natively, not as a translation; never make a voice say names from a language it doesn't speak — show the name, introduce the person by role.
- Put the lines into `src/film/timeline.ts`, caption breaks marked with " | " (and `onScreen: true` on a line the film shows as designed type, so its subtitle steps aside), and every on-screen word into `src/film/script.ts` for every language (its `LANGS` list sets the film's languages; the first is the master).

### 4. Look and storyboard

- One idea per chapter, each with its own visual concept, a hero moment, and a way in and out that hands something to the neighbour. Write it down in `docs/storyboard.md`.
- Decide where real 3D, depth-rebuilt photos or generated plates pay off ([remotion-craft.md](references/remotion-craft.md)). Show one representative frame or clip for anything that changes the look before building a whole set of it.

### 5. Build

- Start the project: `<skill>/scripts/new_film.sh <dir> <Film-Name>` (the name becomes the delivered file names), then `tools/setup.sh`. The starter is a working film — timeline, scene clock, captions, finish, glass and type kit, bloom, mirror floor, dust, light, depth photos, three example scenes, the audio engine and every tool below. Replace the example scenes; keep the architecture.
- Timeline first: scenes, named cue moments and narration slots live in `src/film/timeline.ts`; scenes animate from the cues (`cuesOf(scene, lang)`); `npm run cues` hands the same numbers to the audio. Change timing only there.
- For a long film, split scenes across parallel builder subagents with the brief pattern in [remotion-craft.md](references/remotion-craft.md); you stay the director and verify every report on frames.

### 6. Narration

Full method in [narration.md](references/narration.md). Write the narrator's profile and director's notes; respell what the voice gets wrong in `audio/vo/say.json`; audition voices from what `tools/providers.py` found and let the owner choose; record each batch in one request (`tools/vo_prompt.py` → `tools/tts.py`), cut and word-check every line (`tools/cut_lines.py`), clean and level them, and measure that patches still sound like the same narrator (`tools/voice_score.py`). Lock the exact voice, model and prompt in the README.

### 7. Music, sound, mix

Full method in [music-and-sound.md](references/music-and-sound.md). By default compose a licence-free score in code that changes on the picture's cue moments; cut a licensed track on its bar grid only when the owner supplies one. Sound design hits named cues. The mix ducks the music per line, masters to −14 LUFS with headroom for the AAC encode, and prints a voice-vs-music table.

### 8. Review (every round, before anything is shown)

Full checklist in [review-and-qa.md](references/review-and-qa.md): previews and contact sheets in every language, strips across every transition, full-size stills of every text and caption moment, `tools/qa_scan.py` on every render, `tools/audio_qa.py` on every mix and delivered file, and `tools/review.py` (the newest Gemini Flash watching and listening to a small whole-film copy). Act only on concrete flags you can confirm; its A/B preferences, voice-identity and small-text judgments are unreliable. Re-check every on-screen fact against the fact sheet.

### 9. Release and deliver

`tools/release.sh` ([release-and-delivery.md](references/release-and-delivery.md)) builds everything: narration check, score and mix per language, captions, thumbnails, masters and captioned cuts rendered in chunks, joined, peak-checked, frame-counted, zipped. `REDO=` re-renders only touched chunks; `LANGS=`, `VOICE=` for subsets and voice versions; `ZIP_ONLY=1` re-packages. Verify the outputs, commit the delivered state, update the README, and tell the owner exactly where the package is and that it is safe to send.

### 10. Feedback rounds

[working-with-owner.md](references/working-with-owner.md): treat chat screenshots and mid-task messages as the round's brief; fact-check new claims first; fix the pattern film-wide, not just the frame shown; keep what the owner didn't criticise; re-run review and release; answer point by point. Save every lasting preference where the next session will find it.

## Tools in the starter project

Run them; read their code only if one fails (each tool's first lines say what it does and how to call it). Python tools run in Docker images built by `tools/setup.sh` (film-audio and film-asr; `setup.sh all` adds film-voice and film-depth): `docker run --rm -v "$PWD":/p -w /p <image> python <tool> …`. Node, zsh and Swift tools run on the host.

| Need | Tool (from the project root) | Runs in |
|---|---|---|
| set up, check keys and models | `tools/setup.sh [all]`, `tools/providers.py` | host / film-audio |
| read a website (text + screenshot) | `tools/webpage.sh <url> <name>`, `tools/webpage.sh archive:<domain> <name>` | host |
| timing → audio | `npm run cues` (after any timing change) | host |
| narration take | `tools/vo_prompt.py audio/vo/narrator-en.md en [ids] > take.prompt`, `tools/tts.py <service>:<model> <voice> take.wav take.prompt [--lang en]`, `tools/tts.py --voices <model>` | film-audio |
| cut + word-check a take | `tools/cut_lines.py en take.wav take.prompt audio/vo/en l01,l02` | film-asr |
| narration hygiene | `tools/check_vo.py`, `deess.py`, `trim_lines.py`, `level_lines.py`, `declick.py`, `spans.py` | film-audio |
| same narrator? | `tools/voice_score.py --ref <original lines> -- <takes>`; `tools/listening_page.py spec.json page.html` | film-voice / film-audio |
| another voice, same film | `tools/voice_warp.py <voice>`, then `VOICE=<voice>` for score, mix, captions, release | film-asr |
| captions + .srt | `tools/captions.py [<lang> …]` | film-asr |
| score, sound, mix | `audio/score.py <lang>`, `audio/sound.py`, `audio/mix.py <lang>` | film-audio |
| music analysis / effect peaks | `tools/music_scan.py <track> [--bars]`, `tools/sfx_peaks.py <dir>` | film-audio |
| look at the film | `tools/preview.sh <name> <from> <to> [lang]`, `tools/sheet.sh <video>`, `tools/strip.sh <video> <t>`, `npx remotion still` | host |
| automatic checks | `tools/qa_scan.py <video> [--chunk 150]`, `tools/audio_qa.py <mix or video> [--sync t,…]` | film-audio |
| AI review | `tools/excerpt.sh <video> whole`, `tools/review.py "<prompt>" <media…>` | film-audio |
| generated images | `node tools/imagegen.mjs plate <name> "…"` (also `reframe`, `asset`), `tools/reframe_composite.py` | host / film-audio |
| photos in depth | `tools/depth/depth.py public/depth <photos>`, `tools/depth/layers.py <photo>` | film-depth |
| people cut-outs, masks (macOS) | `swift tools/mac/portraits.swift <in> <out>`, `swift tools/mac/subject_mask.swift` | host |
| ship | `tools/release.sh` (`REDO=`, `LANGS=`, `VOICE=`, `CAPTIONS=0`, `ZIP_ONLY=1`), `tools/phone_preview.sh` | host + Docker |

Keep temporary work inside the project (`tmp/`, git-ignored; Docker can't mount a session scratchpad under /private/tmp) and delete it after. Keys live only in the project's git-ignored `.env`; never print them.

## Pitfalls that bite every film

- R3F only redraws on frame changes: load textures and fonts outside the canvas (`useTexture`, `FontGate`), or frames render blank. `@react-three/postprocessing` renders black under Remotion: use the kit's `Bloom`.
- One NaN pixel blacks a whole frame through bloom; clamp every `pow()` base.
- An opaque background in a scene's pre-roll silently deletes the previous scene's ending: fade your ground in from your own start.
- Text measured before fonts load jitters; several render tabs draw centred text a pixel apart. Hence `FontGate` and concurrency 1 for finals.
- An animation threshold that never reaches 1 never settles (a wordmark's last letter kept scrambling). Check every end state.
- Each voice generation drifts (a patch came out +1.4 semitones "younger"): record with neighbouring lines, measure, let the owner pick.
- A fixed music duck under a dense score left music louder than the voice on some lines: duck per line.
- Never edit a running zsh script or `src/` while a release bundles; one release per project at a time.
- Never spend money or rent machines without asking first, with a number.

## References

All link from here; read the one the task needs.

| File | Read it when |
|---|---|
| [quality-bar.md](references/quality-bar.md) | before designing anything; when feedback says cheap, bland, glitchy, rushed, weird |
| [providers.md](references/providers.md) | at the start: which keys and services to ask for, fallbacks, models, money |
| [case-studies.md](references/case-studies.md) | choosing the structure, length and look for a film type; calibrating what "good" is |
| [story-and-research.md](references/story-and-research.md) | researching an organisation or product, the fact sheet, writing the narration |
| [narration.md](references/narration.md) | anything voice: casting, prompts, takes, patches, pronunciation, voice versions |
| [music-and-sound.md](references/music-and-sound.md) | score, stock music, sound design, mixing, loudness |
| [remotion-craft.md](references/remotion-craft.md) | building scenes: architecture, motion recipes, type, captions, 3D, photos, generated images, builders |
| [review-and-qa.md](references/review-and-qa.md) | every review pass; before showing anything |
| [release-and-delivery.md](references/release-and-delivery.md) | rendering finals, versions, packaging, machine etiquette |
| [working-with-owner.md](references/working-with-owner.md) | feedback rounds, options, reporting, costs, multiple sessions |
