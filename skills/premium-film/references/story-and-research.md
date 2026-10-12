# Research, facts and story

## Contents
1. What to collect first
2. The research subagent (brief template)
3. The fact sheet and the avoid list
4. Real organisations vs product demos: data rules
5. Photos, logos, footage: sourcing and rights
6. Writing the narration
7. Bilingual films
8. The storyboard
9. Fact-check rounds during feedback

---

## 1. What to collect first

- **The owner's material:** report PDFs (`pdftotext` for text; `pdftoppm -r 50` page renders tiled into contact sheets to see layout and photos; `pdfimages -png -p` to extract embedded images — pair images with their soft masks to rebuild transparent logos), scripts, chat screenshots, earlier films.
- **The brand from its source:** open the website in a browser, read computed font families and colours with JavaScript, take the logo SVG path straight from the DOM (verify it numerically against your saved copy). Product films: read the product's CSS tokens (convert OKLCH to hex), its i18n files (exact module names per language), its icons, its email templates and API routes.
- **When a site won't load or shows nothing**, work down this list and record every source with its date:
  1. `tools/webpage.sh <url> <name>` renders the page in a real browser (many sites show nothing until their JavaScript runs) and saves its text and a full-page screenshot — the screenshot is also the quickest look at the brand's real colours, type, logo and product UI.
  2. If the site is down (an HTTP 5xx such as 522, a timeout): `tools/webpage.sh archive:<domain> <name>` opens the newest Internet Archive copy; check its date (an old copy may describe a different product).
  3. The company's other public sources: its parent company's site and product pages, public social posts, app-store listings, press releases, event and partner pages, search results.
  4. Ask the owner, without stopping work: the feature's exact name in each language, what it does step by step, screenshots or a demo account, the brand kit (logo files, colours, fonts), and any claims they want made. Until they answer, show only what you could verify, in plain generic wording, and list the open questions in your report.
- **Official names:** for events, the organiser's own notice; for partners, how they write their own name (a partner was "5G Multimedia" on its own site, not "5G Media" as in the brief). When the brief and the official source differ, ask once with the official wording as the recommended option.

## 2. The research subagent (brief template)

Run it in the background while you design; it took ~45 min and 80+ sources for the brand film. Adapt:

