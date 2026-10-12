# Building the film: Remotion craft

## Contents
1. Architecture of the starter project
2. Rules every scene follows
3. Motion recipes
4. Type, layout and sizes
5. Captions in the picture
6. Real 3D with React Three Fiber under Remotion
7. Photographs: grade, portraits, depth, widening
8. Generated imagery (when allowed)
9. Parallel builders (director + subagents)
10. Product-film specifics (pace knob, stage, truck)
11. Pitfalls table

---

## 1. Architecture of the starter project

```
src/film/timeline.ts   scenes (start/end), CUES (named scene-local moments, read per language with cuesOf), M (music
                       landmarks as [scene, local time]), VO (narration slots + text with " | " caption breaks,
                       onScreen, per-language atIn), per-language SCENES_OF (reshape); the single source of truth
src/film/script.ts     LANGS (the film's languages, the first is the master) and every on-screen word in each
src/film/Film.tsx      one <Sequence> per scene from start−PRE to end+POST, a SceneClock per scene, FontGate,
                       CaptionedProvider, Finish (grain+vignette), CaptionTrack, the mix (when it exists)
src/film/scenes/*.tsx  one component per chapter: reads useTime() (scene-local seconds, negative in the pre-roll)
src/film/voices.ts     the re-timing for a voice version (voices.gen.json from tools/voice_warp.py)
src/Root.tsx           Film-<lang> (one per language, 60 fps), FilmDraft (30 fps), Scenes/S-<key> (each scene alone, 30 fps), Thumb-<lang>
src/components/        ui.tsx (Glass, enter/leave, TitleLine, WordReveal, Headline, BigStat, fitSize), Atmos.tsx
                       (Dust, Rings, Spark), Captions.tsx, Grade.tsx (SVG colour grades), Finish.tsx
src/three/             kit.tsx (Bloom with NaN/HDR clamp and knee, CameraRig, StudioEnv), fx.tsx (PoseRig, project,
                       canvasTexture, Motes, Shaft, Glow, Waves, MirrorFloor, Ray), depth.tsx (DepthPlate,
                       LayeredPlate, DepthCloud)
src/lib/               anim.ts (SceneClock, useTime, ramp, lerp, rng, hash01, smoothPath, hitEnv), FontGate.tsx,
                       tex.ts (useTexture outside the canvas)
scripts/export-cues.mts → audio/cues.json (npm run cues) for every audio tool
```

`remotion.config.ts`: rspack, ANGLE OpenGL, concurrency 1. Studio: `npx remotion studio` (review each scene in the Scenes folder; switch `lang` in props).

## 2. Rules every scene follows

- **Time:** derive everything from `useTime()`; key moments come from `CUES` (and narration word times measured from the recorded lines — put them in comments next to the cue: "en at 15.2: 'Northwind' 17.16–18.0"). When one language's read differs, add a map named by its code (`de: { stat: 1.1 }`) and read the cut's language with `cuesOf(scene, lang)`.
- **Determinism:** no `Math.random()`, `Date`, or effects that depend on render order; use `rng(seed)`/`hash01(i)`. Canvases are redrawn from `t` each frame.
- **Pre-roll is transparent:** before t = 0 draw nothing opaque; fade your ground in from your own start (or as a deliberate crossfade). Post-roll: keep drawing your end state; the next scene covers you.
- **Fonts:** never measure or paint text before `FontGate` resolves (already wraps the film and each Solo scene). Canvas text: quote the family name in `ctx.font`.
- **Text in every language:** read `TEXT[lang]`; size single lines with `fitSize`; check every language the film ships in.
- **Captioned cut:** `useCaptioned()` hides text that repeats the narration; `useCaptionLift()` lifts low type; where the words ARE the picture (a slogan, the closing title), leave them and mark that narration line `onScreen: true` in the timeline so its subtitle steps aside.
- **Nothing static:** something always moves (camera drift ≥ a slow push, dust, light). Every element enters and exits. What passes the glitch scan's "dead" test: on a dark, mostly empty frame a push alone under ~1%/s reads as still (to the scan, and nearly to a viewer); pair a push of ≥ ~1%/s with a drift, particles, a breathing light or a sheen.
- **Names:** never reuse a component name across the DOM and 3D layers (a DOM `Bloom` inside a canvas crashed the render: "Div is not part of the THREE namespace").

## 3. Motion recipes

