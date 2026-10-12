# The quality bar

Every rule below came from a cut that was rejected or corrected, usually in the owner's own words (quoted). Read the whole file before designing; come back to the matching section whenever feedback uses words like cheap, bland, glitchy, rushed, weird, distant or fake. When a rule seems to conflict with a brief, ask what the person would feel watching it: that is what the rules protect.

## Contents
1. The overall bar
2. Composition and components
3. Depth, light and 3D
4. Motion
5. Transitions and continuity
6. Pacing and readability
7. Typography and language
8. Photos and real people
9. Story and wording
10. Narration (taste side)
11. Music and sound (taste side)
12. Captions
13. Brand, logos and truth
14. Delivery

---

## 1. The overall bar

- The owner asks for "premium, polished… the best possible results", "pixel perfect", "dont settle for less… make it so perfect that ur satisfied urself". Reference points the team used: Apple keynote films, Stripe and Linear brand films, a prestigious national TV documentary.
- "Kinda basic… currently ur just merely following the script. Let ur creativity thrive": a brief's bullet list is the minimum. Find one unifying visual idea (a thread of light that the Earth's city lights become, that a prism splits, a blade cuts, threats corrupt and gold rescues), and ideally a recurring story object (one photo of a TV tower that the AI finds, that gets faked into a fire post, pirated, then verified).
- Silence is not approval: the owner rarely praises ("extremely good now" and "everything else is perfect" were the high points). Keep whatever was not criticised; don't replace a concept the owner liked with your own "upgrade" (a busier intro replaced a globe the owner preferred, and had to be rebuilt from logs).
- "Please look for all cheaply designed components and improve them all" / "fix all similar problems": when one thing is flagged, find and fix the whole pattern across the film, in every language.

## 2. Composition and components

- **No screenshots.** "Forcing too much UI into the video, not letting space for custom designed components… looks too cheap." Even when the owner suggested capturing screens, the result was rejected. Use the product only as the source of truth (palette, fonts, icons, module names, real labels, real flows) and recreate its KEY idea per scene as one large designed piece: a glass card, a gauge, a node network, a drawn chart, a phone lock screen.
- **One idea per scene, big, with negative space.** Text ≥ 17 px at 1080p everywhere, labels ≥ 24 px, key data 24–40 px, hero numbers 120 px+. For an LED wall in a hall: statements 100–130 px, threat words ~90 px; no hairlines.
- **No template tells:** pill-shaped labels ("those pills look cheap"), numbered chapter chips ("01 · DATA EXPOSURE"), tracked-out ALL-CAPS mono labels, dot-joined metadata ("214 mentions · 3 platforms"), rubber stamps, generic radar circles. Status = coloured text with a glyph; a container, if needed, is a small-radius (≤ 8–10 px) tinted tag. Modules = icon + name in sentence case.
- **Cards:** smoked glass, a gradient rim lit from above, soft layered shadows. No hard coloured borders. Photos inside cards are inset and the border is drawn LAST ("the image is appearing on top of the card, making the card border not connected").
- **Section titles** must be designed moments, not "02 —— title" ("this way of displaying the section title is so cheap"): an outlined numeral, a hairline drawing on, words rising out of masks with blur, a glint, then an exit.
- **Never one big lonely photo** ("to nhìn hề hề" — looks silly): rotate several real photos with light-sweep handovers, or set it in depth among others.
- **Brand mascots and real product artefacts beat generic graphics** ("show the mascot here instead of those circles").
- Complete mock-ups: a website inside a browser window must show whole, not cropped at its edges.

## 3. Depth, light and 3D

