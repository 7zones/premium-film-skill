#!/usr/bin/env node
// Image generation with GPT Image 2 — through OpenRouter's Images API (OPENROUTER_API_KEY; preferred) or the Codex
// CLI's built-in image tool (a signed-in ChatGPT plan). Outputs land in assets/gen/<name>.png.
//
//   node tools/imagegen.mjs plate   <name> "<what the image shows>"        a cinematic background plate (16:9)
//   node tools/imagegen.mjs reframe <name> <photo> "<task>"                 widen a REAL photo; then
//                                                                            tools/reframe_composite.py lays the real
//                                                                            pixels back over the new canvas
//   node tools/imagegen.mjs asset   <name> <style-ref.png> "<concept>"      an illustration matching a reference sheet
//
// Service and model: IMAGE_VIA (openrouter | codex) and IMAGE_MODEL override the pick in .providers.json
// (tools/providers.py finds the newest openai/gpt-image-*). Each image costs money on OpenRouter (it prints the
// cost): agree a budget with the owner first, and show ONE sample before generating a set.
//
// When not to use it: a film about a real organisation, its people or its events. A client rejected AI stills and AI
// video three times as "too fake" (AI reviewers had rated them 8.5–9.5); real photos plus motion design won.
// Generated pixels suit abstract plates (no people, insignia or text) and extending a real photo's surroundings with
// the person kept as the original pixels. Check every result at 100% before using it.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dotenv = Object.fromEntries(
  (fs.existsSync(path.join(root, ".env")) ? fs.readFileSync(path.join(root, ".env"), "utf8") : "")
    .split("\n").map((l) => l.trim()).filter((l) => /^[A-Z_]+=./.test(l))
    .map((l) => [l.slice(0, l.indexOf("=")), l.slice(l.indexOf("=") + 1).replace(/^["']|["']$/g, "")]),
);
const env = (n) => process.env[n] || dotenv[n];
const picks = fs.existsSync(path.join(root, ".providers.json")) ? JSON.parse(fs.readFileSync(path.join(root, ".providers.json"), "utf8")).images || {} : {};
const codexBin = process.env.CODEX || ["codex", "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"]
  .find((c) => spawnSync(c, ["--version"], { stdio: "ignore" }).status === 0);

const [mode, name, a3, a4] = process.argv.slice(2);
if (!["plate", "reframe", "asset"].includes(mode) || !name) {
  console.error("usage: imagegen.mjs plate|reframe|asset <name> ...  (see the top of this file)");
  process.exit(1);
}
const outDir = path.join(root, "assets", "gen");
fs.mkdirSync(outDir, { recursive: true });
const out = path.join(outDir, `${name}.png`);

let content, refs = [], aspect = "16:9", transparent = false;
if (mode === "plate") {
  content = `PURPOSE: a background plate for a premium, cinematic film. It must look like a still frame from a high-end film shot on an ARRI Alexa with anamorphic lenses: photorealistic, natural light falloff, real materials, shallow depth of field where appropriate, subtle film grain, rich but restrained colour grade. Not illustrative, not CGI-looking, not plastic, no AI artefacts.

IMAGE: ${a3}

RULES: wide 16:9 landscape. No readable text, letters, numbers, logos, brand marks, flags, emblems, badges or insignia anywhere (screens show only abstract imagery or soft glow). No identifiable real people. No watermarks. Leave calm negative space for titles where natural. If a real place is named, match its real landmarks.`;
} else if (mode === "reframe") {
  refs = [path.resolve(a3)];
  content = `Edit the attached photograph. It is a real, unretouched photo of a real person for a documentary film, so the result must stay a faithful photograph.

TASK: ${a4}

RULES: keep the person exactly as in the photo: identical face and facial features, expression, eyes, hair, skin, build, pose, clothes and everything they hold, at the same proportions. Do not redraw, beautify, smooth, sharpen, relight, rotate or move them, and do not change their face in any way. Match the photo's light, colour, focus, depth of field and grain exactly, so the new parts are invisible. Their whole head and face must be fully inside the frame with clear headroom. No other people. No readable text anywhere: no letters, numbers, logos, banners, signs or screens with words. One wide 16:9 landscape image.`;
} else {
  refs = [path.resolve(a3)];
  aspect = "1:1";
  transparent = true;
  content = `The attached image is a style reference sheet of existing illustrations. Match that family exactly (view, depth, proportions, palette, edges) without copying any of its subjects.

CONCEPT: ${a4}

RULES: one clear dominant subject with at most two small supporting details, readable at small sizes. No text, letters, numerals, logos or watermarks. Square canvas, genuinely transparent background (real alpha, not white, not a checkerboard), subject centred and filling about 80%.`;
}

const via = process.env.IMAGE_VIA || picks.via || (env("OPENROUTER_API_KEY") ? "openrouter" : codexBin ? "codex" : null);
if (!via) {
  console.error("no image service: add OPENROUTER_API_KEY to .env (GPT Image 2) or sign in to the Codex CLI; or design without generated images");
  process.exit(1);
}

if (via === "openrouter") {
  const model = process.env.IMAGE_MODEL || (picks.via === "openrouter" && picks.model) || "openai/gpt-image-2";
  const dataUrl = (f) => `data:image/${path.extname(f).slice(1).replace("jpg", "jpeg")};base64,${fs.readFileSync(f).toString("base64")}`;
  const body = {
    model, prompt: content, n: 1, quality: "high", output_format: "png", aspect_ratio: aspect, resolution: "2K",
    ...(transparent ? { background: "transparent" } : {}),
    ...(refs.length ? { input_references: refs.map((f) => ({ type: "image_url", image_url: { url: dataUrl(f) } })) } : {}),
  };
  console.error(`request (openrouter, ${model}, ${mode})`);
  const r = await fetch("https://openrouter.ai/api/v1/images", {
    method: "POST",
    headers: { Authorization: `Bearer ${env("OPENROUTER_API_KEY")}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok || !d.data?.[0]?.b64_json) {
    console.error(`FAILED ${name}: HTTP ${r.status} ${JSON.stringify(d).slice(0, 300)}`);
    process.exit(1);
  }
  fs.writeFileSync(out, Buffer.from(d.data[0].b64_json, "base64"));
  if (d.usage?.cost != null) console.error(`cost $${Number(d.usage.cost).toFixed(3)}`);
} else if (via === "codex") {
  if (!codexBin) {
    console.error("the Codex CLI is not installed or not signed in");
    process.exit(1);
  }
  // Codex quirks: stdin must not be a terminal in the background, -i is variadic so the prompt comes on stdin ("-"),
  // and images also land in ~/.codex/generated_images/.
  const prompt = `Use your built-in image generation tool (image_gen), not a script, SVG, HTML or any code, to ${refs.length ? "work from the attached image" : "create one image"}.

${content}

OUTPUT: exactly one image at the largest size the tool allows. Copy the final image into the current directory as ${name}.png. Reply with only the saved path and the pixel dimensions.`;
  const args = ["exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", outDir, ...refs.flatMap((f) => ["-i", f]), "-o", path.join(outDir, `log-${name}.txt`), "-"];
  if (process.env.CODEX_MODEL) args.splice(1, 0, "-m", process.env.CODEX_MODEL);
  console.error(`request (codex image tool, ${mode})`);
  spawnSync(codexBin, args, { input: prompt, stdio: ["pipe", "ignore", "ignore"] });
  if (!fs.existsSync(out)) {
    console.error(`FAILED ${name} (see assets/gen/log-${name}.txt)`);
    process.exit(1);
  }
} else {
  console.error(`unknown IMAGE_VIA '${via}': use openrouter or codex`);
  process.exit(1);
}
const png = fs.readFileSync(out);
const w = png.readUInt32BE(16), h = png.readUInt32BE(20);
console.log(`${path.relative(root, out)} ${w}x${h}`);
