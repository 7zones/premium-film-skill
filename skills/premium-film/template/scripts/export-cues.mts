// Writes the film's timing to audio/cues.json for the soundtrack (audio/mix.py, audio/score.py, tools/*.py):
// the languages, each cut's running time and scene times, the named cue moments, the music landmarks and the narration slots.
// Run after ANY timing change:  node --experimental-strip-types scripts/export-cues.mts   (or: npm run cues)
import { readFileSync, writeFileSync } from "node:fs";
import { CUES, FPS, M, SCENE_ORDER, SCENES_OF, VO, filmLength, voAt } from "../src/film/timeline.ts";
import { LANGS } from "../src/film/script.ts";

const voices = JSON.parse(readFileSync(new URL("../src/film/voices.gen.json", import.meta.url), "utf-8"));
const out = {
  fps: FPS,
  langs: LANGS,
  duration: Object.fromEntries(LANGS.map((l) => [l, filmLength(l)])),
  order: SCENE_ORDER,
  scenes: SCENES_OF,
  cues: CUES,
  music: M,
  vo: VO.map((v) => ({ id: v.id, at: Object.fromEntries(LANGS.map((l) => [l, voAt(v, l)])), onScreen: !!v.onScreen, text: v.text })),
  voices,
};
writeFileSync(new URL("../audio/cues.json", import.meta.url), JSON.stringify(out, null, 2));
console.log(`wrote audio/cues.json: ${SCENE_ORDER.length} scenes, ${VO.length} narration lines, ${LANGS.map((l) => `${filmLength(l)} s (${l})`).join(" / ")}`);
