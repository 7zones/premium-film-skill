# Music, sound design and the mix

## Contents
1. Two routes to a score
2. Route A: a licence-free score composed in code
3. Route B: a licensed track cut on its bar grid
4. Shapes that work (and the ones owners rejected)
5. Sound design
6. The mix
7. Checks
8. Pitfalls

---

## 1. Two routes to a score

| | A. Composed in code (`audio/score.py` + `audio/kit.py`) | B. Licensed track cut to picture (`kit.splice/stop_hit/freeze/open_filter`) |
|---|---|---|
| Used for | both product films, the 3½-minute brand film | the conference opener |
| Strengths | every chord change, swell and resolve lands exactly on the picture's cue moments; no licence; a recurring motif; an identity instrument | a real orchestra/choir recording, "epic" weight in minutes |
| Costs | composing time; General MIDI realism has limits (the strings and choir are good, solo instruments less so) | finding the right track, measuring it, editing on bars; the picture's big moments must sit on its bar lines |

Generated music (Lyria etc.) was tried and rated synthetic ("MIDI quality, static harmony"); not used.

## 2. Route A: a licence-free score composed in code

The starter's `audio/score.py` is a working example. The method:

- **Harmony on the picture's moments.** A chord map keyed to cue times from the timeline (`film.cue(...)`, `film.m(...)`): chords change when the picture changes. A minor colours resolving to the major on the logo worked twice (Am9 · Fmaj9 · Cadd9 · G6 → Cmaj9). A bass that walks down a chord per opening portrait; one chord per partner group; one per award card.
- **Parts:** `Part(GM[...])` notes rendered through FluidSynth with the MuseScore General soundfont: strings (48 — "strings2"/slow strings swells in over ~1 s and leaves a dip at every chord change), contrabass, cello, piano, choir, celesta, bells, glockenspiel, harp, horns, timpani. Each part renders alone into its own reverb (`kit.hall`). Humanise melodic parts (a few ms, a little velocity); keep pads straight.
- **Balance by measurement.** General MIDI programs differ a lot in level (piano ≈ 18 dB under strings at the same velocity): print each part's RMS and set gains from numbers, not trust.
- **Dynamics:** an expression curve (CC11) through `(time, value)` points keyed to cues — quiet open, a swell into each climax, never a dip right before a transition, a lift INTO the next section. Assert it runs forward in time.
- **A motif** (5 notes) that returns: under the founder, on the logo, in the major at the end. An identity instrument helps (a synthesised traditional instrument of the organisation's country carried the motif at three emotional peaks).
- **Synth layer** for pulse and weight: soft kicks (band-limited click, 1 ms fade-in), sub notes doubled an octave up (a 33 Hz sub alone is inaudible on laptops/phones), pads, risers. Keep it UNDER the orchestra; let a pulse grow in over two bars instead of starting at full level.
- **Builds land and carry:** a rising figure (harp, strings) into a scene change; the resolution exactly on the visual climax; a sustained chord and the groove carried under the next line.

## 3. Route B: a licensed track cut on its bar grid

1. **Find candidates.** Pixabay Music (licence allows use in films; skip items marked AI-generated). Its search pages return 403 to curl; a headless Playwright browser can read the page's bootstrap JSON (`results[].sources.src` = the mp3, plus downloads/likes/isAiGenerated). Queries: "epic cinematic trailer", "heroic orchestral", "documentary epic", "uplifting epic", "cinematic technology"… Filter by length and downloads; shortlist ~20.
2. **Measure, don't trust descriptions.** `tools/music_scan.py <track> --bars` (film-audio): tempo, a straight beat grid fitted to the detected beats (t0, beat, residual), the downbeat phase and bar times, the key, a sparkline of the track's shape (loudness, drums, sub, brightness, onsets) and a per-bar table with phrase marks. Gemini's mood calls (dark vs heroic) were consistent, but it invented structure (stop-time hits that don't exist). Listen-check the first seconds (one candidate opened with a hidden spoken countdown).
3. **Cut on bars.** `kit.bar_grid(t0, bpm)` → `bar(k)`; `kit.splice(track, [(src_from, src_to, dst_at), ...])` with whole bars, cut 12 ms before each downbeat (keeps the attack), 30 ms equal-power crossfades. Reuse a section (a breath + riser) where the picture needs a stop. Put the picture's scene boundaries on bar lines (timeline `M` landmarks) — the picture follows the music here.
4. **Stop-time hits** (a brief's "ngắt nhịp" / epic stop-start breaks): `kit.stop_hit(track, chord_time)` — the climax chord struck once, held 0.14 s, then only its reverb rings into silence; a boom under each; a reverse swell into the next; each spoken slogan starts ~30 ms after its hit.
5. **Handing one track to another** (never a hard switch): check the keys (chroma of the last chord vs the new track's bars) and enter the new track on a soft section in a key that follows; hold the outgoing chord across the gap with `kit.freeze(...)` (a spectral freeze of 0.4 s of the chord, swelling into the new downbeat, then fading under its first bar). Measured: the gap's level rose from −31…−35 dB to −17…−18 dB and the owner's "the music just changes completely, super weird" was solved.
6. **Accumulation:** `kit.open_filter(segment)` opens a low-pass from 6 kHz to 20 kHz and lifts the level ~2 dB across a build (a darker version read as a sag).
7. **Landing:** the full theme arrives on the visual climax (the emblem forming); the final hit on the bar AFTER the narration's last word; 4–5 s of ring-out. Match levels between tracks by loudness on comparable sections.

## 4. Shapes that work (and the ones owners rejected)

- Worked: quiet, tense open → a lift with the first chapter → a stop (silence or a breath) on the "double-edged" turn → a heroic re-entry → three stop-time hits on the slogans → a short build (~6 bars) → the full theme on the emblem → the final hit after the last word.
- Rejected: an over-long spectacle build with orbits and beams (~23 s: "too over-exaggerated… too long"); a break-off then a boom at the end ("mute then boom… a bit too much"); a jump from silence into a new track mid-groove; a big emotional build that empties out as the next section starts ("drops weirdly"); an upbeat groove right after a moving line, then a drop again at the next section.

## 5. Sound design

- Every key visual event has a sound, cued from the same named moments (`audio/sound.py` → `events(film)`): ignite → reverse swell + boom; a card lands → soft whoosh; numbers resolve → fine ticks; a scam ping → a deliberately dissonant, slightly bit-crushed tritone; a lock → clunk; a shatter; a radio sweep for broadcast; typing matched to the typed characters; a heartbeat for tension.
- Procedural effects (`audio/sfx.py`, seeded) and recorded ones (Pixabay, licence in `assets/SOURCES.md`) mix well: recorded impacts/whooshes/risers sound richer; procedural ones fit exactly. Place recorded effects at (moment − their measured peak) — `tools/sfx_peaks.py` (a whoosh peaks 0.6–1 s in; a reverse cymbal 3.4 s in).
- 6 ms fades on every effect; tame highs on the effects bus; effects duck under the voice a little less than the music.
- Soften for gentle visuals: low-passed chimes, no sparkle stacks under narration; nothing shrill or sustained above ~6 kHz (a reused variable once dragged a riser across 99 s as a "fan" hiss).

## 6. The mix (`audio/mix.py`)

- **Voice chain:** high-pass 75 Hz, a little warmth at 160 Hz, −1.5 dB at 320, +1.8 dB presence at 3.2 kHz, a de-ess dip at 6.8 kHz, compression 3:1 at −22 dB with a 9 ms attack. Lines pre-levelled to −20 LUFS.
- **Adaptive ducking per line:** measure each line's loudness and the score's under it; duck the score until it sits ~9 dB under the voice (10.5–12 dB for lines over a dense climax; slogans on stop-time hits only ~3 dB so the hits stay big). Bridge gaps < 3.5 s at 70% of the neighbouring duck so the music doesn't pump. Smooth: 0.18 s attack, 1.1 s release. Blend an EQ carve into the music under speech (−3 dB at 260 Hz, −3.5 dB at 2.5 kHz). A fixed −7.5 dB duck once left a dense score 1–9 dB louder than the voice on some lines.
- **Master:** gentle glue, −14 LUFS integrated, a look-ahead limiter without makeup gain at −2 dBFS on a 4× oversampled peak, re-normalised and re-limited three times, a short end fade. The −2 is headroom for the AAC encode, which raises peaks by up to ~1 dB (a −1.2 dBTP mix measured −0.3 dBTP in the MP4); the release measures each MP4 and trims the gain if it still lands above −1 dBTP. Judge loudness and peaks on the delivered file. Pedalboard's `Limiter` adds makeup gain (a master came out at −11.3 LUFS) — don't use it for the final stage.
- **Stems** (`audio/build/stems-<cut>/vo|music|sfx.wav`) for checks; the per-line table printed by the mix must show voice − music ≥ 6 dB on every line (aim ~8.5–9).
- **One mastered track per cut** (`public/audio/mix-<lang>[-<voice>].wav`); finals are rendered silent and the mix is muxed in by the release.

## 7. Checks

- `tools/audio_qa.py <mix or video>`: −14 LUFS, true peak ≤ −1 dBTP, short-term range, true clicks (isolated spikes above 9 kHz), sustained hiss above 9 kHz, holes (dead air), sudden drops between sections; `--sync t1,t2,...` lists the onsets near each big visual moment with their strength (a reverse swell's last rise, the hit's front edge, a boom's body); the hit should land within a frame or two (+30–40 ms is encoder delay).
- Per-line voice/music table from the mix; per-stem click checks if anything is flagged.
- A loudness envelope (1 s or 0.25 s windows) across every transition you changed: no dip before, no jump after.
- An audio-only review (`tools/review.py` with the mix as mp3) asking for timestamps of anything abrupt, harsh, masked, clipped or out of sync — then verify each claim by measurement (reviewers hear "jumps" that aren't there).

## 8. Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| A 99-second rising hiss | A flat 1,800-line mix script reused a global variable (`f0`) from another section | Keep sound events in functions with local names (`sound.py`); scan the >9 kHz band |
| Notes cut each other off | MIDI note-offs match by pitch: a repeated pitch's earlier note-off kills the new note | End notes exactly at the next onset; alternate pitches for percussion |
| Strings dip at every chord change | Slow-attack string patch | GM 48 strings; overlap chords by ~0.5 s |
| Docker exit 137 in the mix | float64 buffers, all parts in memory | float32; render parts one at a time; free buffers; chunked true-peak |
| Orphan sounds after a picture change | A cue was renamed or deleted, the score still used it | Grep the audio scripts for every cue name after cue changes; re-export cues |
| Logo hit inaudible | Energy only ~33 Hz | Add an impact and a note an octave up; check 60–250 Hz |
| Music louder than the voice on some lines | Fixed duck | Adaptive per-line duck + the table |
| Loudness 3 dB over target | Pedalboard Limiter makeup gain | The kit's look-ahead limiter |
| A random synth layer changes after an edit | Shared RNG consumed in a different order | Give each layer its own seed |
