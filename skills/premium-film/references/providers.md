# Services, keys and models

Every AI service is optional. The best result comes from the best tools the person has, so find out what they have before the first take, image or review, and use the newest premium model for each job.

## Contents
1. Ask once, at the start
2. What each job uses, with fallbacks
3. Choosing models
4. Money and quotas
5. Service quirks

---

## 1. Ask once, at the start

Run `tools/setup.sh` (it ends with `tools/providers.py`): it checks every key in `.env` without printing it, asks each service which models it offers today, picks the best per job and writes `.providers.json`, which the tools read. Then, if something that would raise the quality is missing, ask the person once, in one message, for example:

> To make this film as good as possible I can use: an OpenRouter key (preferred — one key gives the newest Gemini for reviewing picture and sound, ElevenLabs and Gemini voices, and GPT Image 2 for images), a Gemini API key (a free one is enough for narration and reviews), an ElevenLabs key (for your own or cloned voices), and the Codex CLI signed in to ChatGPT (images without API cost). Which of these do you have, and is there a budget for paid calls? Put any keys in the project's `.env`; I never print them.

Don't block on the answer: start research, script and design meanwhile. Re-run `tools/providers.py` after keys are added.

## 2. What each job uses, with fallbacks

| Job | Best | Fallbacks | With nothing |
|---|---|---|---|
| Independent review of picture and sound | newest Gemini Flash that takes video and audio, via OpenRouter | the same through the Gemini API (free tier) | the automatic scans, sheets, strips and loudness checks alone |
| Narration | audition ElevenLabs' newest model and Gemini TTS via OpenRouter; pick by ear | an ElevenLabs key directly; the Gemini API free tier | a film carried by designed on-screen type |
| Generated images (plates, assets, widening a real photo) | GPT Image 2 family, quality variant, via OpenRouter | the Codex CLI's image tool on a ChatGPT plan | real photos and designed motion only (the films that won needed none) |
| Music, sound design, mix | composed in code (always available) | a licensed track the owner supplies, cut on its bar grid | — |
| Captions, cutting, checks, release | local tools in Docker (always available) | — | — |

Respect the owner's routing rules when they set them (for example "this key only for Gemini") and their budget.

## 3. Choosing models

- Trust `tools/providers.py` over any model name written in these docs: lists change every few months. It ranks the newest family first and the quality variant before speed or cheap variants (lite, turbo, flash, mini, "flare").
- Narration: audition, don't assume ([narration.md](narration.md) §1). Then lock one voice and one model per language for the film and write the exact choice in the README.
- Images: the quality variant of the newest GPT Image (`IMAGE_MODEL` pins another one, e.g. `openai/gpt-image-2`). Show one sample before a set.
- Review: the newest Gemini Flash with video and audio input; pin it for the whole round so scores compare.

## 4. Money and quotas

- Free first, then paid only with the owner's yes and a number. Report spend in each round's report (the tools print each request and, on OpenRouter, its cost).
- OpenRouter: set a spend limit on the key; `tools/providers.py` shows what is left. Video input is refused when under ~$1 is left: review a stretch as frames every 0.5 s plus its mp3 (`tools/excerpt.sh <video> <from> <to>`). Costs seen: a narration batch take ≈ $0.01–0.03, a whole-film review at 640 px ≈ $0.03, a frames+audio review ≈ $0.05; images cost much more per call, so agree a number first.
- Gemini API free tier: about 10 voice requests per model per day per Google project (shared by every project using it; a probe counts). Batch lines; schedule the rest after the reset rather than switching models.
- ElevenLabs: a monthly character allowance (`tools/providers.py` shows usage).
- Never rent machines or buy anything to go faster without asking (a cloud rental "to render faster" cost money, produced nothing and angered the owner).

## 5. Service quirks

- OpenRouter's speech API reads `input` aloud: notes go in `instructions` (done by `tools/tts.py`; `TTS_NOTES=inline` for a model that ignores them). Always word-check takes with `tools/cut_lines.py`: some models have read a note aloud on some routes.
- Gemini TTS through the Gemini API takes the whole prompt (profile, scene, notes, transcript) as text.
- ElevenLabs: send only the transcript, with the language code; check the chosen model supports the film's languages (`tools/providers.py` only lists ElevenLabs models that speak every language in the timeline; an older "multilingual" model lacked Vietnamese).
- GPT Image through OpenRouter uses its Images API (`tools/imagegen.mjs`); the Codex route needs `codex` signed in and runs on the host.
- Keys live only in the project's git-ignored `.env` (mode 600). Never print them, never put them in docs or memory, and suggest rotating any key pasted into a chat.
