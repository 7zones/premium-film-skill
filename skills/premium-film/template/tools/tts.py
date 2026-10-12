#!/usr/bin/env python3
"""Records one narration take:  tts.py <via>:<model> <voice> <out.wav> <prompt-file> [--lang <code>]
                                tts.py auto <voice> <out.wav> <prompt-file> [--lang ..]   (first pick in .providers.json)
                                tts.py --voices [<openrouter model>]   (a model's voices; no model: your ElevenLabs voices)
  via = openrouter (OPENROUTER_API_KEY; Gemini TTS, ElevenLabs and more, e.g. openrouter:elevenlabs/<model>)
        gemini     (GEMINI_API_KEY; the free tier works, e.g. gemini:<gemini tts model>)
        elevenlabs (ELEVENLABS_API_KEY, e.g. elevenlabs:<model_id> with a voice_id from --voices)
tools/providers.py lists the models each key reaches today; audition before choosing, then keep ONE voice and model
per language for the whole film and write the exact choice in the README (a different model of the "same" voice is
audibly a different narrator).

The prompt file (tools/vo_prompt.py) is the narrator's profile, the scene and the director's notes, then '#### TRANSCRIPT'
and the lines, one paragraph each. Record all lines of a batch in ONE request: one generation keeps one consistent
voice; separate requests drift. How each service gets it:
  gemini      the whole prompt as text (Gemini TTS follows the notes without reading them aloud)
  openrouter  the speech API reads `input` aloud, so the notes go in `instructions` and only the transcript in `input`
              (TTS_NOTES=inline sends the whole prompt as `input`, for a model that ignores `instructions`; check
              the take for notes read aloud)
  elevenlabs  only the transcript (direction comes from the chosen voice and its settings), with --lang as language_code
Always cut and word-check the take (tools/cut_lines.py): any model can read a note aloud, skip or double a phrase.
Env: TEMP (Gemini, default 1.0), TTS_TRIES (default 2: one retry after a server error or a per-minute limit; a
daily-quota error never retries), EL_STABILITY / EL_STYLE (ElevenLabs voice settings). Every request is printed:
each counts against a quota or a budget."""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envkeys import ROOT, key  # noqa: E402


def http(url, body=None, headers=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})}, method=method)
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read(), r.headers.get("Content-Type", "")


if sys.argv[1] == "--voices":
    if len(sys.argv) > 2:  # an OpenRouter model: its voice names
        raw, _ = http("https://openrouter.ai/api/v1/models?output_modalities=speech")
        m = next((m for m in json.loads(raw)["data"] if m["id"] == sys.argv[2]), None)
        print(", ".join(m.get("supported_voices") or []) if m else f"{sys.argv[2]}: not an OpenRouter voice model")
        sys.exit(0)
    raw, _ = http("https://api.elevenlabs.io/v2/voices?page_size=100", headers={"xi-api-key": key("ELEVENLABS_API_KEY")})
    for v in json.loads(raw).get("voices", []):
        lab = v.get("labels", {}) or {}
        print(f"{v['voice_id']}  {v['name'][:28]:28s}  {lab.get('gender', ''):7s} {lab.get('age', ''):12s} {lab.get('accent', ''):14s} {(v.get('description') or lab.get('description', ''))[:60]}")
    sys.exit(0)

args = [a for a in sys.argv[1:] if not a.startswith("--lang")]
lang = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--lang=")), None)
if "--lang" in sys.argv:
    lang = sys.argv[sys.argv.index("--lang") + 1]
    args = [a for a in args if a != lang]
spec, voice, out, tf = args[:4]
if spec == "auto":
    first = json.load(open(os.path.join(ROOT, ".providers.json")))["narration"][0]
    spec = f"{first['via']}:{first['model']}"
via, model = spec.split(":", 1)
text = open(tf, encoding="utf-8").read().strip()
notes, transcript = (text.split("#### TRANSCRIPT", 1) + [""])[:2] if "#### TRANSCRIPT" in text else ("", text)
notes, transcript = notes.strip(), transcript.strip()

if via == "openrouter":
    url, headers = "https://openrouter.ai/api/v1/audio/speech", {"Authorization": f"Bearer {key('OPENROUTER_API_KEY')}"}
    body = {"model": model, "voice": voice, "response_format": "pcm", "input": transcript}
    if notes and os.environ.get("TTS_NOTES") == "inline":  # for a model that ignores `instructions`: whole prompt as text
        body["input"] = text
    elif notes:
        body["instructions"] = notes
elif via == "gemini":
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": key("GEMINI_API_KEY")}
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "temperature": float(os.environ.get("TEMP", "1")),
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
elif via == "elevenlabs":
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=pcm_24000"
    headers = {"xi-api-key": key("ELEVENLABS_API_KEY")}
    body = {"text": transcript, "model_id": model,
            "voice_settings": {"stability": float(os.environ.get("EL_STABILITY", "0.5")), "similarity_boost": 0.8,
                               "style": float(os.environ.get("EL_STYLE", "0.2")), "use_speaker_boost": True}}
    if lang:
        body["language_code"] = lang
else:
    sys.exit(f"unknown service '{via}': use openrouter, gemini or elevenlabs")

for attempt in range(int(os.environ.get("TTS_TRIES", "2"))):
    print(f"request {attempt + 1} ({via}, {model}, {voice})", file=sys.stderr)
    try:
        raw, ctype = http(url, body, headers)
        break
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:400]
        print("HTTP", e.code, msg, file=sys.stderr)
        if e.code in (500, 502, 503) or (e.code == 429 and "PerDay" not in msg and "per day" not in msg.lower()):
            time.sleep(10 * (attempt + 1))
            continue
        sys.exit(1)
else:
    sys.exit(1)
rate = 24000
if via == "gemini":
    part = json.loads(raw)["candidates"][0]["content"]["parts"][0]["inlineData"]
    pcm, ctype = base64.b64decode(part["data"]), part["mimeType"]
    rate = int(ctype.split("rate=")[1].split(";")[0]) if "rate=" in ctype else 24000
else:
    pcm = raw  # 16-bit mono PCM at 24 kHz from both OpenRouter and ElevenLabs
with wave.open(out, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(pcm)
print(out, round(len(pcm) / 2 / rate, 2), "s", f"({via}, {model}, {voice})")