- Flat layouts read as "simple and bland": text column left, one card right, plain background. Hero scenes need a lit SET: a reflective floor that fades into haze at the horizon (never a hard line), objects turned in 3D, light that moves (sweeps, beams, shafts, bloom), dust in the air, and a camera that moves through space.
- Real 3D (React Three Fiber) was what finally read as premium for the conference film: depth-rebuilt photographs, glass, mirror floors, volumetric light, particles. 2.5D panels over plates read as a "corporate explainer".
- Photos given depth must be split into two layers (near cut-out over an inpainted far layer); a single depth surface smears around people when the camera moves ("it creates a shadow on all images u animate").
- **Full, rich frames — most of all in short films.** Every frame should hold up as a poster: at least three layers of depth (out-of-focus particles or glass in front, the hero in the middle, a lit environment behind), a visible light source, and real materials (reflection, refraction, haze). The hero fills the frame at its moment: a UI card or device ≥ ~55–65% of the frame width (its text must read on a phone), a headline ≥ 72 px. Dark is premium; empty is not — large stretches of plain black, thin lines floating in a void, or a small card in the middle of a big dark frame read as sparse. When an image service is available, a lit environment plate (GPT Image) behind a 3D or UI hero is a quick way to add depth. A trial teaser whose leaked-record cloud was thin lines on black, with a small card, looked clean but sparse next to the real films.
- Don't put type over bloom or a hot spot; give it clean dark space.
- Keep white logo plates below the bloom threshold; never let a brand colour blow out to white.

## 4. Motion

- "Please make every component more polished, animation happens more smoothly." Entrances: rise + sharpen out of a blur + fade, with a strong ease-out. No springy overshoot on UI. Exits mirror them (lift away, soften).
- Nothing just appears, sits, or vanishes ("it just instantly displays without any animation, and it just shows the 4 cards there for like 10 s, looks so bland"). Every element enters and exits; no hold over ~2–3 s without something moving (camera drift, light, particles). A client flagged "1–2 seconds of dead picture" as a drop in emotion; scan for still stretches ≥ 1 s (`tools/qa_scan.py`). Drift alone is not enough for long holds: one composition on screen more than ~4 s needs a second beat inside it (the camera travels to a detail, a new element arrives, the cursor acts) — a trial teaser's warning card held 6 s on a slow push and sheen, and read as static.
- Graphs draw from start to end (bottom-left to top-right for a rise); they never morph or slide into place ("it shows half of the graph, then it kinda moves up weirdly").
- Effects must visibly apply to the whole object (a wordmark decode that only touched the last letters read as broken), and every animation must settle (the last letter that kept scrambling forever was a float threshold that never reached 1).
- Hits, flashes, rings and locks get a 3–4 frame attack; an instant attack reads as a glitch. No per-frame random jitter or camera shake.
- Numbers resolve by focus (the final value, blurred, pulls sharp); a count-up that is readable mid-count ("157 triệu+") was flagged. If you count, finish while still blurred and use tabular figures.
- Typing: ~25–30 characters/s with an uneven human rhythm and a hold before sending (52 cps was "too fast").
- Mid-animation frames are not typos, but reviewers will call them typos; make sure settled frames are perfect.

## 5. Transitions and continuity

- Every transition is a real camera or light move: push, pull, dive, whip, focus pull, light sweep, iris, truck along one continuous stage. Never a flat white or grey wash, never a pop. The good ones carried an element across: a spark becomes the next scene's core; an ember stretches into the next scene's gold line; the shielded core's light becomes the dawn; reports drop into the next scene's pipeline; the dome becomes a globe.
- "The transition into AI agent kinda not smooth, like it's been very fast pace, then to the AI agent it's kinda slow": energy must be continuous across chapter cuts, in picture AND music.
- "The part before this… is kinda far from this, which makes the scene feel a bit distant": adjacent sections share something on screen (the previous photo racked out of focus behind the new element) and the narration gap after a colon stays short (3.4 s → 1.7 s fixed it).
- "This part [a big emotional build] just drops weirdly on the next section": land the build ON the climax and carry the chord and groove into the next line; the next scene must not look dimmer than the climax.
- Engineer hand-offs numerically when two scenes share an element (same centre, radius, tilt, spin rate; a shared routine that paints an identical burst on both sides; brightness continuity measured across the cut).
- Scene pre-rolls are transparent: an opaque ground in the incoming scene's lead-in silently deletes the end of the previous scene.
- Fly-throughs of planes (text, glows) need a fade margin, or the camera crossing the plane flashes for one frame.