- **Entrance:** `enter(t, at, 0.8, 24, 10)` — rise 24 px, sharpen from 10 px blur, fade, strong ease-out `bezier(0.16,1,0.3,1)`. Exit: `leave(t, at, 0.6)`. Once settled, no transform/filter remains (resting transforms are drawn a pixel apart by different render tabs → flicker).
- **Headlines:** `TitleLine` — each part rises out of its own mask (115% → 0, blur 9 → 0, 1 s, 0.16 s stagger), lead white + accent colour (if the brand does two-tone; `gap={0}` for a one-word two-tone wordmark). Longer lines: `WordReveal` (each word 0.07 s apart).
- **Hero numbers:** `BigStat` resolves by focus (final value blurred 18 px and 6% large → sharp over ~1 s).
- **Hits:** `hitEnv(t, at, decay, attack=0.06)` — never an instant attack. Rings: grow + fade, a few frames of attack.
- **Camera paths:** `smoothPath(t, times, values)` (monotone cubic: no overshoot, no velocity jumps) for each axis; a long slow push under holds; small parallax drifts at different depths. For a 2D "camera", transform a wrapper (`scale`, `translate`) — and keep `mix-blend-mode: screen` layers as SIBLINGS of a transformed wrapper (a transformed parent isolates the blend; a screen-blended plate showed as a dark rectangle).
- **Typing:** ~25–30 characters/s with an uneven rhythm, a cursor, and a hold before "send"; one key-click sound per character.
- **Graphs:** draw the path with stroke-dashoffset from start to end; dim the frame behind a hero line.
- **Lists:** items one at a time ~0.35 s apart, each on its spoken word.
- **Light sweeps:** a soft band (gradient) crossing a card or wordmark once, after it lands; screen blend.
- **Light hand-offs:** a spark that flies to the next scene's anchor; a point that the incoming scene bursts from; a shared routine (exported function) that paints the identical burst at the end of one scene and the start of the next.

## 4. Type, layout and sizes (1080p)

- Display faces: the brand's own (if it covers the language) or Space Grotesk / Noto Serif Display; running text Be Vietnam Pro; data JetBrains Mono (weight 600 for small URLs on screens). All with the subsets every language of the film needs (pick other faces for scripts these don't cover).
- Minimums: labels ≥ 22–24 px, body 26–34 px, lines 40–90 px, headlines 64–110 px, hero numbers 140–190 px. Short films for social or phones: labels ≥ 28 px, body ≥ 34 px, headlines ≥ 72 px, and check every text moment at 640 px wide. LED wall in a hall: statements 100–130 px, threat words ~90 px, no thin hairlines.
- One idea per frame; generous negative space; title-safe ≥ 110 px from the edges for anything that matters (a plaque clipped at the edge showed a stray "ERPOL"); browser/app mock-ups fill ~75–80% of the frame width.
- Glass cards: `Glass` (radius 18–22 px, rim lit from above, deep soft shadows). Tags: radius ≤ 8–10 px.
- Status: coloured text + glyph (green = real/safe, red = fake/threat, gold = honours).
- A label that sits where a subtitle will be: move it up in the captioned cut (and test with a red band drawn in the subtitle zone, ~y 898–1028).

## 5. Captions in the picture

`tools/captions.py` writes `src/film/captions.gen.json`; `CaptionTrack` draws one line on an rgba(0,0,0,0.6) band (8 px radius, 40 px Be Vietnam Pro 500, ~48 px from the bottom); consecutive cues inside a sentence switch in place; the band fades only at the ends of a run. Render the captioned cut with the `captions` prop (the release does). A separate transparent caption overlay rendered opaque because of the global page background — draw captions inside the film.

## 6. Real 3D with React Three Fiber under Remotion

**Set-up:** `<ThreeCanvas width={1920} height={1080} gl={{ antialias: true, preserveDrawingBuffer: true }} camera={{ fov, near, far, position }}>`, a `PoseRig` (position/target/fov/roll from `useTime()`), `<color attach="background">`, then the set, then `<Bloom>` last.

