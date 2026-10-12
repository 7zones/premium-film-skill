# Release and delivery

## Contents
1. What a release does
2. Running it well
3. Partial re-renders, languages, voice versions
4. Verifying the outputs
5. Packaging and handing over
6. Machine etiquette (shared Mac, disk, other sessions, money)
7. Speeds to expect

---

## 1. What a release does (`tools/release.sh`)

cues → every narration line present and glitch-free (`check_vo.py`) → score + mix per language → captions + .srt → bundle (audio left out; the picture renders silent) → thumbnails (Thumb-<lang>) → for each language: the master, then the captioned cut, rendered in 150-frame chunks (JPEG quality 100, crf 16, yuv420p, concurrency 1, 5 retries per chunk, waiting for free disk and for other projects' renders) → chunks joined without re-encoding, the mix muxed in (AAC 320k, faststart) → frame count verified → .srt copied → the zip (stored, uncompressed) rebuilt and tested.

Why chunks: unless the OS reports lots of free RAM (macOS rarely does), Remotion keeps every frame on disk until it encodes — tens of GB for a 3-minute film — and full-length renders died with ENOSPC on a nearly full disk. Why concurrency 1: several render tabs share Chrome's GPU budget and some draw centred text a pixel apart (a title "constantly glitching its position"); per-chunk start-up dominates anyway (150 frames ≈ 10–15 s at 1 or 8 tabs). Why silent + mux: no inline audio mixing in Remotion (it writes more temp files); the mastered mix is exact.

## 2. Running it well

- Run it in the background with a log; check the log, not the terminal. A 3½-minute film with four 60 fps cuts took ~75 min on an M4 Pro; a 20 s film ~3 min.
- Never edit `tools/release.sh` while it runs (zsh reads scripts as it goes): run a frozen copy (`cp tools/release.sh tmp/release-frozen.sh && zsh tmp/release-frozen.sh`). Don't edit `src/` while it bundles (a race broke a bundle). One release per project at a time (they share `.render-tmp`); chain a second after the first exits.
- The "other renders" guard matches any process whose command line contains "remotion render" and doesn't contain this project's path — keep that phrase out of any monitoring command you run, or the release waits on you.
- If Claude Code's memory-pressure reaper kills a long background job, report what finished and what didn't; don't restart heavy jobs unasked (`CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` exists if the owner wants it).
- Keep durations a whole number of 1/30 s (the 30 fps draft composition needs whole frames).

## 3. Partial re-renders, languages, voice versions

- `REDO=a-b tools/release.sh`: re-renders only chunks touching frames a–b and reuses the rest from `.render-chunks/` — valid only if the timeline before and after is unchanged (a visual-only fix). A one-frame fix costs minutes instead of an hour. `REDO=99998-99999` reuses every existing chunk (e.g. to finish an interrupted release).
- `LANGS=en tools/release.sh`: only that language's cuts; the zip still collects every language's existing files.
- `VOICE=<name> tools/release.sh`: the voice version (after `tools/voice_warp.py <name>` and `npm run cues`); outputs end in `-<Name>` with their own chunk folders and zip; no new thumbnails.
- `CAPTIONS=0`: skip captioned cuts.
- Audio-only change: no picture re-render — re-mux the existing video with the new mix (`ffmpeg -i old.mp4 -i public/audio/mix-<lang>.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -movflags +faststart new.mp4`).
- Patching by hand (rare): keyframes fall on chunk boundaries, so segment/concat by stream copy is exact; a chunk with a different timescale breaks a join (remux it with `-video_track_timescale <neighbour's>`); always verify frame counts (`ffprobe -count_packets`) and decode-check the splice.

## 4. Verifying the outputs

- `ffprobe` each file: duration, 1920×1080, 60 fps, frame count (the release asserts it), audio present.
- `tools/qa_scan.py --chunk 150` on each master; `tools/audio_qa.py` on each (the release already trims a mix whose AAC peaks land above −1 dBTP; it prints when it does).
- After a stopped release or a hand fix: `ZIP_ONLY=1 tools/release.sh` rebuilds the zip from what is in `out/` and lists when each file was made — never send a zip without checking those times.
- A sheet of each master; stills of every moment you changed; the captioned cut's subtitle moments.
- `unzip -l` the package: exactly the expected files at its root.

## 5. Packaging and handing over

- The deliverable is what the owner sends on: by default one zip with every language's master, captioned cut and thumbnail at its root (stored, not compressed); .srt files beside it. If the owner already has a package, inspect it (`unzip -l`) and mirror it exactly — and refresh any unzipped copy they keep.
- Don't ship extras nobody asked for (phone previews, music-only files): they were removed on request. Make a 30 fps phone copy (`tools/phone_preview.sh`, < 25–30 MB) only when someone needs to watch on a phone through a chat app.
- Thumbnails: the Thumb-<lang> compositions (designed poster) or a frame of the finished film; a lone `remotion still` of a 3D moment can miss lighting that builds over frames.
- New version = new files, old kept (`out/v1/`, or a `-v2` / `-<Voice>` suffix); overwrite a version's own files in place so no stale file is left to send.
- Say exactly where the package is, which file to send, and whether anything in the folder is stale or still rendering ("don't send the zip until I confirm"). The owner asked "is it done? where do you store the videos?" three times in one round when this was missing.
- Commit the delivered state locally (`git add -A && git commit`) so any earlier version can be recovered.
- Credits to publish (CC BY photographers, etc.) go in the README and the report.

## 6. Machine etiquette (shared Mac, disk, other sessions, money)

- Check before heavy work: `df -h` (renders need a few GB; the Mac often had < 3 GB), `pgrep -fl "remotion render"`, running Docker containers, and the load (`uptime`): under other sessions' work a 150-frame chunk went from 15 s to 2.5 min. Estimate the finish from the first few chunks and report that ETA; never start a second heavy job of the same kind next to someone else's (Whisper, depth and renders all compete for the same memory — a depth job was killed for memory while two Whisper jobs ran). Wait for space; never delete the owner's files (VM disks, other projects, downloads) — say what is using the space if it blocks you. Clean only your own caches and temp folders.
- Use a private TMPDIR inside the project (other sessions' clean-ups wiped shared temp folders mid-render). Docker can't mount a session scratchpad under /private/tmp: keep Docker work inside the project, delete it after.
- Kill only your own processes (never a broad `pkill chrome`); don't restart shared services (Colima) others use.
- Two agents on one film overwrote each other's narration and zip. Before acting, check recent file changes (`find . -mmin -120 -type f -not -path "*/node_modules/*"`) and running processes; if another session is on the film, stop and ask the owner who owns it; answer coordination questions from other sessions promptly with your scope.
- Never spend money or rent infrastructure without asking first, with the size and price. A 180-CPU cloud machine rented "to render faster" cost money, produced nothing (renders timed out), and angered the owner. If approved: test one chunk small first, tear everything down (VM and volume), report the exact cost. Prefer local headroom (render a different deliverable in parallel).
- API spend: check the key's balance before batches; report spend in the round's report.

## 7. Speeds to expect (M4 Pro, shared with other work)

| Job | Time |
|---|---|
| 150-frame chunk, 1080p60, 2D/light 3D | 10–15 s (2.5 min on a busy machine with heavy 3D) |
| Full release, 3:41 film, four 60 fps cuts | ~75 min |
| Half-size preview of 30 s | ~45 s |
| Score + mix of one language | 15–60 s |
| Whisper cut of one take (`--jobs`) | ~40–70 s |
| One TTS batch take | 10–60 s |
| A patch via REDO | ~3 min |