## 6. Pacing and readability

- "The current intro too fast I can't read": hold each headline line ≥ 2 s; results/answers ≥ 3 s after their line ("the AI answer was fully visible for under 1 s"); award cards and clues readable ≥ 1.4–2.2 s at their size.
- Problem before fix in product demos (the fake page loads, then the block lands ~0.8 s later, then holds ~3 s); reasons and list items one at a time, ~0.35 s apart; 1.2–1.5 s between narration lines.
- "Every part should have their place with enough timing… it can be a bit over [the length]": never cram.
- "A bit slower" means about 10% (25% slower was "too slow"; product film pace settled at 1.1 s per unit between 1.0 too fast and 1.25 too slow). Keep pace a single global knob for product films.
- An intro of 12 s before the first content beat was "kinda long"; ~9 s was accepted.
- Even pacing across chapters; a fast section next to a slow one "feels broken".
- Each language is judged on its own pacing: a shorter English read placed in the slots of a longer Vietnamese master left 2.4–3.7 s silences and was "awkwardly long". Give each language its own timing where the reads differ.

## 7. Typography and language

- Fonts must cover every language of the film (accents, diacritics, other scripts): a missing glyph falls back mid-word. The starter uses Be Vietnam Pro for running text, Space Grotesk / Noto Serif Display for display, JetBrains Mono for data; Latin-only brand faces only for wordmarks.
- Size single-line titles to their length per language (`fitSize`): translations run 15–60% longer than English (German, French, Vietnamese…). Check every frame of every language: truncated lines (only the first half of a translated tagline showed) and wrapping labels were caught by the owner.
- Two-tone headlines (white lead + accent) where the brand does it; one colour where the brand does that. Follow the brand's own site.
- Masks for rising text leave room above and below for diacritics.
- Text must be rock-steady ("this text kinda not staying but constantly glitching its position"): fonts loaded before anything measures (FontGate), finals at concurrency 1, no resting transforms left on settled text.

## 8. Photos and real people

- Real organisations: their real photos (events, team, founder). People keep whole heads ("ur cropping too wrongly, making his face not complete"); every portrait framed the same way (face ~30% of the square, hair top 12% below the edge).
- No glow, rim light or halo around real people ("why there's like a weird aura / green shadow around him"). Grade and vignette only.
- No generated backgrounds behind cut-out real people (a client called it weird). Extending a real photo's own surroundings is acceptable when the person stays the original pixels (Codex canvas + re-composite).
- AI-generated video and images of a real organisation's world were rejected three times as "too fake" — while AI reviewers rated them 8.5–9.5. Default: none. Show one sample and get a reaction before generating a set.
- Never attach crime categories to frames of real people; fake-news/deepfake examples use fictional imagery only.
- Avoid insignia, emblems and political banners in real photos unless the client wants them; flag what you keep.

## 9. Story and wording

