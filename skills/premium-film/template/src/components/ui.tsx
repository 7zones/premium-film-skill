import React from "react";
import { measureText } from "@remotion/layout-utils";
import { C, EASE, FONT, rgba } from "../theme";
import { clamp01, lerp, ramp } from "../lib/anim";

// The shared kit every designed piece is built from. Rules baked in (each one came from a rejected cut):
//  - entrances rise, sharpen out of a blur and fade in with a strong ease-out; nothing pops, nothing springs
//  - once an element has arrived it is plain (no transform or filter left on it): a resting transformed layer can
//    be drawn a pixel apart by different render tabs, which reads as a 1-px flicker
//  - containers have small radii (8–22 px); never pill-shaped labels, numbered chips or tracked-out ALL-CAPS tags
//  - text is big enough for a phone: ≥ 24 px for labels, 40–90 px for lines, 120 px+ for hero numbers

/** The surface designed components sit on: smoked glass, a rim lit from above, an optional accent on the rim. */
export const Glass: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties; accent?: string; glow?: number; radius?: number }> = ({
  children,
  style,
  accent,
  glow = 0,
  radius = 18,
}) => {
  const surface = `linear-gradient(180deg, ${rgba(C.steel, 0.82)} 0%, ${rgba(C.ink, 0.92)} 100%)`;
  const rim = accent
    ? `linear-gradient(150deg, ${rgba(accent, 0.55 + 0.35 * glow)} 0%, ${rgba(accent, 0.16)} 32%, rgba(255,255,255,0.06) 66%, rgba(255,255,255,0.12) 100%)`
    : "linear-gradient(180deg, rgba(235,245,255,0.22) 0%, rgba(235,245,255,0.05) 45%, rgba(235,245,255,0.1) 100%)";
  return (
    <div
      style={{
        position: "relative",
        borderRadius: radius,
        border: "1px solid transparent",
        background: `${surface} padding-box, ${rim} border-box`,
        boxShadow: ["0 40px 100px rgba(0,0,0,0.55)", "0 12px 30px rgba(0,0,0,0.35)", "inset 0 1px 0 rgba(235,245,255,0.08)", accent && glow > 0 ? `0 0 ${90 * glow}px ${rgba(accent, 0.24 * glow)}` : ""]
          .filter(Boolean)
          .join(", "),
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** Entrance: rise, sharpen and fade in over [at, at + dur]. */
export const enter = (t: number, at: number, dur = 0.8, y = 24, blur = 10): React.CSSProperties => {
  const p = ramp(t, at, at + dur, EASE.out);
  if (p >= 1) return { opacity: 1 };
  return { opacity: clamp01(p * 1.3), transform: `translateY(${lerp(y, 0, p)}px)`, filter: `blur(${(1 - p) * blur}px)` };
};

/** Exit: drift up, soften and fade over [at, at + dur]. */
export const leave = (t: number, at: number, dur = 0.6, y = -16, blur = 10): React.CSSProperties => {
  const p = ramp(t, at, at + dur, EASE.in);
  if (p <= 0) return { opacity: 1 };
  return { opacity: 1 - p, transform: `translateY(${lerp(0, y, p)}px)`, filter: `blur(${p * blur}px)` };
};

/** An entrance at `a` and an exit at `b` (the exit wins once it starts). */
export const inOut = (t: number, a: number, b: number, opts: { dur?: number; outDur?: number; y?: number } = {}): React.CSSProperties =>
  t < b ? enter(t, a, opts.dur ?? 0.8, opts.y ?? 24) : leave(t, b, opts.outDur ?? 0.6);

export const TRACK = "-0.035em";

/** Largest size (up to `max`) at which `text` fits in `width`. Size every single-line title with it, per language. */
export const fitSize = (text: string, width: number, max: number, weight = "600", family: string = FONT.display, track = TRACK) => {
  const w = measureText({ text, fontFamily: family, fontWeight: weight, fontSize: 100, letterSpacing: track }).width;
  return Math.min(max, Math.floor((width * 100) / w));
};

/**
 * One headline line; each part rises out of its own mask, in its own colour (lead in white, accent in the brand
 * colour). The mask leaves room above and below for accents and stacked diacritics.
 */
export const TitleLine: React.FC<{
  t: number;
  at: number;
  parts: string[];
  size: number;
  colors?: string[];
  stagger?: number;
  exit?: number;
  weight?: number;
  family?: string;
  glow?: string;
  /** space between parts in em: 0.3 for words; 0 sets a one-word two-tone wordmark ("Link" + "Safe") */
  gap?: number;
}> = ({ t, at, parts, size, colors = [C.fg, C.accent], stagger = 0.16, exit = 0, weight = 600, family = FONT.display, glow, gap = 0.3 }) => (
  <div style={{ display: "flex", flexWrap: "nowrap", whiteSpace: "nowrap", justifyContent: "center" }}>
    {parts.map((part, i) => {
      const p = ramp(t, at + i * stagger, at + 1.0 + i * stagger, EASE.out);
      const moving = p < 1 || exit > 0;
      return (
        <span key={i} style={{ display: "inline-block", overflow: "hidden", fontSize: size, lineHeight: 1.12, padding: "0.2em 0.06em", margin: "-0.2em -0.06em", marginRight: i < parts.length - 1 ? `${gap - 0.06}em` : "-0.06em" }}>
          <span
            style={{
              display: "inline-block",
              fontFamily: family,
              fontWeight: weight,
              fontSize: size,
              lineHeight: 1.12,
              letterSpacing: TRACK,
              color: colors[i % colors.length],
              transform: moving ? `translateY(${lerp(115, 0, p) - exit * 26}%)` : undefined,
              opacity: clamp01(p * 1.4) * (1 - exit),
              filter: moving ? `blur(${(1 - p) * 9 + exit * 9}px)` : undefined,
              textShadow: glow ? `0 0 ${size * 0.5}px ${rgba(glow, 0.35)}` : undefined,
            }}
          >
            {part}
          </span>
        </span>
      );
    })}
  </div>
);

/** A word-by-word reveal for longer lines; "\n" breaks the line, words keep one reveal order across lines. */
export const WordReveal: React.FC<{
  t: number;
  at: number;
  text: string;
  size: number;
  color?: string;
  accent?: { words: string[]; color: string };
  perWord?: number;
  weight?: number;
  family?: string;
  exit?: number;
  maxWidth?: number;
  align?: "left" | "center";
}> = ({ t, at, text, size, color = C.fg, accent, perWord = 0.07, weight = 500, family = FONT.display, exit = 0, maxWidth, align = "center" }) => {
  let k = 0;
  const row = (words: string[], key?: number) => (
    <div key={key} style={{ display: "flex", flexWrap: "wrap", justifyContent: align === "center" ? "center" : "flex-start", maxWidth, columnGap: size * 0.26, rowGap: size * 0.06 }}>
      {words.map((w) => {
        const i = k++;
        const p = ramp(t, at + i * perWord, at + i * perWord + 0.75, EASE.out);
        const moving = p < 1 || exit > 0;
        const isAccent = accent?.words.includes(w.replace(/[.,:;!?…“”"]/g, ""));
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontFamily: family,
              fontWeight: weight,
              fontSize: size,
              lineHeight: 1.22,
              letterSpacing: "-0.02em",
              color: isAccent ? accent!.color : color,
              opacity: clamp01(p * 1.3) * (1 - exit),
              transform: moving ? `translateY(${lerp(0.35, 0, p) * size - exit * 12}px)` : undefined,
              filter: moving ? `blur(${(1 - p) * 8 + exit * 8}px)` : undefined,
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
  const lines = text.split("\n");
  if (lines.length === 1) return row(text.split(" "));
  return <div style={{ display: "flex", flexDirection: "column", alignItems: align === "center" ? "center" : "flex-start", rowGap: size * 0.06 }}>{lines.map((l, li) => row(l.split(" "), li))}</div>;
};

/** A headline as lead (white) + accent: one line when it fits `width` at a good size, otherwise two. */
export const Headline: React.FC<{ t: number; at: number; head: readonly [string, string]; width?: number; size?: number; exit?: number; accent?: string }> = ({
  t,
  at,
  head,
  width = 1500,
  size = 84,
  exit = 0,
  accent = C.accent,
}) => {
  const one = fitSize(head.join(" "), width, size);
  const two = one < size * 0.82;
  const fs = two ? Math.min(fitSize(head[0], width, size), fitSize(head[1], width, size)) : one;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      {two ? (
        <>
          <TitleLine t={t} at={at} parts={[head[0]]} size={fs} colors={[C.fg]} exit={exit} />
          <TitleLine t={t} at={at + 0.16} parts={[head[1]]} size={fs} colors={[accent]} exit={exit} />
        </>
      ) : (
        <TitleLine t={t} at={at} parts={[head[0], head[1]]} size={fs} colors={[C.fg, accent]} exit={exit} />
      )}
    </div>
  );
};

/** Splits "26.000+" / "10 triệu+" / "21M+" into a countable number and its text. */
const parseStat = (v: string) => {
  const m = v.match(/^([^\d]*)([\d.,]+)(.*)$/);
  if (!m) return null;
  const raw = m[2];
  const dotThousands = /\d\.\d{3}(\D|$)/.test(raw);
  const n = parseFloat(dotThousands ? raw.replace(/\./g, "").replace(",", ".") : raw.replace(/,/g, ""));
  return { pre: m[1], n, post: m[3], sep: dotThousands ? "." : raw.includes(",") ? "," : "" };
};
const group = (n: number, sep: string) => {
  const s = Math.round(n).toString();
  return sep ? s.replace(/\B(?=(\d{3})+(?!\d))/g, sep) : s;
};

/**
 * A hero number with its label underneath. By default it RESOLVES BY FOCUS: the final value is there from the first
 * frame, heavily blurred and slightly large, then pulls into focus (a reviewer read "157 triệu+" mid-count and the
 * film switched to this). `count` > 0 makes it count up instead, finishing while it is still blurred, for small UI
 * counters with tabular figures. Hold it sharp ≥ 1.4 s after it lands.
 */
export const BigStat: React.FC<{ t: number; at: number; value: string; label: string; size?: number; color?: string; labelSize?: number; labelWidth?: number; exit?: number; count?: number }> = ({
  t,
  at,
  value,
  label,
  size = 180,
  color = C.fg,
  labelSize = 34,
  labelWidth = 900,
  exit = 0,
  count = 0,
}) => {
  const p = ramp(t, at, at + (count > 0 ? Math.max(1.0, count + 0.25) : 0.95), EASE.out);
  const s = parseStat(value);
  let shown = value;
  if (s && count > 0 && s.n >= 10) shown = `${s.pre}${group(s.n * ramp(t, at, at + count, EASE.outSoft), s.sep)}${s.post}`;
  const lp = ramp(t, at + 0.35, at + 1.25, EASE.out);
  const moving = p < 1 || exit > 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: 1 - exit, filter: exit > 0 ? `blur(${exit * 10}px)` : undefined }}>
      <div
        style={{
          fontFamily: FONT.display,
          fontWeight: 600,
          fontSize: size,
          lineHeight: 1,
          letterSpacing: "-0.05em",
          color,
          fontVariantNumeric: "tabular-nums",
          whiteSpace: "nowrap",
          opacity: clamp01(p * 1.6),
          transform: moving ? `scale(${lerp(1.06, 1, p)})` : undefined,
          filter: p < 1 ? `blur(${(1 - p) * 18}px)` : undefined,
          textShadow: `0 0 ${size * 0.4}px ${rgba(C.accent, 0.25)}`,
        }}
      >
        {shown}
      </div>
      <div style={{ marginTop: size * 0.12, maxWidth: labelWidth, textAlign: "center", fontFamily: FONT.sans, fontWeight: 500, fontSize: labelSize, lineHeight: 1.3, color: C.fgSoft, opacity: clamp01(lp * 1.3), filter: lp < 1 ? `blur(${(1 - lp) * 6}px)` : undefined }}>
        {label}
      </div>
    </div>
  );
};
