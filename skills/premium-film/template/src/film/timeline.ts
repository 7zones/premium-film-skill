// The single source of truth for the film's timing (seconds). Scenes read these numbers, and
// scripts/export-cues.mts hands the very same numbers to the soundtrack (audio/cues.json → audio/mix.py), so
// picture, narration, music and sound effects stay locked together. Change timing HERE, never by nudging a scene.
import { LANGS, MASTER, type Lang } from "./script.ts"; // with the extension: npm run cues runs this file in Node

export const FPS = 60;

// EXAMPLE STRUCTURE — replace with the film's own chapters.
export const SCENES = {
  opening: { start: 0, end: 7.5 },
  proof: { start: 7.5, end: 14 },
  closing: { start: 14, end: 20 },
} as const;
export type SceneKey = keyof typeof SCENES;
export const SCENE_ORDER: SceneKey[] = ["opening", "proof", "closing"];
type Scenes = Record<SceneKey, { start: number; end: number }>;

/** A copy of `base` whose scene `scene` is `by` seconds longer (negative: shorter), every later scene moved with it. */
export const reshape = (base: Scenes, scene: SceneKey, by: number): Scenes => {
  const i = SCENE_ORDER.indexOf(scene);
  return Object.fromEntries(
    SCENE_ORDER.map((k, j) => [k, j < i ? base[k] : j === i ? { start: base[k].start, end: base[k].end + by } : { start: base[k].start + by, end: base[k].end + by }]),
  ) as Scenes;
};

/**
 * Each language's cut. Identical by default; when one language's narration is shorter (English often is), give
 * that cut its own, shorter scenes rather than leaving the other language's dead air in it — trim the scene that
 * holds the shorter lines and move every later scene by the same amount, e.g. `{ ...SAME, de: reshape(SCENES, "proof", 1.2) }`.
 */
const SAME = Object.fromEntries(LANGS.map((l) => [l, SCENES])) as Record<Lang, Scenes>;
export const SCENES_OF: Record<Lang, Scenes> = SAME;
export const filmLength = (lang: Lang) => SCENES_OF[lang][SCENE_ORDER[SCENE_ORDER.length - 1]].end;

/** Scenes mount PRE seconds early and stay POST seconds late, so neighbours can overlap for camera/light moves. */
export const PRE = 1.0;
export const POST = 1.0;

/**
 * Named moments inside each scene (scene-local seconds). Scenes animate from them (`cuesOf(scene, lang)`) and the
 * sound design hits on them (audio/sound.py), so a moved cue moves its whoosh/boom too. For moments that follow one
 * language's read, add an override map named by its code inside the scene: `proof: { card: 0.3, stat: 0.8, de: { stat: 1.1 } }`.
 */
export const CUES = {
  opening: { ignite: 0.9, title: 2.0, out: 6.5 },
  proof: { card: 0.3, stat: 0.8, line: 2.6, out: 5.6 },
  closing: { mark: 0.5, tagline: 1.9, url: 2.9 },
} as const;

/** One scene's cue moments in one language's cut (that language's map overrides the shared values). */
export const cuesOf = <K extends SceneKey>(scene: K, lang: Lang) => {
  const base = CUES[scene] as Record<string, unknown>;
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(base)) if (typeof v === "number") out[k] = v;
  return { ...out, ...((base[lang] ?? {}) as Record<string, number>) } as Record<Exclude<keyof (typeof CUES)[K], Lang>, number>;
};

/**
 * Music landmarks: the downbeats the picture's big moments sit on, as [scene, scene-local seconds], so they follow
 * each language's own scene times (and a voice version's re-timing) like every other cue.
 */
export const M: Record<string, [SceneKey, number]> = { start: ["opening", 0], lift: ["proof", 0], resolve: ["closing", 0.5] };

/**
 * Narration: audio/vo/<lang>/<id>.wav placed at `at` (global seconds; `atIn` overrides it for one language's cut).
 * Leave ~1.2–1.5 s between lines and ~1 s more at chapter turns; never squeeze or time-stretch the reads.
 * `onScreen`: the line's words ARE the picture (a slogan or title card the film shows as designed type) — the
 * captioned cut shows no subtitle for it, so the words never appear twice; the .srt still carries it.
 */
export const VO: Array<{ id: string; at: number; atIn?: Partial<Record<Lang, number>>; onScreen?: boolean; text: Record<Lang, string> }> = [
  { id: "l01", at: 1.2, text: { en: "Every day, millions of signals pass us by." } },
  { id: "l02", at: 8.2, text: { en: "We turn them into clear answers." } },
  { id: "l03", at: 14.6, onScreen: true, text: { en: "Your brand. Safe, every day." } },
];
export const voAt = (v: { at: number; atIn?: Partial<Record<Lang, number>> }, lang: Lang) => v.atIn?.[lang] ?? v.at;

/** Global time of a scene-local moment. */
export const at = (scene: SceneKey, local: number, lang: Lang = MASTER) => SCENES_OF[lang][scene].start + local;
