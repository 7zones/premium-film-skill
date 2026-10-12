import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { staticFile, useDelayRender } from "remotion";

/**
 * An image as a three.js texture; the frame waits until it is decoded. Load textures OUTSIDE the <ThreeCanvas>
 * and pass them in: R3F only redraws when the frame changes, so anything that arrives asynchronously inside the
 * canvas misses its frame and renders blank or stale. `srgb` marks colour images (not depth maps or masks).
 */
export const useTexture = (src: string, opts: { mip?: boolean; srgb?: boolean; wrap?: boolean } = {}) => {
  const { mip = true, srgb = false, wrap = false } = opts;
  const [tex, setTex] = useState<THREE.Texture | null>(null);
  const { delayRender, continueRender } = useDelayRender();
  const handle = useRef<number | null>(null);
  if (!tex && handle.current === null && typeof document !== "undefined") handle.current = delayRender(`Loading ${src}`);
  useEffect(() => {
    if (tex) return;
    let alive = true;
    // decoding can fail transiently while many frames render at once: try again a few times
    const load = (tries: number): Promise<HTMLImageElement> => {
      const im = new Image();
      im.src = staticFile(src);
      return im.decode().then(
        () => im,
        (e) => (tries > 1 ? new Promise((r) => setTimeout(r, 250)).then(() => load(tries - 1)) : Promise.reject(e)),
      );
    };
    load(4).then((img) => {
      if (!alive) return;
      const t = new THREE.Texture(img);
      t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      t.flipY = false;
      t.generateMipmaps = mip;
      t.minFilter = mip ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
      t.magFilter = THREE.LinearFilter;
      t.anisotropy = 16;
      if (wrap) t.wrapS = THREE.RepeatWrapping;
      t.needsUpdate = true;
      setTex(t);
    });
    return () => {
      alive = false;
    };
  }, [tex, src, mip, srgb, wrap]);
  useEffect(() => {
    if (tex && handle.current !== null) {
      continueRender(handle.current);
      handle.current = null;
    }
  }, [tex, continueRender]);
  return tex;
};