- Every section must flow through the voice-over itself ("after 'free for everyone', you just jump straight to the extension — that feels very weird… ensure each section has a smooth transition in voiceline"). Open sections with connectors: "To fight those traps…", "Among them…", "As for…", "Beyond that…", "Thanks to that…", "Besides…", "Behind those tools is a team…", "To date…".
- A bare list sounds unnatural ("Kỹ sư, chuyên gia bảo mật…" — "seems very weird, not natural"): fold it into a sentence ("Behind those tools is a team of engineers, security experts…").
- A list of names "seems like a procedure": close it with a line that carries meaning ("Together, they turned that promise into a shield for the whole community"), with a visual and musical payoff on its key words.
- Warm, plain language, not technical claims ("don't say 'data is shared with…', say 'we connect with them to help stop scams faster'").
- Don't reuse slogans or names owned by others (a slogan matching a national TV programme's name was replaced).
- Product films: show the product as built (real labels, real email template, real endpoints); never invent a feature (a "similarity %", a "Suspicious" verdict and a countdown that don't exist in the UI had to come out).

## 10. Narration (taste side; method in narration.md)

- The narrator must sound like one person: "the voice of the new part is kinda young, not the correct voice. The original voice is a deeper and calmer voice" (it was +1.4 semitones off); "the voice in the co-founder part sounds different… quite high pitch and faster".
- Never speed up or squeeze the read: "keep the pacing between sentences so it's not like you're forcing speed".
- "Natural, conversational" reads came out flat ("sounds like just reading the script without emotion"); a per-beat emotional direction gave "more dramatic, with more intonation and emphasis".
- "Punchy" means emotion and emphasis, not a new, brighter, louder voice ("I don't like this voice. Keep the old voice, or a similar deep one, but more punchy, more emotion"). Keep the timbre the owner knows.
- Correct pronunciation of loanwords and acronyms in the local way ("it should be pronounced correctly as 'ây ai'").
- English narration must not mangle local names; introduce people by role, show names on screen.

## 11. Music and sound (taste side; method in music-and-sound.md)

- "Better soundtrack", "rich sound": a real score (orchestral + synth, or a licensed cinematic track cut on its bars) with a returning motif, builds that land, and sound design on every key visual event.
- Never a hard switch between pieces: "right after this part the music just changes completely, which feels super weird… you can make your own sound if needed". Bridge harmonically.
- Restraint at the end: "too over-exaggerated… the final part having a mute then boom being a bit too much". A short build, a proportionate final hit on the bar after the last word, no silence-then-boom, no white flash.
- "Upbeat music with an accumulation effect to the end… preparing for the final sentence" — accumulate (filter opening, rising level, monoliths on the beat), then land.
- Honour every SFX and music line of a client's brief ("you missed this part: Epic Climax, ngắt nhịp đứt gãy" → three stop-time hits on the slogans).
- Nothing shrill or constant ("a very weird and annoying fan sound… very high pitch… seems like not belong there").
- Big visual hits need audible energy above ~60 Hz (a 33 Hz sub alone is inaudible on laptops and phones).
- After an emotional line, don't jump into an upbeat groove and then drop again at the next section.

## 12. Captions

- "Always display in 1 line only with a transparent black text background": one line per caption (≤ 42–52 characters), on an rgba(0,0,0,0.6) band, appearing as its first word is spoken. Never two lines or a gradient shade.
- In the captioned cut, hide on-screen text that repeats the narration ("we shouldn't have the video text, it's being duplicate"); where the words ARE the picture (a 3D slogan, a title card), the subtitles step aside instead (`onScreen` on that line).
- Graphics that sit low lift clear of the band in the captioned cut; nothing overlaps.
- Short product films: one short caption line per beat, ≤ ~17–19 characters per second.

## 13. Brand, logos and truth

- "It's gonna be a disaster if you got just 1 logo wrong": logos only from the organisation's own files or site, never redrawn, retyped or recoloured, shown no larger than their native resolution, on plates if needed.
- Official names and titles copied verbatim from the organiser's documents (an official workshop title differed from the brief's; a partner was "5G Multimedia", not "5G Media"). When the brief and the official source differ, ask once with the official wording as the recommended option.
- Fact-check everything ("please fact check all the things before you make any change"). Calibrate wording to the evidence ("can… within 1 to 24 hours", "an estimated 200 million", "connects with"). Drop what can't be verified.
- Product demos: only fictional brands, domains that don't resolve (checked with `dig`), documentation IPs (198.51.100.x, 203.0.113.x, AS64500), invented actor names; no real companies, malware, CVEs, vendor logos or attack arcs between real countries.
- No map borders on a globe for government clients; city lights only.

## 14. Delivery

- The deliverable is the package the owner sends (e.g. one zip: masters + captioned cuts + thumbnails at its root). Rebuild it after every release, mirror an existing package exactly, and say where it is and whether it's safe to send. Don't ship extras nobody asked for ("remove all the preview files, remove the render of music only too").
- Keep previous versions when making a new one (label the new one clearly: -v2, -<Voice>).
- Options when exploring ("try some, I want to have options"): finished alternatives plus a page to compare them.
