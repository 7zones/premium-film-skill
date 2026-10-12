import React from "react";
import { AbsoluteFill } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { hitEnv, ramp, smoothPath, useTime } from "../../lib/anim";
import { Bloom } from "../../three/kit";
import { Glow, MirrorFloor, Motes, PoseRig, Shaft, Waves } from "../../three/fx";
import { TitleLine, fitSize } from "../../components/ui";
import { C, EASE } from "../../theme";
import { TEXT, type Lang } from "../script";
import { cuesOf } from "../timeline";

// EXAMPLE SCENE (replace): a lit 3D set rather than a flat background. A small, intense core over a polished floor
// that reflects it, dust that catches the light, a soft shaft from above, a ring of light on the ignite cue (with a
// few frames of attack, never an instant pop), and a camera that keeps moving along one smooth path. The title is
// HTML over the canvas, set in clear dark space BELOW the light (never type over a hot spot), revealed out of a mask
// and blurred out on exit. The floor fades into the dark before the horizon, so there is no hard line.
const CORE: [number, number, number] = [0, 1.9, 0];

export const Opening: React.FC<{ lang: Lang }> = ({ lang }) => {
  const Q = cuesOf("opening", lang);
  const t = useTime();
  const s = TEXT[lang].opening;
  const z = smoothPath(t, [0, 3.5, 8.5], [10.5, 7.6, 6.4]);
  const y = smoothPath(t, [0, 8.5], [1.25, 1.05]);
  const ignite = hitEnv(t, Q.ignite, 0.6);
  const core = ramp(t, Q.ignite - 0.25, Q.ignite + 1.6, EASE.out);
  const out = ramp(t, Q.out, Q.out + 1.1, EASE.inOut);
  const size = fitSize(`${s.lead} ${s.accent}`, 1400, 96);
  return (
    <AbsoluteFill style={{ background: C.void }}>
      <ThreeCanvas width={1920} height={1080} gl={{ antialias: true, preserveDrawingBuffer: true }} camera={{ fov: 34, near: 0.05, far: 200, position: [0, 1.25, 10.5] }}>
        <PoseRig pose={{ pos: [0, y, z], target: [0, 1.45, 0], fov: 34 }} />
        <color attach="background" args={[C.void]} />
        <MirrorFloor y={0} strength={0.5} fade={9} blur={[0.002, 0.005]} base={C.void} haze={C.void} hazeRange={[9, 22]} />
        {/* halo, then a small hot core: the light reads as a source, not a blown-out blob */}
        <Glow position={CORE} scale={1.1 + 1.1 * core} color={C.accent} opacity={(0.1 + 0.55 * core + 0.6 * ignite) * (1 - out)} depthTest={false} />
        <Glow position={CORE} scale={0.28 + 0.16 * core} color={C.accentSoft} core={2.2} opacity={(0.2 + 0.9 * core) * (1 - out)} depthTest={false} />
        <Waves t={t} at={[Q.ignite, Q.ignite + 1.9, Q.ignite + 3.8]} position={CORE} reach={2.6} life={2.4} color={C.accent} opacity={0.55 * (1 - out)} />
        <Shaft t={t} position={[0, 7.5, -0.4]} length={7.5} radius={2.2} top={0.3} color={C.accentSoft} opacity={0.07 * core * (1 - out)} />
        <Motes t={t} n={1400} box={[16, 5, 18]} center={[0, 2.2, -2]} color={C.accentSoft} opacity={0.6} focus={7} />
        <Bloom strength={0.8} radius={0.55} threshold={0.2} knee={0.2} />
      </ThreeCanvas>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 190 }}>
        <TitleLine t={t} at={Q.title} parts={[s.lead, s.accent]} size={size} exit={out} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
