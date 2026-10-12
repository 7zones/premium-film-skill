// Alternative narrators ("Version 2" with another voice). The film is timed to its original narration; another
// voice says the same lines at its own pace, so a voice version re-times the WHOLE film to it instead of touching
// the narration: tools/voice_warp.py measures a smooth, monotone map from the original timeline to the new one
// (through every line's first sound and the pauses both reads share) into voices.gen.json. The picture (through the
// scene clock), the score (audio/mix.py with VOICE=…) and the captions follow it, so every beat still lands on its
// word, while the narration itself is never stretched.
import VOICES from "./voices.gen.json";
import type { Lang } from "./script";
import { filmLength } from "./timeline";

type Table = { vo: Record<string, number>; anchors: [number, number][]; duration: number };
const TABLES = VOICES as unknown as Record<string, Record<Lang, Table>>;

/** Monotone cubic (Fritsch–Carlson) through the anchors; tools/voice_warp.py and audio/mix.py use the same curve. */
const pchip = (xs: number[], ys: number[]) => {
  const n = xs.length;
  const h = xs.slice(1).map((x, k) => x - xs[k]);
  const s = h.map((hk, k) => (ys[k + 1] - ys[k]) / hk);
  const d = xs.map((_, k) => {
    if (k === 0) return s[0];
    if (k === n - 1) return s[n - 2];
    if (s[k - 1] * s[k] <= 0) return 0;
    const w1 = 2 * h[k] + h[k - 1];
    const w2 = h[k] + 2 * h[k - 1];
    return (w1 + w2) / (w1 / s[k - 1] + w2 / s[k]);
  });
  return (x: number) => {
    if (x <= xs[0]) return ys[0] + (x - xs[0]) * d[0];
    if (x >= xs[n - 1]) return ys[n - 1] + (x - xs[n - 1]) * d[n - 1];
    let lo = 0;
    let hi = n - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (xs[mid] <= x) lo = mid;
      else hi = mid;
    }
    const t = (x - xs[lo]) / h[lo];
    const t2 = t * t;
    const t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[lo] + (t3 - 2 * t2 + t) * h[lo] * d[lo] + (-2 * t3 + 3 * t2) * ys[lo + 1] + (t3 - t2) * h[lo] * d[hi];
  };
};

export type VoiceClock = { toNew: (t: number) => number; toOld: (t: number) => number; duration: number };
const clocks = new Map<string, VoiceClock>();

/** The re-timing for a voice version, or null for the original narration. */
export const voiceClock = (voice: string | undefined, lang: Lang): VoiceClock | null => {
  if (!voice) return null;
  const key = `${voice}-${lang}`;
  const hit = clocks.get(key);
  if (hit) return hit;
  const table = TABLES[voice]?.[lang];
  if (!table) throw new Error(`no narration timing for voice ${voice} (${lang}): run tools/voice_warp.py ${voice}`);
  const toNew = pchip(
    table.anchors.map((a) => a[0]),
    table.anchors.map((a) => a[1]),
  );
  const toOld = (t: number) => {
    let lo = -10;
    let hi = filmLength(lang) + 60;
    for (let i = 0; i < 48; i++) {
      const mid = (lo + hi) / 2;
      if (toNew(mid) < t) lo = mid;
      else hi = mid;
    }
    return (lo + hi) / 2;
  };
  const clock = { toNew, toOld, duration: table.duration };
  clocks.set(key, clock);
  return clock;
};

/** Running time of a cut. */
export const filmDuration = (voice: string | undefined, lang: Lang) => voiceClock(voice, lang)?.duration ?? filmLength(lang);
