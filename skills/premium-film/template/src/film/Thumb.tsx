import React from "react";
import { AbsoluteFill } from "remotion";
import { FontGate } from "../lib/FontGate";
import { GradeDefs } from "../components/Grade";
import { Finish } from "../components/Finish";
import { C, FONT, rgba } from "../theme";
import { TEXT, type Lang } from "./script";

// The poster frame / thumbnail: designed as its own composition (a hero image from the film plus the title), one
// per language. Prefer a frame of the finished film as the image; a lone `remotion still` of a 3D scene can miss
// lighting that builds up over several frames.
export const Thumb: React.FC<{ lang: Lang }> = ({ lang }) => {
  const s = TEXT[lang].closing;
  return (
    <AbsoluteFill style={{ background: C.void }}>
      <GradeDefs />
      <FontGate>
        <AbsoluteFill style={{ background: `radial-gradient(50% 60% at 30% 45%, ${rgba(C.accentDeep, 0.35)} 0%, ${C.ink} 55%, ${C.void} 100%)` }} />
        <div style={{ position: "absolute", left: 160, top: 360 }}>
          <div style={{ fontFamily: FONT.display, fontWeight: 600, fontSize: 150, lineHeight: 1.04, letterSpacing: "-0.04em", color: C.fg }}>{s.name}</div>
          <div style={{ fontFamily: FONT.display, fontWeight: 600, fontSize: 150, lineHeight: 1.1, letterSpacing: "-0.04em", color: C.accent, textShadow: `0 0 60px ${rgba(C.accent, 0.35)}` }}>{s.accent}</div>
          <div style={{ marginTop: 30, fontFamily: FONT.sans, fontWeight: 500, fontSize: 44, color: C.fgSoft }}>{s.tagline}</div>
        </div>
      </FontGate>
      <Finish grain={0.06} vignette={0.6} />
    </AbsoluteFill>
  );
};
