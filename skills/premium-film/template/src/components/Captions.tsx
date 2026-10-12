import React, { createContext, useContext } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { ramp } from "../lib/anim";
import { C, EASE, FONT } from "../theme";
import type { Lang } from "../film/script";
import CAPTIONS from "../film/captions.gen.json";

// Burned-in subtitles for the captioned cut: the narration in the film's own type, ALWAYS one line on a
// see-through black band, low and centred. Cues come from tools/captions.py (Whisper word times, hand-picked
// phrase breaks, the same cues as the .srt). Cues that follow each other within a sentence switch in place; the
// band fades only at the ends of a run, so it never blinks between phrases.
//
// When captions are on, scenes must (1) lift anything that sits low in the frame (useCaptionLift) and (2) hide
// on-screen text that only repeats what the narrator is saying (useCaptioned) — duplicated words read as clutter.

type Cue = [number, number, string];
const GAP = 0.35;

const CaptionedContext = createContext(false);
export const CaptionedProvider = CaptionedContext.Provider;
/** True in the captioned cut. */
export const useCaptioned = () => useContext(CaptionedContext);
/** How far (px) type that sits at the bottom of the frame should move up in the captioned cut. */
export const useCaptionLift = () => (useContext(CaptionedContext) ? 64 : 0);

const runsOf = (cues: Cue[]) => {
  const out: { from: number; to: number }[] = [];
  for (const [a, b] of cues) {
    const last = out[out.length - 1];
    if (last && a - last.to < GAP) last.to = b;
    else out.push({ from: a, to: b });
  }
  return out;
};

export const CaptionTrack: React.FC<{ lang: Lang; voice?: string }> = ({ lang, voice }) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const cues = ((CAPTIONS as unknown as Record<string, Cue[]>)[voice ? `${lang}-${voice}` : lang] ?? []) as Cue[];
  const run = runsOf(cues).find((r) => t >= r.from - 0.12 && t < r.to + 0.12);
  if (!run) return null;
  const cue = [...cues].reverse().find(([a]) => t >= a - 0.12 && a >= run.from - 0.01 && a < run.to + 0.01);
  if (!cue) return null;
  const a = ramp(t, run.from - 0.12, run.from + 0.06, EASE.out) * (1 - ramp(t, run.to - 0.06, run.to + 0.12, EASE.inOut));
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 48, pointerEvents: "none" }}>
      <div
        style={{
          opacity: a,
          background: "rgba(0, 0, 0, 0.6)",
          borderRadius: 8,
          padding: "6px 24px 9px",
          fontFamily: FONT.sans,
          fontWeight: 500,
          fontSize: 40,
          lineHeight: "52px",
          letterSpacing: "0.005em",
          color: C.fg,
          whiteSpace: "nowrap",
        }}
      >
        {cue[2]}
      </div>
    </AbsoluteFill>
  );
};
