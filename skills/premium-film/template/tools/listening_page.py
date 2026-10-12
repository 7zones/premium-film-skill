#!/usr/bin/env python3
"""A self-contained listening page so the film's owner can pick narration takes BY EAR, each heard in context.
  docker run --rm -v "$PWD":/p -w /p film-audio python tools/listening_page.py <spec.json> <out.html>

spec.json:
{
  "title": "Narrator casting",
  "intro": "Each option plays between the film's real lines before and after it. Pick one per row.",
  "gap": 1.2,
  "groups": [
    {"name": "English · team line", "before": "audio/vo/en/a-06.wav", "after": "audio/vo/en/b-01.wav",
     "options": [
       {"id": "A", "label": "Take A", "files": ["tmp/takes/en-t1-a-07.wav"], "note": "1.2 semitones deeper than the film · very close match"},
       {"id": "B", "label": "Take B", "files": ["tmp/takes/en-t2-a-07.wav"], "note": "same pitch · close match"}]}
  ]
}
Every piece is levelled to −20 LUFS so no option wins by being louder; "before"/"after" are optional. The page embeds
the audio (mp3), plays one player at a time, remembers picks, and a "Copy my picks" button produces a line like
"My picks · English · team line: B" for the owner to paste back. Describe options in plain words (pitch in
semitones, "very close / close / fairly close"), never raw scores. Why: the owner hears drifts no model catches
(a +1.4 semitone take was "not the correct voice"), and Gemini's A/B picks are position-biased."""
import base64
import html
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

SR = 24000
spec_path, out = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path, encoding="utf-8"))
gap = float(spec.get("gap", 1.2))
meter = pyln.Meter(SR)


def load(p):
    x, sr = sf.read(p, dtype="float32", always_2d=True)
    x = x.mean(1)
    if sr != SR:
        x = np.interp(np.arange(0, len(x) / sr, 1 / SR), np.arange(len(x)) / sr, x).astype(np.float32)
    lv = meter.integrated_loudness(x) if len(x) > SR * 0.5 else -20.0
    return x * 10 ** ((-20.0 - lv) / 20)


def mp3_b64(x):
    with tempfile.TemporaryDirectory() as d:
        w, m = os.path.join(d, "a.wav"), os.path.join(d, "a.mp3")
        sf.write(w, np.clip(x, -0.98, 0.98), SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", w, "-c:a", "libmp3lame", "-b:a", "96k", m], check=True)
        return base64.b64encode(open(m, "rb").read()).decode()


sil = np.zeros(int(gap * SR), np.float32)
groups_html = []
for g in spec["groups"]:
    rows = []
    for o in g["options"]:
        parts = []
        if g.get("before"):
            parts += [load(g["before"]), sil]
        for k, f in enumerate(o["files"]):
            parts += ([np.zeros(int(0.85 * SR), np.float32)] if k else []) + [load(f)]
        if g.get("after"):
            parts += [sil, load(g["after"])]
        b64 = mp3_b64(np.concatenate(parts))
        rows.append(f"""
      <div class="row" data-group="{html.escape(g['name'])}" data-id="{html.escape(o['id'])}">
        <div class="slate">{html.escape(o['id'])}</div>
        <div class="body"><div class="label">{html.escape(o.get('label', ''))}</div><div class="note">{html.escape(o.get('note', ''))}</div>
          <audio controls preload="none" src="data:audio/mpeg;base64,{b64}"></audio></div>
        <button class="pick">Pick</button>
      </div>""")
    groups_html.append(f"""
    <section><h2>{html.escape(g['name'])}</h2>{''.join(rows)}</section>""")

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(spec.get('title', 'Listening page'))}</title>
<style>
:root {{ --bg:#f7f7f5; --card:#ffffff; --ink:#18181b; --muted:#6b6b72; --line:#e4e4e7; --accent:#0f766e; --accentSoft:#ccfbf1; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0f1012; --card:#18191c; --ink:#ececee; --muted:#9a9aa3; --line:#2a2b30; --accent:#5eead4; --accentSoft:#134e4a; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
main {{ max-width:760px; margin:0 auto; padding:32px 16px 120px; }}
h1 {{ font-size:28px; margin:0 0 6px; letter-spacing:-0.01em; }}
p.intro {{ color:var(--muted); margin:0 0 28px; }}
h2 {{ font-size:15px; text-transform:none; color:var(--muted); font-weight:600; margin:28px 0 10px; }}
.row {{ display:flex; gap:14px; align-items:center; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 14px; margin-bottom:10px; }}
.row.picked {{ border-color:var(--accent); box-shadow:0 0 0 2px var(--accentSoft); }}
.slate {{ font:700 22px/1 ui-monospace,Menlo,monospace; width:40px; text-align:center; color:var(--accent); }}
.body {{ flex:1; min-width:0; }}
.label {{ font-weight:600; }}
.note {{ color:var(--muted); font-size:14px; margin-bottom:6px; }}
audio {{ width:100%; height:36px; }}
button {{ font:600 14px/1 inherit; border:1px solid var(--line); background:var(--card); color:var(--ink); border-radius:8px; padding:10px 14px; cursor:pointer; }}
.row.picked button {{ background:var(--accent); color:var(--bg); border-color:var(--accent); }}
.bar {{ position:fixed; left:0; right:0; bottom:0; background:var(--card); border-top:1px solid var(--line); padding:12px 16px; display:flex; gap:12px; align-items:center; justify-content:center; }}
.bar span {{ color:var(--muted); font-size:14px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:60vw; }}
@media (max-width:520px) {{ .row {{ flex-wrap:wrap; }} .slate {{ width:auto; }} }}
</style></head><body><main>
<h1>{html.escape(spec.get('title', 'Listening page'))}</h1>
<p class="intro">{html.escape(spec.get('intro', 'Each option plays in context. Pick one per row, then copy your picks.'))}</p>
{''.join(groups_html)}
</main>
<div class="bar"><span id="summary">No picks yet</span><button id="copy">Copy my picks</button></div>
<script>
const KEY = "picks:" + document.title;
let picks = {{}};
try {{ picks = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{}}
const render = () => {{
  document.querySelectorAll(".row").forEach(r => r.classList.toggle("picked", picks[r.dataset.group] === r.dataset.id));
  const s = Object.entries(picks).map(([g, id]) => g + ": " + id).join(" · ");
  document.getElementById("summary").textContent = s || "No picks yet";
}};
document.querySelectorAll(".row button").forEach(b => b.addEventListener("click", () => {{
  const r = b.closest(".row"); picks[r.dataset.group] = r.dataset.id;
  try {{ localStorage.setItem(KEY, JSON.stringify(picks)); }} catch (e) {{}}
  render();
}}));
document.querySelectorAll("audio").forEach(a => a.addEventListener("play", () => document.querySelectorAll("audio").forEach(o => {{ if (o !== a) o.pause(); }})));
document.getElementById("copy").addEventListener("click", () => {{
  const text = "My picks · " + Object.entries(picks).map(([g, id]) => g + ": " + id).join(" · ");
  navigator.clipboard.writeText(text).then(() => {{ document.getElementById("copy").textContent = "Copied"; setTimeout(() => document.getElementById("copy").textContent = "Copy my picks", 1500); }});
}});
render();
</script></body></html>"""
open(out, "w", encoding="utf-8").write(page)
print(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB, {sum(len(g['options']) for g in spec['groups'])} options)")
