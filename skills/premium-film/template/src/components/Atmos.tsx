import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import { C, rgba } from "../theme";
import { clamp01, rng } from "../lib/anim";

// Atmosphere for 2D scenes, so nothing is ever a dead, static frame: drifting dust in depth, concentric rings that
// travel outward (with one bright pulse on a cue), and a point of light with a soft halo and an anamorphic streak.
// All deterministic functions of time.

/** Dust drifting upward in depth: near motes are bigger, brighter and softer. */
export const Dust: React.FC<{ t: number; seed?: number; count?: number; opacity?: number; color?: string; parallax?: [number, number] }> = ({ t, seed = 7, count = 60, opacity = 1, color = C.accentSoft, parallax = [0, 0] }) => {
  const motes = useMemo(() => {
    const r = rng(seed);
    return Array.from({ length: count }, () => ({ x: r() * 1920, y: r() * 1080, z: 0.25 + r() * 0.75, drift: 6 + r() * 14, phase: r() * Math.PI * 2, size: 1.5 + r() * 3 }));
  }, [seed, count]);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      {motes.map((m, i) => {
        const x = m.x + Math.sin(t * 0.21 + m.phase) * m.drift + parallax[0] * m.z;
        const y = ((((m.y - t * m.drift * 0.6 * m.z + parallax[1] * m.z) % 1180) + 1180) % 1180) - 50;
        const s = m.size * (0.6 + m.z);
        const blur = (1 - m.z) * 3;
        return (
          <div
            key={i}
            style={{ position: "absolute", left: x - s / 2, top: y - s / 2, width: s, height: s, borderRadius: 99, background: rgba(color, 0.35 + 0.5 * m.z), boxShadow: `0 0 ${s * 3}px ${rgba(color, 0.4 * m.z)}`, filter: blur > 0.4 ? `blur(${blur}px)` : undefined }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Concentric rings travelling outward; `pulse` (0..1) sends one bright ring through. */
export const Rings: React.FC<{ t: number; cx?: number; cy?: number; count?: number; gap?: number; r0?: number; color?: string; opacity?: number; speed?: number; pulse?: number }> = ({
  t,
  cx = 960,
  cy = 540,
  count = 18,
  gap = 70,
  r0 = 40,
  color = C.accent,
  opacity = 0.06,
  speed = 10,
  pulse,
}) => {
  const off = (t * speed) % gap;
  const rMax = r0 + count * gap;
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
      {Array.from({ length: count + 1 }, (_, i) => {
        const r = r0 + i * gap + off;
        const fade = clamp01((r - r0) / (gap * 1.5)) * clamp01((rMax - r) / (gap * 4));
        return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeOpacity={opacity * fade} strokeWidth={1.5} />;
      })}
      {pulse !== undefined && pulse > 0 && pulse < 1 ? (
        <circle cx={cx} cy={cy} r={r0 + pulse * rMax} fill="none" stroke={color} strokeOpacity={0.5 * (1 - pulse)} strokeWidth={2 + 10 * (1 - pulse)} style={{ filter: `blur(${1 + 3 * pulse}px)` }} />
      ) : null}
    </svg>
  );
};

/** A point of light with a soft halo and a thin anamorphic streak (screen-blended). */
export const Spark: React.FC<{ x: number; y: number; size?: number; intensity?: number; color?: string; streak?: number }> = ({ x, y, size = 1, intensity = 1, color = C.accent, streak = 1 }) => {
  if (intensity <= 0.001) return null;
  const halo = 220 * size;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, pointerEvents: "none", mixBlendMode: "screen" }}>
      <div style={{ position: "absolute", left: -halo, top: -halo, width: halo * 2, height: halo * 2, borderRadius: "50%", background: `radial-gradient(circle, ${rgba(color, 0.55 * intensity)} 0%, ${rgba(color, 0.16 * intensity)} 28%, transparent 66%)` }} />
      <div style={{ position: "absolute", left: -halo * 2.4 * streak, top: -1.5 * size, width: halo * 4.8 * streak, height: 3 * size, background: `linear-gradient(90deg, transparent, ${rgba(color, 0.55 * intensity)}, ${rgba("#ffffff", 0.9 * intensity)}, ${rgba(color, 0.55 * intensity)}, transparent)`, filter: `blur(${1.2 * size}px)` }} />
      <div style={{ position: "absolute", left: -10 * size, top: -10 * size, width: 20 * size, height: 20 * size, borderRadius: "50%", background: `radial-gradient(circle, rgba(255,255,255,${intensity}) 0%, ${rgba(color, 0.8 * intensity)} 45%, transparent 75%)` }} />
    </div>
  );
};
