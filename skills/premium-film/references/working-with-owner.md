# Working with the film's owner

The owner (the person you work for) usually relays a client or a team, writes short messages, and expects you to run the whole production yourself. These habits are what made the four films land.

## Contents
1. Autonomy: decide, don't ask
2. Reading feedback
3. Mid-task messages
4. Options and versions
5. Reporting
6. Keeping the knowledge
7. Interruptions, limits, long jobs
8. Money and accounts

---

## 1. Autonomy: decide, don't ask

- Make the call with a sensible default and say what you decided. Ask only what is truly outside your control: a photo that doesn't exist publicly (ship a placeholder meanwhile), a sign-in, rights, money, or a naming conflict between the brief and an official source (ask once, with the official option marked "Recommended").
- Don't pause a round for yes/no questions about details: decision questions in the films were answered with a word ("continue") and the work had stalled for nothing.
- Verify before asking the owner to change anything on their side (a "blocked download" turned out to be a slow one).
- Never make the owner do work you can do (cleaning up, renaming, re-zipping). "Never assume I or anyone else will do anything for you."
- Keep what the owner liked. Two of your own "improvements" (a busier intro, faster typing) replaced things the owner preferred and had to be reverted.

## 2. Reading feedback

- Feedback arrives as screenshots of a team chat (often in another language), a frame grab with a few words, or a forwarded client message ("I don't quite understand, but make the changes your best way"). Translate it, list every point, and treat the list as the round's brief.
- A screenshot shows one instance; the owner means the pattern: "please fix all similar problems". Search the film for siblings (a client's "dead picture" at 1:46 led to a second one found by scanning).
- Vague words have known meanings here:
  | They say | They mean |
  |---|---|
  | cheap, bland, basic | flat layout, template chrome, static holds, no depth or light; or just following the script |
  | glitch, weird transition | a pop, a blocky dissolve, a one-frame flash, an instant attack, a cut with no carried element |
  | too fast / can't read | holds under ~2 s for lines, ~3 s for results; typing > 30 cps |
  | a bit slower / faster | about 10%, not 25% |
  | drops weirdly, distant | the music or picture empties out at a section change; a long gap after a colon |
  | not smooth / procedure | a beat starts under the previous one; a list of names with no meaning line |
  | voice wrong / young | pitch or brightness drifted from the original narrator; a different model |
  | more punch / emotion | emphasis and conviction in the same deep voice, not a new brighter voice |
  | over-exaggerated | escalating spectacle and theatrical silence-then-boom at the climax |
- When a screenshot you're referred to didn't reach you (pasted text shows "[Image #6]" with nothing behind it), say so, fix the likeliest culprit, and ask for the time in the film.
- Re-read the client's original brief each round: a missed line ("Epic Climax, stop-start breaks") is noticed.
- Fact-check new claims in feedback before writing them in (§9 of story-and-research.md).

## 3. Mid-task messages

Half the owner's messages arrive while you're working (they surface as "the user sent a new message while you were working"). Fold each into the current round at once: a new constraint goes to any running helper agents immediately (SendMessage); a status question gets a Done / In progress / Still to do answer; a pointed-out miss gets "yes, I had missed that" and a fix. Keep each on your to-do list across interruptions and compactions, and answer it by name in the round's report.

## 4. Options and versions

- "Try some, I want to have options": produce real alternatives (a finished version 2, a five-voice audition) with a recommended default and a page to compare them (`tools/listening_page.py` for voices; a short page or sheet of stills for looks). The owner picks by ear/eye; they paste back their pick.
- Keep the previous version when making a new one; label clearly (v1/v2, -<Voice>); the main deliverable doesn't change unless the owner says so.
- Before generating a whole set of anything that changes the look (AI stills, a new style), show one sample and wait for a reaction.

## 5. Reporting

- Plain language, high level, grouped by the owner's points. No file names, function names or code. What changed, what was checked and how ("checked by measurement, not by ear"), what wasn't checked, what you rejected and why (a reviewer's false note, a logo request for a pillar that has no partner), and anything you added beyond the request (with an offer to revert). Name what is outside your control (a quota reset time, a budget) with numbers.
- "Is it done?" comes often: answer in one line (yes/no, what's still running and when it ends), then the package location and which file to send, and whether anything in the folder is stale.
- Progress during long jobs: short notes with a clock-time ETA.
- Mention risks the owner should know: photo rights and credits, partner logos visible in real photos, a key pasted in chat (suggest rotating it), a claim the client must confirm.

## 6. Keeping the knowledge

- Write every lasting preference and decision where the next session will find it, the moment it happens: the project README (structure, commands, credits, content rules) and Claude's memory (feedback with "why" and "how to apply"; project state per round). The films stayed coherent across many compactions and sessions because of this.
- Keep `docs/brief.md`'s round log and the fact-check docs current.
- Record exact settings that produced approved results (narrator model + voice + prompt file, mix constants), so a patch weeks later matches: "check the past conversation to get the exact voice setting" is a real request.

## 7. Interruptions, limits, long jobs

- Usage limits and app restarts happen mid-round. Leave a resumable state: scripts in the project (not in a session scratchpad), chunked renders that reuse finished chunks, a short "Done / Left / Needs you" note (e.g. `audio/vo/r10/NEXT.txt` with scores and picks), and memory updated before long waits.
- Background helper agents can die at a limit: brief them to save output early and incrementally; resume them with SendMessage; don't depend on a helper staying alive.
- Long jobs run in the background with logs; use wait-loops or the Monitor tool, not sleeps; don't start a second heavy job of the same kind (two Whisper containers ran out of memory).
- Daily quotas (TTS): schedule a follow-up after the reset instead of switching models.

## 8. Money and accounts

- Find out at the start which services the owner has ([providers.md](providers.md)) and use the best of them; free tiers first, and any paid spend (API credit, generated images, cloud machines, stock purchases) needs the owner's yes, with a number. Report spend each round. Respect routing rules the owner sets (e.g. "this key only for Gemini; Claude only through our subscription").
- Keys go in the project's git-ignored `.env` (mode 600), loaded by the tools; never printed, never in memory or docs.
- Never borrow another project's key without asking. Never drive the owner's personal apps or accounts beyond what they asked (if you must automate a desktop app, guard every keypress by checking the frontmost app).
