import { Easing } from "remotion";
import { loadFont as loadDisplay } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadSans } from "@remotion/google-fonts/BeVietnamPro";
import { loadFont as loadSerif } from "@remotion/google-fonts/NotoSerifDisplay";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

// The film's palette. Take it from the brand itself (website CSS, logo files, report/deck), never invent it:
// a deep "void" for the ground, a few steps of dark tint for surfaces, near-white text, ONE accent family from the
// brand, and signal colours (red = threat/fake, green = real/safe, gold = honours) used sparingly.
// Replace these placeholder values per film.
export const C = {
  void: "#04080c",
  ink: "#07101a",
  deep: "#0c1a26",
  steel: "#1a2c3c",
  fg: "#f3f7fa",
  fgSoft: "#cdd9e2",
  muted: "#8a9dae",
  dim: "#526577",
  accent: "#5ee0b0",
  accentSoft: "#bff5df",
  accentDeep: "#1f9f72",
  gold: "#e3bd72",
  goldLight: "#fbe7b5",
  red: "#ff4d5a",
  green: "#3ddc97",
  amber: "#ffb547",
} as const;

export const rgba = (hex: string, a: number) => {
  const n = parseInt(hex.replace("#", ""), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
};

// Every face must cover every language the film ships in: a font without the glyphs falls back mid-word and breaks
// accents and diacritics. These cover Latin, Latin Extended and Vietnamese; for Greek, Cyrillic, CJK, Arabic, Thai…
// pick faces (and subsets) that include them. Brand display faces that are Latin-only may set the wordmark only.
const subsets: Array<"latin" | "latin-ext" | "vietnamese"> = ["latin", "latin-ext", "vietnamese"];
const display = loadDisplay("normal", { weights: ["400", "500", "600", "700"], subsets });
const sans = loadSans("normal", { weights: ["300", "400", "500", "600", "700"], subsets });
const serif = loadSerif("normal", { weights: ["400", "500", "600"], subsets });
const mono = loadMono("normal", { weights: ["400", "500", "600"], subsets });

export const FONT = { display: display.fontFamily, sans: sans.fontFamily, serif: serif.fontFamily, mono: mono.fontFamily };

/** Resolves once every face above has loaded (FontGate waits for it before anything renders). */
export const fontsLoaded = () => Promise.all([display.waitUntilDone(), sans.waitUntilDone(), serif.waitUntilDone(), mono.waitUntilDone()]);

// Smooth, premium motion: strong ease-out for entrances, gentle in-out for camera moves. No springy overshoot on UI.
export const EASE = {
  out: Easing.bezier(0.16, 1, 0.3, 1),
  outSoft: Easing.bezier(0.25, 1, 0.5, 1),
  inOut: Easing.bezier(0.65, 0, 0.35, 1),
  inOutSoft: Easing.bezier(0.45, 0, 0.25, 1),
  in: Easing.bezier(0.7, 0, 0.84, 0),
  linear: (t: number) => t,
};

export const W = 1920;
export const H = 1080;
