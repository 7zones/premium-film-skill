import React from "react";
import { AbsoluteFill } from "remotion";
import { clamp01, lerp, ramp, useTime } from "../../lib/anim";
import { TitleLine, enter, fitSize } from "../../components/ui";
import { useCaptionLift } from "../../components/Captions";
import { Dust, Rings } from "../../components/Atmos";
import { C, EASE, FONT, rgba } from "../../theme";
import { TEXT, type Lang } from "../script";
import { cuesOf } from "../timeline";

// EXAMPLE SCENE (replace): the lockup. The wordmark lands with a light sweep (a real light move, not a white flash),
// the tagline and the URL follow a breath later, and the frame holds long enough to be read and remembered.
// Use the brand's own logo files (never retypeset a logo); this example only sets the name in type.

export const Closing: React.FC<{ lang: Lang }> = ({ lang }) => {
  const Q = cuesOf("closing", lang);
  const t = useTime();
  const s = TEXT[lang].closing;
  const lift = useCaptionLift();
  const ground = ramp(t, 0, 1.0, EASE.inOut);
  const sweep = ramp(t, Q.mark + 0.2, Q.mark + 1.6, EASE.inOut);
  const size = fitSize(`${s.name} ${s.accent}`, 1300, 150);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: ground, background: `radial-gradient(55% 60% at 50% 46%, ${rgba(C.accentDeep, 0.28)} 0%, ${C.ink} 60%, ${C.void} 100%)` }} />
      <AbsoluteFill style={{ opacity: ground }}>
        <Rings t={t} cy={470} opacity={0.045} pulse={ramp(t, Q.mark + 0.3, Q.mark + 3.0, EASE.out)} />
        <Dust t={t} seed={23} count={50} opacity={0.55} />
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 80 + lift, transform: `scale(${lerp(1.03, 1, clamp01(t / 6))})` }}>
        <div style={{ position: "relative" }}>
          <TitleLine t={t} at={Q.mark} parts={[s.name, s.accent]} size={size} glow={C.accent} />
          {/* the sweep: a soft band of light crossing the wordmark once */}
          <div
            style={{
              position: "absolute",
              inset: "-30% -10%",
              background: `linear-gradient(105deg, transparent ${lerp(-30, 110, sweep) - 12}%, ${rgba(C.accentSoft, 0.32)} ${lerp(-30, 110, sweep)}%, transparent ${lerp(-30, 110, sweep) + 12}%)`,
              mixBlendMode: "screen",
              opacity: sweep > 0 && sweep < 1 ? 1 : 0,
              pointerEvents: "none",
            }}
          />
        </div>
        <div style={{ marginTop: 34, fontFamily: FONT.sans, fontWeight: 500, fontSize: 42, color: C.fgSoft, ...enter(t, Q.tagline, 0.9) }}>{s.tagline}</div>
        <div style={{ marginTop: 22, fontFamily: FONT.mono, fontWeight: 500, fontSize: 30, letterSpacing: "0.04em", color: C.accentSoft, ...enter(t, Q.url, 0.9) }}>{s.url}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
