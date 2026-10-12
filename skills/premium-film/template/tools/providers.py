#!/usr/bin/env python3
"""What this machine can use for the film, and the best current model for each job. Run it at the start of every
film (tools/setup.sh does) and again when a key changes:
  docker run --rm -e CODEX=... -v "$PWD":/p -w /p film-audio python tools/providers.py

It checks each key in .env without printing it (OPENROUTER_API_KEY, GEMINI_API_KEY, ELEVENLABS_API_KEY), asks each
service which models it offers today, and picks per job:
  review     the newest Gemini Flash that takes video and audio (independent eyes and ears on every cut)
  narration  the voice models to audition: ElevenLabs and Gemini TTS via OpenRouter (or an ElevenLabs key / the
             Gemini API directly)
  images     GPT Image 2 (the newest openai/gpt-image-*) via OpenRouter, else the Codex CLI's image tool
OpenRouter is preferred where it offers the model (one key, many models, a spend cap you can see); the Gemini API
free tier alone still covers narration and review. Everything is optional: with no key at all the film still gets
designed type, code-composed music, the automatic checks and the release — only narration and AI review are missing.
Writes .providers.json (no secrets; git-ignored), which tts.py, review.py and imagegen.mjs read for their defaults.
Model lists change every few months: trust this output over any model name written in the docs."""
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envkeys import ROOT, key  # noqa: E402


cues_path = os.path.join(ROOT, "audio", "cues.json")
FILM_LANGS = json.load(open(cues_path, encoding="utf-8"))["langs"] if os.path.exists(cues_path) else ["en"]


def get(url, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:160]}"}
    except Exception as e:  # offline, DNS, timeout
        return {"_error": str(e)[:160]}


def version(model_id):
    """Sort key: newest family first (gemini-3.8 > 3.1; eleven_v4 > v3), full models before lite/turbo/preview."""
    m = re.search(r"(?:gemini-|[_-]v|image-)(\d+(?:\.\d+)?)", model_id)
    v = float(m.group(1)) if m else 0.0
    # quality variants first: speed/cheap variants (lite, turbo, flash-v, mini, "flare") and previews rank lower
    penalty = sum(w in model_id for w in ("lite", "turbo", "preview", "exp", "conversational", "flash-v", "flash_v", "mini", "flare"))
    return (v, -penalty)


picks = {"review": None, "narration": [], "images": None, "notes": []}
lines = []
OR, GM, EL = key("OPENROUTER_API_KEY"), key("GEMINI_API_KEY"), key("ELEVENLABS_API_KEY")

# ---- OpenRouter
if OR:
    k = get("https://openrouter.ai/api/v1/key", {"Authorization": f"Bearer {OR}"})
    if "_error" in k:
        lines.append(f"OpenRouter key: NOT working ({k['_error']})")
        OR = None
    else:
        d = k.get("data", {})
        left = d.get("limit_remaining")
        lines.append(f"OpenRouter key: works; spent ${d.get('usage', 0):.2f}" + (f", ${left:.2f} left of its limit" if left is not None else ", no spend limit set"))
        if left is not None and left < 1:
            picks["notes"].append("OpenRouter refuses video input with under $1 left: review with frames + mp3 (tools/excerpt.sh <video> <from> <to>)")
        models = get("https://openrouter.ai/api/v1/models").get("data", [])
        arch = lambda m, k: m.get("architecture", {}).get(k, [])
        rev = [m["id"] for m in models if m["id"].startswith("google/gemini") and "flash" in m["id"] and "video" in arch(m, "input_modalities")
               and "image" not in m["id"] and "tts" not in m["id"]]
        speech = get("https://openrouter.ai/api/v1/models?output_modalities=speech").get("data", [])
        voices = {m["id"]: len(m.get("supported_voices") or []) for m in speech}
        el = sorted([i for i in voices if i.startswith("elevenlabs/")], key=version, reverse=True)
        gtts = sorted([i for i in voices if i.startswith("google/") and "tts" in i], key=version, reverse=True)
        tts = el[:1] + gtts[:3]
        imgs = [m["id"] for m in models if m["id"].startswith("openai/gpt-image")]
        if not imgs:
            im = get("https://openrouter.ai/api/v1/images/models").get("data", [])
            imgs = [m.get("id", "") for m in im if str(m.get("id", "")).startswith("openai/gpt-image")]
        if rev:
            best = sorted(rev, key=version, reverse=True)[0]
            picks["review"] = {"via": "openrouter", "model": best}
        for t in tts:
            picks["narration"].append({"via": "openrouter", "model": t})
        if len(voices) > len(tts):
            picks["notes"].append(f"OpenRouter has {len(voices)} voice models in all (MiniMax, Microsoft, Fish Audio…); "
                                  "tools/tts.py --voices <model> lists a model's voices")
        if imgs:
            picks["images"] = {"via": "openrouter", "model": sorted(imgs, key=version, reverse=True)[0]}
