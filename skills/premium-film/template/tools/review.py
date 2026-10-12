#!/usr/bin/env python3
"""An independent pair of eyes and ears: asks the newest Gemini Flash about rendered media and prints the answer.
  review.py <prompt-file or "text"> <media...>
Media: .mp4/.mov (video), .wav/.mp3 (audio), .png/.jpg (images), attached in order, each labelled with its file name
(name frames by their film time, e.g. t012.5.jpg, so the answer can cite times).

Routes (REVIEW_VIA): "openrouter" (preferred when OPENROUTER_API_KEY is set; prints the cost; video needs ≥ $1 left
on the key, else send frames + mp3) or "gemini" (GEMINI_API_KEY, free tier fine; media over 18 MB go through the Files
API and are deleted afterwards). The model is the review pick in .providers.json (tools/providers.py finds the newest
Gemini Flash that takes video and audio); REVIEW_MODEL overrides it, REVIEW_MODELS (comma list) adds fallbacks on the
direct API.
Env: FPS (video frames sampled per second, direct API), MEDIA_RES (LOW|MEDIUM|HIGH), TEMP (default 0.4),
REVIEW_TRIES (tries per model, default 2). Every request is printed; under a strict budget pin one model in
REVIEW_MODELS and set REVIEW_TRIES=1.

Cheapest useful media (tools/excerpt.sh makes them): the whole film at 640 px, 24 fps, crf 32 (≈5 MB for 3 min);
or a stretch as frames every 0.5 s plus its audio as mp3.

How far to trust it (learned over four films):
  - USEFUL: concrete, checkable flags — a misspelt or mis-said word, a clipped word at a cut, a glitch at a time, a
    name read wrongly, text cut off, a harsh sound, sync between a word and a picture beat. Verify each on frames.
  - UNRELIABLE: A/B preferences (pure position bias: the second clip listed wins), subtle voice identity, small text
    at low resolution, music "jumps" that aren't there, motion between its ~1 fps samples ("hard cut" on a smooth
    move), and its own taste (it asked for faster typing the owner had rejected). Never let it override the owner.
  - Ask for problems with timestamps, "only report real problems; say none if none", "do not praise", and (for any
    agentic CLI) "do not run any tools". Run blind comparisons twice with the order swapped."""
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from envkeys import key  # noqa: E402

prompt = sys.argv[1]
if os.path.exists(prompt):
    prompt = open(prompt, encoding="utf-8").read()
files = sys.argv[2:]
_pick_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".providers.json")
pick = (json.load(open(_pick_path)).get("review") or {}) if os.path.exists(_pick_path) else {}
via = os.environ.get("REVIEW_VIA") or pick.get("via") or ("openrouter" if key("OPENROUTER_API_KEY") else "gemini")
mimetypes.add_type("audio/wav", ".wav")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("video/mp4", ".mp4")


def call(url, data=None, headers=None, method=None, timeout=900):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers


if via == "openrouter":
    model = os.environ.get("REVIEW_MODEL") or (pick.get("model") if pick.get("via") == "openrouter" else None)
    if not model:
        sys.exit("no review model: run tools/providers.py (or set REVIEW_MODEL, e.g. the newest google/gemini-*-flash)")
    parts = [{"type": "text", "text": prompt}]
    for f in files:
        ext = f.rsplit(".", 1)[-1].lower()
        b64 = base64.b64encode(open(f, "rb").read()).decode()
        parts.append({"type": "text", "text": f"[{os.path.basename(f)}]"})
        if ext in ("wav", "mp3"):
            parts.append({"type": "input_audio", "input_audio": {"data": b64, "format": ext}})
        elif ext in ("mp4", "mov"):
            parts.append({"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64}"}})
        else:
            parts.append({"type": "image_url", "image_url": {"url": f"data:image/{'jpeg' if ext == 'jpg' else ext};base64,{b64}"}})
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": parts}], "usage": {"include": True}, "temperature": float(os.environ.get("TEMP", "0.4"))}).encode()
    for attempt in range(4):
        try:
            out, _ = call("https://openrouter.ai/api/v1/chat/completions", body, {"Content-Type": "application/json", "Authorization": f"Bearer {key('OPENROUTER_API_KEY')}"})
            d = json.loads(out)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            print("HTTP", e.code, msg, file=sys.stderr)
            if e.code == 402:
                print("(OpenRouter refuses video when the key has < $1 left: send frames + an mp3 instead)", file=sys.stderr)
            if e.code in (429, 500, 502, 503):
                time.sleep(15 * (attempt + 1))
                continue
            sys.exit(1)
    else:
        sys.exit(1)
    print(d["choices"][0]["message"]["content"])
    u = d.get("usage", {})
    print(f"\n[{model}: {u.get('prompt_tokens')} in, {u.get('completion_tokens')} out, ${u.get('cost', 0):.4f}]", file=sys.stderr)
    sys.exit(0)

