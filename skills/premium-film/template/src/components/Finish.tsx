import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { hash01, rng } from "../lib/anim";

const TILE = 256;

const makeGrainTile = () => {
  const canvas = document.createElement("canvas");
  canvas.width = TILE;
  canvas.height = TILE;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";
  const img = ctx.createImageData(TILE, TILE);
  const rand = rng(1337);
  for (let i = 0; i < TILE * TILE; i++) {
    // a triangular distribution reads as finer, more filmic grain than uniform noise
    const v = Math.round(((rand() + rand()) / 2) * 255);
    img.data[i * 4] = v;
    img.data[i * 4 + 1] = v;
    img.data[i * 4 + 2] = v;
    img.data[i * 4 + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return canvas.toDataURL("image/png");
};

/**
 * The finish on top of every frame: moving film grain (it also dithers dark gradients, which otherwise band after
 * H.264 encoding) and a lens vignette. Mount once, above all scenes.
 */
export const Finish: React.FC<{ grain?: number; vignette?: number }> = ({ grain = 0.085, vignette = 0.7 }) => {
  const frame = useCurrentFrame();
  const tile = useMemo(makeGrainTile, []);
  const ox = Math.floor(hash01(frame * 2 + 1) * TILE);
  const oy = Math.floor(hash01(frame * 2 + 2) * TILE);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 72% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${vignette}) 100%)` }} />
      {tile ? (
        <AbsoluteFill style={{ backgroundImage: `url(${tile})`, backgroundSize: `${TILE}px ${TILE}px`, backgroundPosition: `${ox}px ${oy}px`, mixBlendMode: "overlay", opacity: grain }} />
      ) : null}
    </AbsoluteFill>
  );
};