> Research <organisation> for a public brand film. Produce a VERIFIED FACT SHEET in markdown. Every fact gets a source URL with its date and a status: VERIFIED (two independent sources or one official primary source), SINGLE-SOURCE, REPORT-ONLY (only in the organisation's own report), SELF-REPORTED (the organisation's own claim), or UNVERIFIED. (OWNER-STATED is the extra status for claims that come only from the owner's brief.) Search in the organisation's own language(s) and in English: Wikipedia (each language), the country's major national newspapers and broadcasters, international bodies relevant to the field, and the organisation's own channels. Verify, extend or correct this list of claims from their report rather than repeating it: <claims>. Sections: Timeline, Awards (exact name, category, year, grantor), Numbers (with their definitions — different sources count differently), Partners (only publicly documented relationships), Programs, Products, International, Founder story, Quotable lines (under 15 words), an AVOID LIST (what must not be said or shown, and why), Open questions. Do not upgrade self-claims. Never log in, never submit forms, never use Facebook or other walled sources. Write to docs/factsheet.md as you go (save early; a usage limit can stop you mid-way).

For a later round (new awards, a new year), the same brief with a time window and the existing rail entries; it found that no national award existed yet for the new year, corrected dates ("June, not May"), roles ("an implementing partner", "speaker", "by video") and kept three verified milestones with real photos.

## 3. The fact sheet and the avoid list

- `docs/factsheet.md`: claim as it will be said/shown · status · sources · safe wording per language · where used.
- Nothing goes on screen or into the narration unless it is there with a status. SELF-REPORTED figures are attributed ("an estimated…", "according to…"); averages and plans are worded as such ("can… within 1 to 24 hours", "helping stop scams faster").
- What research corrected in practice: founding vs registration dates; an event's exact name and month; a speaker listed as a "partner"; a ministry name the organisation itself had wrong; two "big numbers" defined differently that must never sit side by side; partners with no public trace (dropped); a claimed standard with no public feed (dropped).
- The avoid list matters as much as the facts. From the brand film: no details of a founder's troubled past (one respectful line at most: "someone who once stood on the other side of the story"); no "took down" wording that reads as hacking back; no rescues or money recovery; no politics; no real flagged domains; no logos as endorsements; no victim data; no commercial ventures; only official handles.

## 4. Real organisations vs product demos: data rules

**Real organisation films:** their real people, photos, events and numbers; every claim fact-checked; scam/threat examples fictional; partners as typography plus real photos of joint events, never a logo wall; avoid emblems, political banners and big-tech logos in photos unless the client wants them (flag what you keep).

**Product demo films:** every example fictional and non-resolving:
- the customer is "YourBrand" (`yourbrand.com.vn`);
- lookalike domains checked with `dig +short <domain> A` / `NS` (no answer = safe);
- IPs only from documentation ranges (198.51.100.x, 203.0.113.x, 192.0.2.x) and private ASNs (AS64500–64511);
- invented actors and gangs (TA-2217, RX-44), redacted victims, masked phones and passwords, placeholder executives;
- no real companies, malware families, CVE IDs, vendor or code-host logos, attack arcs between real countries. Audit every on-screen string, number and logo before the final (the product's own demo data contained real company names, a real IP and a real CVE). Show the product as built: real labels, real flows; never invent a feature.

**A product you can't inspect** (unreleased, no code or UI to read, a one-paragraph brief): show only what the brief states it does, in a UI you design for the film (it must not imitate any real app's chrome); no detection reasons, scores, user counts or other stats the brief doesn't give. In the fact sheet, mark the brief's claims OWNER-STATED and list them in the report for the owner to confirm. Lure content (the scam message, the fake page) is generic and invented: a courier "fee", a prize, a locked account, from a masked sender, on a domain checked as non-resolving; never a real bank, courier, shop or app name. No logo files: set the product name in the film's type as a wordmark (never draw a logo mark), say so in the report and ask for the files for the final.

## 5. Photos, logos, footage: sourcing and rights

- **The organisation's own photos** first (the owner can clear them: "images captured about us can be used by us"). A photo subagent can find dozens in news coverage: log file, what it shows, page URL, image URL, published credit ("NVCC"/"FBNV" = supplied by the subject) in `assets/SOURCES.md`; no logins, nothing under ~1000 px unless nothing else exists. Check each at full size: sponsor walls, unrelated brand props, slogans owned by others, uniforms and insignia, sensitive screens — crop, defocus, flag or drop.
- **Chat-app photos:** when the owner points at a group chat, read only the shared-media panel (never messages), and if you automate a desktop app, check the frontmost app before every synthetic key, never post keys to a background app, warn that the clipboard was used, and give focus back.
- **Plates:** Wikimedia Commons (CC BY: record the credit to publish), NASA imagery (public domain). Stock video (Pexels/Pixabay): check what each clip actually shows (a clip labelled with one city showed another; a "police" clip a foreign police car; a control room showed a real foreign channel and politicians), no watermarks, no visible brands.
- **DRM-protected sources** (e.g. HLS with an AES key server) are off-limits; their public poster frames are fine.
- **Logos:** only the organisation's own files (site SVG/PNG, official social accounts); keep provenance in `assets/research/`. Never redraw, retype or recolour (reviewers suggest monochrome logos — refuse). If no flat file exists, matte it from the organiser's own key visual (estimate the ground, derive alpha from the channel where the mark differs most, keep the main connected region, un-premultiply, check on dark/brand/white backgrounds) and show it no larger than its native size. A pillar without a partner gets a visual, not an invented logo.
- **Generated images** (GPT Image via `tools/imagegen.mjs`): abstract plates without people, insignia or text, ARRI-look prompts, upscaled (Real-ESRGAN) and checked at 100%; never for a real organisation's people or events without consent.

## 6. Writing the narration

- Write it as one spoken piece and read it aloud top to bottom before recording. Every chapter opens by linking to the one before. Lists live inside sentences. Name lists close with a line that carries meaning. Numbers are written the way they are spoken in that language (and the TTS notes say how to read years and figures).
- Keep sentences speakable: one idea each, the key word near the end where the voice lands.
- Calibrate to the evidence (see §3); prefer warm, plain verbs ("connects with", "helps stop") to technical claims.
- Fit the slots: measure each recorded line; if a chapter runs long, cut words and re-record — never speed up the read.
- Have every language's copy read by a strict native editor (a model asked to act as a senior copy editor in that language caught calques, the wrong register of a near-synonym, repeated words, official capitalisation); the owner is the final ear ("the master language matters most").
- Product films without narration: one short line per beat on screen, held ≥ 2 s, sized to fit in every language.

### Structures that worked

- **Brand film:** the problem in the audience's life (a message, a link, a call) → the origin and the promise → what they built (each tool demoed problem → fix) → a participatory element (a game) → the people → the community → the partners → the journey recognised (awards rail with real photos) → a finale that returns to the opening image, transformed, with the one-line belief.
- **Event opener:** the scale of the world (data, light) → the opportunity → the double edge (threats) → why it matters for THIS audience → the three pillars → the call (three stop-time slogans) → the partners → the official emblem and the event title, landing on the music's final phrase.
- **Product showcase:** a hook that states the stake ("Threats never sleep.") → the brand answers → the core modules, each one idea with its own visual concept → the moment of attribution or proof → the centrepiece capability → the AI/answer climax → the wordmark, tagline, URL.

## 7. Bilingual films

- Each language is written natively; the picture is shared, but each language's narration times its own beats (`en` overrides in the timeline/cues) and, when one read is shorter, its own scene timing.
- English narration must not say local names it can't pronounce (respelling helped little); show the names on screen and introduce people by role. Allowed exceptions are decided by the owner (the organisation's name and the founder).
- All on-screen text in `src/film/script.ts` for every language; translations run longer — fit every single-line title per language and check every frame of every language.

## 8. The storyboard

`docs/storyboard.md`, one row per beat: time · picture (the one idea, the hero moment, how it enters and leaves) · narration · sound · notes. Write it before building and keep it current; parallel builders work from it. Include for each chapter the element that hands over to the next.

## 9. Fact-check rounds during feedback

"Please fact check all the things before you make any change": when feedback adds claims (a new capability, a new person, a new award), check them first. A background subagent with a numbered brief (part A: the client's new wording; part B: re-check every existing claim) writes verdicts (Supported / Partly / Not supported / Contradicted), 1–3 dated sources and safe wording per language into `docs/factcheck-<round>.md`. Report what you corrected and why, what the client must confirm, and anything you added beyond the request (with an offer to revert).
