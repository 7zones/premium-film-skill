# Film title

One paragraph: what the film is, for whom, how long, which languages and cuts, and the rules it follows (real photos only / fictional data only; every claim fact-checked in docs/factsheet.md). Keep this README true after every round: the next session (or colleague) starts here.

| Time | Chapter |
| --- | --- |
| 0–7.5 s | … |

## Commands

```bash
tools/setup.sh                     # npm packages, .env, Docker images, then which keys/models are available
npx remotion studio                # preview every scene (Scenes folder) and the whole film
npm run cues                       # after ANY timing change: hand the timeline to the audio tools
docker run --rm -v "$PWD":/p -w /p film-audio python audio/score.py en    # the score for one cut
docker run --rm -v "$PWD":/p -w /p film-audio python audio/mix.py en      # narration + score + sound → public/audio/mix-en.wav
tools/preview.sh <name> <from> <to> [lang]                                 # a quick half-size look, with sound
tools/release.sh                   # everything that ships → out/ (masters, captioned cuts, .srt, thumbnails, zip)
```

## Where things live

- `src/film/timeline.ts`: scene times, named cue moments, music landmarks and narration slots — the single source of truth. `scripts/export-cues.mts` hands it to the audio tools as `audio/cues.json`.
- `src/film/script.ts`: the languages (the first is the master) and every on-screen word in each. `src/film/scenes/*`: one file per chapter.
- `src/components/*`, `src/three/*`, `src/lib/*`: the shared kit (glass, type, captions, grain; bloom, mirror floor, dust, depth photos; scene clock, font gate).
- `audio/vo/<lang>/<id>.wav`: narration lines (narrator, model and prompt: `audio/vo/narrator-*.md`; respellings: `audio/vo/say.json`). `audio/score.py`, `audio/sound.py`, `audio/mix.py`: music, sound design, final mix.
- `docs/brief.md`, `docs/factsheet.md`, `docs/script.md`: the brief and its round log, the checked facts, the narration.
- `assets/SOURCES.md`: where every photo, logo, track and effect came from, and its licence/credit.

## Services and exact settings

Fill in once chosen, so every later patch matches (re-run `tools/providers.py` when keys change):

- Narration: service, model, voice (and voice settings), per language: …
- Review: model and route: …
- Images: model and route (or "none: real photos only"): …
- Budget agreed and spent so far: …

## Credits to publish with the film

- …

## Content rules followed

- …
