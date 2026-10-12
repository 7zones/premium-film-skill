import React from "react";
import { AbsoluteFill } from "remotion";
import { clamp01, lerp, ramp, useTime } from "../../lib/anim";
import { BigStat, Glass, WordReveal, enter, leave } from "../../components/ui";
import { Dust, Rings, Spark } from "../../components/Atmos";
import { useCaptioned, useCaptionLift } from "../../components/Captions";
import { C, EASE, rgba } from "../../theme";
import { TEXT, type Lang } from "../script";
import { cuesOf } from "../timeline";

// EXAMPLE SCENE (replace): one idea, one big designed piece, generous space. Patterns worth keeping:
//  - the ground is transparent during the pre-roll and fades in from the scene's own start, so the previous scene's
//    ending is never blacked out (an opaque pre-roll silently deletes the last beat of the scene before)
//  - the light arrives first (a spark that opens into the card), then the card, then the hero number, which lands
//    sharp and gets a single light sweep across its glass; a supporting line follows word by word
//  - nothing is ever static: dust drifts, rings travel, the camera pushes slowly the whole time
//  - in the captioned cut, the line that only repeats the narration is hidden and low type lifts clear of the band

export const Proof: React.FC<{ lang: Lang }> = ({ lang }) => {
  const Q = cuesOf("proof", lang);
  const t = useTime();
  const s = TEXT[lang].proof;
  const captioned = useCaptioned();
  const lift = useCaptionLift();
  const ground = ramp(t, 0, 0.9, EASE.inOut);
  const push = lerp(1, 1.06, clamp01(t / 7));
  const exit = ramp(t, Q.out, Q.out + 0.9, EASE.in);
  const spark = ramp(t, Q.card - 0.6, Q.card, EASE.out) * (1 - ramp(t, Q.card, Q.card + 0.7, EASE.inOut));
  const sweep = ramp(t, Q.stat + 0.9, Q.stat + 2.1, EASE.inOut);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity: ground * (1 - 0.6 * exit), background: `radial-gradient(60% 70% at 50% 45%, ${rgba(C.accentDeep, 0.22)} 0%, ${C.ink} 55%, ${C.void} 100%)` }} />
      <AbsoluteFill style={{ opacity: ground }}>
        <Rings t={t} cy={500} pulse={ramp(t, Q.stat + 0.9, Q.stat + 3.2, EASE.out)} />
        <Dust t={t} seed={11} count={70} opacity={0.7} />
      </AbsoluteFill>
      <Spark x={960} y={500} size={1.1} intensity={spark} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 80, transform: `scale(${push})` }}>
        <div style={{ position: "relative", ...enter(t, Q.card, 1.0, 40, 14), ...(t >= Q.out ? leave(t, Q.out, 0.9) : {}) }}>
          <Glass accent={C.accent} glow={0.6 * ramp(t, Q.stat, Q.stat + 1.2)} style={{ padding: "64px 110px 70px", overflow: "hidden" }}>
            <BigStat t={t} at={Q.stat} value={s.value} label={s.label} size={170} exit={exit} />
            {/* one soft band of light crossing the glass after the number lands */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: `linear-gradient(105deg, transparent ${lerp(-40, 120, sweep) - 14}%, ${rgba(C.accentSoft, 0.14)} ${lerp(-40, 120, sweep)}%, transparent ${lerp(-40, 120, sweep) + 14}%)`,
                opacity: sweep > 0 && sweep < 1 ? 1 : 0,
                pointerEvents: "none",
              }}
            />
          </Glass>
        </div>
      </AbsoluteFill>
      {captioned ? null : (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 170 + lift }}>
          <WordReveal t={t} at={Q.line} text={s.line} size={46} color={C.fgSoft} exit={exit} />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