**Building blocks in `src/three/fx.tsx`:**
- `MirrorFloor` — a true planar reflection (three's `Reflector`) with a wet blur that widens with distance, an exponential fade, grain, and horizon haze so the far floor melts into the sky colour (no hard horizon line; one once crossed a logo). Keep objects out of the reflection by putting them on layer 1 (the floor's reflection camera sees only layer 0).
- `Glow` (camera-facing additive glow; `depthTest={false}` when it would be cut by a floor), `Shaft` (volumetric light cone, NaN-safe), `Motes` (dust with depth-of-field blur), `Waves` (broadcast rings with a few frames of attack), `Ray` (a beam drawn on with a travelling pulse), `canvasTexture` (crisp type/UI inside 3D, drawn once after fonts load), `project(point, pose)` (HTML that rides on a 3D point).
- `StudioEnv` or drei `<Environment>` with `Lightformer`s: metal and glass need an environment (black otherwise). drei's `MeshTransmissionMaterial` works under Remotion for glass hearts/prisms/monoliths.

**Bloom values that worked** (strength / radius / threshold): night Earth .85/.55/.42; tunnel 1.0/.6/.3; glass core .55/.42/.95; hall with white logo plates .6/.5/1.05 (plates ≤ 0.92 brightness); `knee` 0.2–0.45 so a fading light's glow fades with it.

**Set pieces that read as premium:** a night Earth from NASA Black Marble (no borders for government clients) with arcs and broadcast rings; a fibre/data tunnel whose travel is the integral of a speed curve (accelerates smoothly; soft glints, not 0/1 digits — a reviewer called digits a cliché); a crystal heart over a mirror floor with glass screens rising around it; a prism splitting a beam onto five platforms; a turning steel blade lit cool on one edge and red on the other; a deepfake face made only of points; a library rotunda of frames; geodesic shields assembling plate by plate; glass monoliths rising out of the floor on the beat; thousands of points flying on Béziers to targets sampled from the official logo's own alpha, landing exactly under the 2D logo before it fades in.

## 7. Photographs: grade, portraits, depth, widening

