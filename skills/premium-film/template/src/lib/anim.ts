import React, { createContext, useContext } from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { EASE } from "../theme";

type EaseFn = (t: number) => number;

// Every scene is mounted a little before its nominal start (PRE) so neighbours can overlap for camera and light
// transitions. The clock offset keeps each scene's own timeline anchored to its nominal start: useTime() is the
// number of seconds since the scene started (negative during the pre-roll). A voice version (another narrator,
// re-timed by tools/voice_warp.py) also passes a warp, so a moment of the new cut shows what the original showed
// for the same words.
type Clock = { offset: number; warp?: { from: number; start: number; toOld: (t: number) => number } };
const ClockContext = createContext<Clock>({ offset: 0 });

export const SceneClock: React.FC<{ offset: number; warp?: Clock["warp"]; children: React.ReactNode }> = ({ offset, warp, children }) =>
  React.createElement(ClockContext.Provider, { value: { offset, warp } }, children);

/** Seconds since the current scene's nominal start (negative during its pre-roll). */
export const useTime = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { offset, warp } = useContext(ClockContext);
  return warp ? warp.toOld(warp.from + frame / fps) - warp.start : frame / fps - offset;
};

/** 0 → 1 between t0 and t1 (seconds), clamped, eased. The workhorse of every animation. */
export const ramp = (t: number, t0: number, t1: number, ease: EaseFn = EASE.out) =>
  interpolate(t, [t0, t1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });

export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** Deterministic pseudo-random generator (mulberry32). Never use Math.random(): every frame must be reproducible. */
export const rng = (seed: number) => {
  let s = seed >>> 0;
  return () => {
    s += 0x6d2b79f5;
    let r = Math.imul(s ^ (s >>> 15), 1 | s);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
};

/** Stable hash-based random in [0, 1) for an integer key. */
export const hash01 = (n: number) => {
  let x = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b);
  x ^= x >>> 13;
  x = Math.imul(x, 0xc2b2ae35);
  x ^= x >>> 16;
  return (x >>> 0) / 4294967296;
};

/**
 * Smooth path through keyframes (monotone cubic Hermite, Fritsch–Carlson): no overshoot and no velocity jumps,
 * unlike chained eased segments. Use it for camera moves that pass through several poses.
 */
export const smoothPath = (t: number, times: number[], values: number[]) => {
  const n = times.length;
  if (t <= times[0]) return values[0];
  if (t >= times[n - 1]) return values[n - 1];
  const d: number[] = [];
  for (let i = 0; i < n - 1; i++) d.push((values[i + 1] - values[i]) / (times[i + 1] - times[i]));
  const m: number[] = [d[0]];
  for (let i = 1; i < n - 1; i++) m.push(d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2);
  m.push(d[n - 2]);
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) {
      m[i] = 0;
      m[i + 1] = 0;
      continue;
    }
    const a = m[i] / d[i];
    const b = m[i + 1] / d[i];
    const s = a * a + b * b;
    if (s > 9) {
      const k = 3 / Math.sqrt(s);
      m[i] = k * a * d[i];
      m[i + 1] = k * b * d[i];
    }
  }
  let i = 0;
  while (t > times[i + 1]) i++;
  const h = times[i + 1] - times[i];
  const u = (t - times[i]) / h;
  const h00 = 2 * u * u * u - 3 * u * u + 1;
  const h10 = u * u * u - 2 * u * u + u;
  const h01 = -2 * u * u * u + 3 * u * u;
  const h11 = u * u * u - u * u;
  return h00 * values[i] + h10 * h * m[i] + h01 * values[i + 1] + h11 * h * m[i + 1];
};

/** A hit's envelope: a 3–4 frame attack, then an exponential decay. An instant attack reads as a glitch. */
export const hitEnv = (t: number, at: number, decay = 0.35, attack = 0.06) => {
  if (t < at) return 0;
  const u = t - at;
  return clamp01(u / attack) * Math.exp(-Math.max(0, u - attack) / decay);
};