else:
    lines.append("OpenRouter key: none (preferred: one key reaches Gemini review/TTS and GPT Image 2 with a visible spend cap)")

# ---- Gemini API (free tier works)
if GM:
    g = get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000", {"x-goog-api-key": GM})
    if "_error" in g:
        lines.append(f"Gemini key: NOT working ({g['_error']})")
    else:
        names = [m["name"].split("/")[-1] for m in g.get("models", [])]
        lines.append("Gemini key: works (free tier ≈ 10 TTS requests per model per day, shared by every project on that Google project)")
        rev = [n for n in names if "flash" in n and not re.search(r"tts|image|live|embed|audio|thinking", n)]
        tts = [n for n in names if "tts" in n]
        if rev and not picks["review"]:
            picks["review"] = {"via": "gemini", "model": sorted(rev, key=version, reverse=True)[0]}
        if not any(n["via"] == "openrouter" and "gemini" in n["model"] for n in picks["narration"]):
            for t in sorted(tts, key=version, reverse=True)[:3]:
                picks["narration"].append({"via": "gemini", "model": t})
else:
    lines.append("Gemini key: none (a free key from aistudio.google.com covers narration and review)")

# ---- ElevenLabs (optional narration)
if EL:
    sub = get("https://api.elevenlabs.io/v1/user/subscription", {"xi-api-key": EL})
    ms = get("https://api.elevenlabs.io/v1/models", {"xi-api-key": EL})
    if isinstance(ms, dict) and "_error" in ms:
        lines.append(f"ElevenLabs key: NOT working ({ms['_error']})")
    else:
        if "_error" not in sub:
            lines.append(f"ElevenLabs key: works; {sub.get('character_count', 0):,} of {sub.get('character_limit', 0):,} characters used this period")
        else:
            lines.append("ElevenLabs key: works")
        ok = []
        for m in ms if isinstance(ms, list) else []:  # only models that speak every language the film ships in
            langs = {l.get("language_id", "") for l in m.get("languages", [])}
            if m.get("can_do_text_to_speech") and all(l in langs for l in FILM_LANGS):
                ok.append(m["model_id"])
        for t in sorted(ok, key=version, reverse=True)[:2]:
            picks["narration"].insert(0, {"via": "elevenlabs", "model": t})
        picks["notes"].append("ElevenLabs voices: tools/tts.py --voices (pick by audition; the voice id goes in the README)")
else:
    lines.append("ElevenLabs key: none (optional: more voices to audition)")

# ---- Codex (images through a signed-in ChatGPT plan; setup.sh passes its path in)
codex = os.environ.get("CODEX", "")
lines.append("Codex CLI: " + ("found (image generation through the signed-in ChatGPT plan)" if codex else "not found"))
if not picks["images"] and codex:
    picks["images"] = {"via": "codex", "model": "image_gen"}

# ---- report
print("\n".join(lines))
print("\nBest available per job:")
r = picks["review"]
print(f"  review     {r['model']} via {r['via']}" if r else "  review     none: rely on the automatic checks and your own frame/audio checks")
if picks["narration"]:
    print("  narration  audition: " + "; ".join(f"{n['model']} via {n['via']}" for n in picks["narration"][:4]))
else:
    print("  narration  none: design the film for on-screen text (or ask for a Gemini key — the free tier is enough)")
i = picks["images"]
print(f"  images     {i['model']} via {i['via']}" if i else "  images     none: real photos and designed motion only (the films that won did not need generated images)")
for n in picks["notes"]:
    print("  note:", n)
json.dump(picks, open(os.path.join(ROOT, ".providers.json"), "w"), indent=1)
print("\nwrote .providers.json")