- **Grade:** mount `GradeDefs` once; `filter: url(#grade-photo)` etc. Tune the tables to the palette. Real people: grade and vignette only — no glows, rims or halos.
- **Ken Burns with intent:** a slow push and drift; rack focus (blur + dim + desaturate under a veil) to hand a photo to the next element; rotate several photos with light-sweep handovers rather than one big still.
- **Portraits:** `swift tools/mac/portraits.swift <in> <out>` (Apple subject lift + face box): every face 30% of the square, hair top 12% below the edge, never cropped past the photo's bottom; then round with a thin rim. A portrait shows only while its whole circle is inside the frame.
- **Depth photos:** `tools/depth/depth.py` (Depth Anything V2 Large, film-depth image) → `DepthPlate` for small camera moves; for photos with people or objects in front, always `tools/depth/layers.py` → `LayeredPlate` (near cut-out over a LaMa-filled far layer). Keep moves small; never turn the camera while a plate is up (its edges show); use a camera fov narrower than the plate's, or crane instead of tilt; give effects in front a higher `renderOrder`. Thin structures above the near mask (an antenna) stay in the far layer and ghost — add them to the near mask and repaint the far sky.
- **Dissolving a photo:** release by depth + smooth fbm noise with a short burn edge (`DepthPlate release`), flying off as `DepthCloud` points (each lingering a random moment so a depth contour never flies as one neon line). Never by grid cells (reads as a render glitch), never a thin neon iso-line or rim.
- **Widening a real photo** (a tall photo in a wide frame cut the founder's head): `node tools/imagegen.mjs reframe` asks GPT Image to extend the canvas under strict rules, then `tools/reframe_composite.py` finds the photo inside it (SIFT + RANSAC, ≥ 30 inliers) and lays the original pixels back (Lab colour match at the seam, matched grain). The person is always the real photograph. A cut-out on a generated background was rejected — extend, don't replace.

## 8. Generated imagery (when allowed)

`node tools/imagegen.mjs plate <name> "<description>"`: cinematic plates with the newest GPT Image (via OpenRouter, or the Codex CLI on a ChatGPT plan; [providers.md](providers.md)) — ARRI look, no text, logos, insignia or real people. Generated images must meet the same premium bar as everything else: show one sample, then generate the set; check each at 100% for artefacts, warped geometry, fake-looking light and stray text, and regenerate rather than settle. For UI-style illustrations (`asset` mode): attach a style-reference sheet of the existing family, specify view/depth/palette with exact hex values, "no gradients, no outlines, transparent background", validate one image end to end, then batch; check each on light, dark and magenta backgrounds and measure palette adherence; never remap pixels to the palette (speckled edges). Composite light-on-black plates with `mix-blend-mode: screen` and a feathered mask (their blacks are not pure black).

## 9. Parallel builders (director + subagents)

For a long film, split scenes across 3–4 background builder subagents; you stay the director (integration, copy, score, finale, hand-offs). Write `docs/storyboard.md` and a builder brief first. The brief that worked contained:
- the bar and why ("the client rejected the previous cut because it pushed raw screenshots… dense, tiny, cheap") and which scenes/films to study;
- the kit and assets available; the taste rules (from quality-bar.md); determinism; transparent pre-rolls;
- file ownership: edit only your scene files and your own helper folder; request shared changes in your report;
- the scene's duration, copy keys, cue keys, an "Idea:" sentence and beat-by-beat direction tied to named cues with concrete sizes ("URL ≥ 24 px mono", "the browser window fills ~75–80% of the width", "show ONE role word at a time, 64–72 px, on its spoken word");
- deliverables: the scene, a cue sheet (`CUES` of every audible moment with a one-line comment), a short report (beats with times, changed cues, frames to check, decisions for the director);
- how to check: `npx remotion still src/index.ts S-<key> f.png --frame=<(t+PRE)*30>`, short clip renders turned into frame strips, every language, the hand-in and hand-out; "don't run tsc, lint or git"; save work early (a usage limit killed five helpers before they saved anything). Re-brief builders with `SendMessage` (they resume from their transcripts). Verify every report on frames yourself. After builders rename or delete cues, grep the audio scripts for the old names.

## 10. Product-film specifics

- **A pace knob:** write times in units (one bar = 2 units) and convert with `PACE` seconds per unit in one place; the score's tempo follows (`500000·PACE` µs per beat). Changing one number retimes picture and music together ("a bit slower" settled at 1.1 between 1.0 too fast and 1.25 too slow).
- **One continuous stage:** a persistent lit set (aurora gradients, a perspective floor with a travelling sweep, dust) that every module scene plays on; modules truck in from the right as the previous leaves left (perspective, translate, a little rotateY and blur), 0.6 s overlap.
- **Real product truth:** real labels per language from the product's i18n, real templates/endpoints/event names, real icons; claims kept within measured reality ("in seconds" rested on a measured 0.5–5 s).
- **Brand name only as text** if the owner says so ("no logo"); keep the short and long forms as constants.

## 11. Pitfalls table

| Symptom | Cause | Fix |
|---|---|---|
| Blank or stale frames in 3D | Something loaded asynchronously inside the canvas (R3F redraws only on frame changes) | Load outside (`useTexture`) and pass in; per-frame loaders call `useThree().advance()` before `continueRender` |
| Whole frame goes black for one frame | A NaN pixel (pow of a negative base under MSAA) smeared by bloom | Clamp every pow base, write squares as products; the kit's bloom zeroes NaN/Inf |
| Particles form a narrow column instead of a logo | Faded-out meshes still write depth | Unmount after dissolving, or `depthWrite: false` |
| Bloom renders black | `@react-three/postprocessing` under Remotion | The kit's `Bloom` (three's EffectComposer in a priority-1 `useFrame`) |
| A blinking horizon line | A 1–2 px HDR line near the bloom threshold | Draw it as a soft band (sharp core + wider glow) |
| A one-frame white blob on glass | A specular glint thousands of times too bright | Clamp HDR before bloom (`maxV`) |
| Reflection shows something you removed | `Reflector` clones the camera's layers | Layer 1 + force the reflection camera's mask to 1 (built into `MirrorFloor`) |
| Metal/gold renders black | No environment | `<Environment>` with lightformers, or `StudioEnv` |
| Depth photos smear "shadows" around people | Single-surface depth | Two layers (`layers.py`, `LayeredPlate`) |
| Previous scene's last beat vanished | Opaque pre-roll | Fade your ground in from your own start |
| Labels/cursor jitter between frames | Text measured before fonts loaded in some tabs | `FontGate` around everything |
| Title jumps a pixel every few frames | Several render tabs drawing text differently | Concurrency 1; no resting transforms |
| Canvas text in a serif fallback | Canvas doesn't redraw when the font arrives | Wait for the FontFace (FontGate), quote the family in `ctx.font` |
| Video textures lag | `useOffthreadVideoTexture` timing | Extract clips to JPEG sequences, one image per frame |
| Thumbnail darker than the film | A lone still skips lighting that builds over frames | Take the thumbnail from the finished video, or render the Thumb-<lang> composition |
| Upside-down canvas texture atlas | `CanvasTexture` keeps flipY | Fix the UVs or set flipY |
| Shader link error | The same uniform name declared with different types in two shaders | Rename one |