# ---- direct Gemini API
K = key("GEMINI_API_KEY")
BASE = "https://generativelanguage.googleapis.com"
models = [m for m in [os.environ.get("REVIEW_MODEL") or (pick.get("model") if pick.get("via") == "gemini" else None)]
          + os.environ.get("REVIEW_MODELS", "").split(",") if m]
if not models:
    sys.exit("no review model: run tools/providers.py (or set REVIEW_MODEL to the newest gemini-*-flash)")


def upload(path, mime):
    size = os.path.getsize(path)
    _, h = call(f"{BASE}/upload/v1beta/files", json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
                {"x-goog-api-key": K, "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(size), "X-Goog-Upload-Header-Content-Type": mime, "Content-Type": "application/json"})
    body, _ = call(h["X-Goog-Upload-URL"], open(path, "rb").read(), {"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize", "Content-Length": str(size)}, timeout=1800)
    f = json.loads(body)["file"]
    while f.get("state") == "PROCESSING":
        time.sleep(4)
        f = json.loads(call(f"{BASE}/v1beta/{f['name']}", headers={"x-goog-api-key": K})[0])
    return f


parts, uploaded = [], []
try:
    for p in files:
        mime = mimetypes.guess_type(p)[0] or "application/octet-stream"
        parts.append({"text": f"[file: {os.path.basename(p)}]"})
        if os.path.getsize(p) > 18_000_000:
            f = upload(p, mime)
            uploaded.append(f["name"])
            part = {"fileData": {"mimeType": mime, "fileUri": f["uri"]}}
        else:
            part = {"inlineData": {"mimeType": mime, "data": base64.b64encode(open(p, "rb").read()).decode()}}
        if mime.startswith("video/") and os.environ.get("FPS"):
            part["videoMetadata"] = {"fps": float(os.environ["FPS"])}
        parts.append(part)
    parts.append({"text": prompt})
    gen = {"temperature": float(os.environ.get("TEMP", "0.4"))}
    if os.environ.get("MEDIA_RES"):
        gen["mediaResolution"] = f"MEDIA_RESOLUTION_{os.environ['MEDIA_RES'].upper()}"
    body = json.dumps({"contents": [{"parts": parts}], "generationConfig": gen}).encode()
    sent = 0
    for m in models:
        for attempt in range(int(os.environ.get("REVIEW_TRIES", "2"))):  # "high demand" 503s come and go
            sent += 1
            print(f"[request {sent}: {m}]", file=sys.stderr)  # every request counts against the day's quota
            try:
                out, _ = call(f"{BASE}/v1beta/models/{m}:generateContent", body, {"x-goog-api-key": K, "Content-Type": "application/json"})
                d = json.loads(out)
                txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"] if not p.get("thought"))
                u = d.get("usageMetadata", {})
                print(txt)
                print(f"\n[{m}: {u.get('promptTokenCount')} tokens in]", file=sys.stderr)
                sys.exit(0)
            except urllib.error.HTTPError as e:
                msg = e.read().decode()[:200].replace("\n", " ")
                print(f"[{m}] HTTP {e.code} {msg}", file=sys.stderr)
                if e.code == 503 or (e.code == 429 and "PerDay" not in msg and attempt < 1):
                    time.sleep(10)
                    continue
                break
    sys.exit(1)
finally:
    for n in uploaded:
        try:
            call(f"{BASE}/v1beta/{n}", headers={"x-goog-api-key": K}, method="DELETE")
        except Exception:
            pass
