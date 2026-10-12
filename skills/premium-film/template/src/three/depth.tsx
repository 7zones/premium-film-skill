import React, { useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { useTexture } from "../lib/tex";

/** Photo + depth textures, loaded outside the canvas (R3F only redraws on frame changes). */
export const useDepthTex = (name: string, dir = "plates", ext = "jpg") => {
  const img = useTexture(`${dir}/${name}.${ext}`, { srgb: true });
  const dep = useTexture(`depth/${name}.png`, { mip: false });
  return img && dep ? { img, dep } : null;
};
export type DepthTex = { img: THREE.Texture; dep: THREE.Texture };

/** The two layers of a photo (tools/depth/layers.py): the far layer filled in behind, the near layer's alpha. */
export const useLayers = (name: string, dir = "plates") => {
  const img = useTexture(`${dir}/${name}.jpg`, { srgb: true });
  const dep = useTexture(`depth/${name}-fgd.png`, { mip: false });
  const bgImg = useTexture(`${dir}/${name}-bg.jpg`, { srgb: true });
  const bgDep = useTexture(`depth/${name}-bg.png`, { mip: false });
  const mask = useTexture(`depth/${name}-fg.png`, { mip: false });
  return img && dep && bgImg && bgDep && mask ? { front: { img, dep }, back: { img: bgImg, dep: bgDep }, mask } : null;
};
export type Layers = NonNullable<ReturnType<typeof useLayers>>;

// 2.5D photographs: a photo plus its depth map (Depth Anything V2, near = white) rebuilt as real
// geometry seen from a virtual camera at the origin looking down −z, so a moving camera gets true
// parallax. `DepthPlate` is the solid surface; `DepthCloud` is the same picture as points that can
// come apart into a stream of light.

export type DepthOpts = {
  tex: DepthTex;
  aspect?: number; // image width / height
  fov?: number; // vertical field of view of the original photo (degrees)
  near?: number; // distance of the nearest pixel
  far?: number; // distance of the farthest pixel
};

const PROJ = /* glsl */ `
uniform sampler2D uDepth; uniform float uTanY; uniform float uAspect; uniform float uNear; uniform float uFar;
vec3 project(vec2 uv, out float z) {
  float d = texture2D(uDepth, uv).r;
  z = 1.0 / mix(1.0 / uFar, 1.0 / uNear, d);
  return vec3((uv.x - 0.5) * 2.0 * uTanY * uAspect * z, (0.5 - uv.y) * 2.0 * uTanY * z, -z);
}`;

// Release timing shared by plate and cloud, so a pixel leaves the photo exactly when its point flies
// off. The front follows depth (near first, or far first) loosened by smooth noise, so it travels
// as an organic, burning edge rather than in blocks.
const KEY = /* glsl */ `
uniform float uTime; uniform float uT0; uniform float uT1; uniform float uOrder; uniform vec2 uGrid; uniform float uFarFirst;
float cellHash(vec2 c, float k){ return fract(sin(dot(c, vec2(12.9898, 78.233)) + k * 17.17) * 43758.5453); }
float vnoise(vec2 p){
  vec2 i = floor(p); vec2 f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  float a = cellHash(i, 7.0); float b = cellHash(i + vec2(1.0, 0.0), 7.0);
  float c = cellHash(i + vec2(0.0, 1.0), 7.0); float d = cellHash(i + vec2(1.0, 1.0), 7.0);
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbm(vec2 p){ return 0.55 * vnoise(p) + 0.3 * vnoise(p * 2.03 + 1.7) + 0.15 * vnoise(p * 4.1 + 3.1); }
float releaseAt(vec2 uv){
  float d = texture2D(uDepth, uv).r;
  float order = uFarFirst > 0.5 ? d : 1.0 - d;
  float key = mix(order, fbm(uv * vec2(30.0, 17.0)), uOrder);
  return mix(uT0, uT1, clamp(key, 0.0, 1.0));
}`;

const uniformsFor = (o: Required<Omit<DepthOpts, "tex">>, img: THREE.Texture, dep: THREE.Texture) => ({
  uImg: { value: img },
  uDepth: { value: dep },
  uTanY: { value: Math.tan(((o.fov / 2) * Math.PI) / 180) },
  uAspect: { value: o.aspect },
  uNear: { value: o.near },
  uFar: { value: o.far },
});

const PLATE_VERT = /* glsl */ `
${PROJ}
attribute vec2 aUv; varying vec2 vUv; varying float vZ;
void main(){ float z; vec3 p = project(aUv, z); vUv = aUv; vZ = z; gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0); }`;
const PLATE_FRAG = /* glsl */ `
uniform float uNear; uniform float uFar; uniform sampler2D uDepth;
${KEY}
uniform sampler2D uImg; uniform float uA; uniform float uExposure; uniform vec3 uTint; uniform float uFog; uniform vec3 uFogColor;
uniform float uSat; uniform float uEdge; uniform vec3 uRim; varying vec2 vUv; varying float vZ;
uniform sampler2D uMask; uniform float uHasMask; uniform float uCut;
uniform vec4 uLamp; uniform vec3 uLampColor; uniform vec3 uScan; uniform vec3 uScanColor;
void main(){
  // past its release a pixel burns out over uEdge seconds behind a soft glowing rim
  float e = (uTime - releaseAt(vUv)) / uEdge;
  if (e >= 1.0) discard;
  vec3 c = texture2D(uImg, vUv).rgb;
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(l), c, uSat) * uTint * uExposure;
  // a hand-held lamp: a soft pool of light (photo uv centre xy, radius z, strength w) that also warms the grade
  vec2 ld = (vUv - uLamp.xy) * vec2(1.7778, 1.0) / max(uLamp.z, 0.001);
  float pool = exp(-dot(ld, ld) * 2.2) * uLamp.w;
  c = c * (1.0 + 2.6 * pool * uLampColor) + uLampColor * pool * 0.05;
  // a scanning slice of light travelling through the depth of the picture (depth x, width y, strength z)
  float sd = (vZ - uScan.x) / max(uScan.y, 0.001);
  float slice = exp(-sd * sd) * uScan.z;
  c = c * (1.0 + 0.7 * slice) + uScanColor * slice * (0.22 + 0.5 * smoothstep(0.2, 0.7, dot(c, vec3(0.33))));
  c = mix(c, uFogColor, uFog * smoothstep(0.0, 1.0, vZ / uFar));
  // stretched skins between foreground and background fade out instead of smearing (the far layer of a
  // layered photo has nothing behind it and keeps them; its depth is smooth)
  float stretch = fwidth(vZ) / max(vZ, 0.001) * uCut;
  // a thin hot line right at the front, not a wash
  float rim = smoothstep(-0.1, 0.0, e) * (1.0 - smoothstep(0.0, 0.18, e));
  c += uRim * rim;
  float a = uA * (1.0 - smoothstep(0.06, 0.2, stretch)) * (1.0 - smoothstep(0.0, 1.0, e));
  if (uHasMask > 0.5) a *= texture2D(uMask, vUv).r;
  if (a < 0.02) discard;
  gl_FragColor = vec4(c, a);
}`;

const grid = (cols: number, rows: number) => {
  const uv = new Float32Array((cols + 1) * (rows + 1) * 2);
  for (let j = 0; j <= rows; j++) for (let i = 0; i <= cols; i++) uv.set([i / cols, j / rows], (j * (cols + 1) + i) * 2);
  const idx: number[] = [];
  for (let j = 0; j < rows; j++)
    for (let i = 0; i < cols; i++) {
      const a = j * (cols + 1) + i;
      idx.push(a, a + cols + 1, a + 1, a + 1, a + cols + 1, a + cols + 2);
    }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(new Float32Array((cols + 1) * (rows + 1) * 3), 3));
  g.setAttribute("aUv", new THREE.BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g;
};

export const DepthPlate: React.FC<
  DepthOpts & { opacity?: number; exposure?: number; tint?: THREE.ColorRepresentation; fog?: number; fogColor?: THREE.ColorRepresentation; saturation?: number; cols?: number; renderOrder?: number; t?: number; release?: [number, number]; order?: number; farFirst?: boolean; edge?: number; rim?: THREE.ColorRepresentation; layer?: number } & PlateLight & { mask?: THREE.Texture; cut?: boolean }
> = ({ tex, aspect = 16 / 9, fov = 50, near = 2, far = 30, opacity = 1, exposure = 1, tint = "#ffffff", fog = 0, fogColor = "#000000", saturation = 1, cols = 480, renderOrder, t = 0, release, order = 0.35, farFirst = true, edge = 0.3, rim = "#000000", layer = 0, lamp, scan, mask, cut = true }) => {
  const { img, dep } = tex;
  const geo = useMemo(() => grid(cols, Math.round(cols / aspect)), [cols, aspect]);
  const mat = useMemo(() => {
    return new THREE.ShaderMaterial({
      vertexShader: PLATE_VERT,
      fragmentShader: PLATE_FRAG,
      uniforms: { ...uniformsFor({ aspect, fov, near, far }, img, dep), uTime: { value: 0 }, uT0: { value: 1e9 }, uT1: { value: 1e9 }, uOrder: { value: 0.35 }, uFarFirst: { value: 1 }, uGrid: { value: new THREE.Vector2(560, Math.round(560 / aspect)) }, uA: { value: 1 }, uExposure: { value: 1 }, uTint: { value: new THREE.Color() }, uFog: { value: 0 }, uFogColor: { value: new THREE.Color() }, uSat: { value: 1 }, uEdge: { value: 0.3 }, uRim: { value: new THREE.Color() }, uMask: { value: null }, uHasMask: { value: 0 }, uCut: { value: 1 }, uLamp: { value: new THREE.Vector4(0, 0, 1, 0) }, uLampColor: { value: new THREE.Color() }, uScan: { value: new THREE.Vector3(0, 1, 0) }, uScanColor: { value: new THREE.Color() } },
      transparent: true,
      depthWrite: true,
    });
  }, [img, dep, aspect, fov, near, far]);
  mat.uniforms.uA.value = opacity;
  mat.uniforms.uExposure.value = exposure;
  (mat.uniforms.uTint.value as THREE.Color).set(tint);
  mat.uniforms.uFog.value = fog;
  (mat.uniforms.uFogColor.value as THREE.Color).set(fogColor);
  mat.uniforms.uSat.value = saturation;
  mat.uniforms.uTime.value = t;
  mat.uniforms.uT0.value = release ? release[0] : 1e9;
  mat.uniforms.uT1.value = release ? release[1] : 1e9;
  mat.uniforms.uOrder.value = order;
  mat.uniforms.uFarFirst.value = farFirst ? 1 : 0;
  mat.uniforms.uEdge.value = edge;
  (mat.uniforms.uRim.value as THREE.Color).set(rim);
  mat.uniforms.uMask.value = mask ?? null;
  mat.uniforms.uHasMask.value = mask ? 1 : 0;
  mat.uniforms.uCut.value = cut ? 1 : 0;
  (mat.uniforms.uLamp.value as THREE.Vector4).set(lamp?.uv[0] ?? 0, lamp?.uv[1] ?? 0, lamp?.r ?? 1, lamp?.i ?? 0);
  (mat.uniforms.uLampColor.value as THREE.Color).set(lamp?.color ?? "#ffd9a8");
  (mat.uniforms.uScan.value as THREE.Vector3).set(scan?.z ?? 0, scan?.w ?? 1, scan?.i ?? 0);
  (mat.uniforms.uScanColor.value as THREE.Color).set(scan?.color ?? "#7fdcff");
  const ref = useRef<THREE.Mesh>(null);
  useLayoutEffect(() => void ref.current?.layers.set(layer), [layer]);
  return <mesh ref={ref} geometry={geo} material={mat} frustumCulled={false} renderOrder={renderOrder} />;
};

type PlateLight = { lamp?: { uv: [number, number]; r: number; i: number; color?: THREE.ColorRepresentation }; scan?: { z: number; w: number; i: number; color?: THREE.ColorRepresentation } };
type PlateProps = React.ComponentProps<typeof DepthPlate>;

/** A photo in depth as two layers: the filled-in far layer, and the near layer cut out on top of it. */
export const LayeredPlate: React.FC<Omit<PlateProps, "tex" | "mask" | "cut"> & { layers: Layers }> = ({ layers, renderOrder = 0, ...rest }) => (
  <>
    <DepthPlate {...rest} tex={layers.back} cut={false} renderOrder={renderOrder} />
    <DepthPlate {...rest} tex={layers.front} mask={layers.mask} renderOrder={renderOrder + 1} />
  </>
);

// ---------------------------------------------------------------------------------------------
// Point cloud of the same picture. A point is drawn once its cell is released (or always, with
// `rest`): it lifts off, turns to light and is pulled onto a stream from `from` to `to`.

const CLOUD_VERT = /* glsl */ `
${PROJ}
${KEY}
uniform sampler2D uImg; uniform float uSize; uniform vec3 uFrom; uniform vec3 uTo; uniform float uSpread; uniform float uSpeed;
uniform float uRest; uniform vec3 uGlow; uniform vec3 uLift; uniform float uKeep; uniform float uMaxPx; uniform float uCut; uniform float uJitter;
attribute vec2 aUv;
varying vec3 vCol; varying float vA; varying float vK;
void main(){
  float z; vec3 p = project(aUv, z);
  vec2 cell = floor(aUv * uGrid);
  float h1 = cellHash(cell, 3.0); float h2 = cellHash(cell, 4.0); float h3 = cellHash(cell, 5.0);
  float age = uTime - releaseAt(aUv);
  if (texture2D(uDepth, aUv).r < uCut || (age < 0.0 && uRest < 0.5)) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); gl_PointSize = 0.0; vA = 0.0; return; }
  // each point lingers a random moment as a grain of the photo before it lifts off, so the points freed
  // together along one depth contour never travel as a single line
  float a = max(age - h2 * uJitter, 0.0);
  vec3 c = texture2D(uImg, aUv).rgb;
  // lift: a small kick away from where it sat, with its own wobble
  float lift = 1.0 - exp(-a * 2.2);
  vec3 kick = (vec3(h1, h2, h3) - 0.5) * 0.5 + uLift;
  vec3 q = p + kick * lift * (0.4 + 0.6 * h3);
  // stream: joins the line near its own position and runs toward uTo
  vec3 dir = uTo - uFrom;
  float s0 = clamp(dot(p - uFrom, dir) / dot(dir, dir), 0.0, 1.0);
  float s = s0 + max(a - 0.35, 0.0) * uSpeed * (0.6 + 0.8 * h2);
  float ang = h1 * 6.2831 + a * (1.0 + h3);
  vec3 side = normalize(cross(dir, vec3(0.0, 1.0, 0.0)));
  vec3 up = normalize(cross(side, dir));
  vec3 onLine = uFrom + dir * s + (side * cos(ang) + up * sin(ang)) * uSpread * (0.15 + 0.85 * h2 * h2);
  float k = smoothstep(0.2, 1.6, a);
  q = mix(q, onLine, k);
  float glow = smoothstep(0.0, 0.6, a);
  vCol = mix(c, uGlow * (0.55 + 0.9 * h3), glow * 0.9);
  vK = glow;
  // only a share of the freed points stay as sparks; the rest fade like ash
  float keep = step(h1, uKeep);
  vA = (1.0 - smoothstep(0.92, 1.05, s)) * (age < 0.0 ? 0.7 : mix(1.0 - smoothstep(0.1, 0.55, a), 1.0, keep));
  vec4 mv = modelViewMatrix * vec4(q, 1.0);
  vA *= smoothstep(0.25, 1.2, -mv.z);
  float rest = 2.0 * uTanY / uGrid.y * z * 1.25;
  float spark = uSize * (0.5 + 1.5 * pow(h3, 4.0));
  gl_PointSize = clamp(mix(rest, spark, glow) * projectionMatrix[1][1] * 540.0 / -mv.z, 1.0, mix(64.0, uMaxPx, glow));
  gl_Position = projectionMatrix * mv;
}`;
const CLOUD_FRAG = /* glsl */ `
uniform float uA; uniform float uExposure; varying vec3 vCol; varying float vA; varying float vK;
void main(){
  vec2 c = gl_PointCoord - 0.5; float d = length(c);
  float a = mix(1.0 - smoothstep(0.35, 0.5, d), exp(-d * d * 22.0), vK);
  if (a * vA < 0.004) discard;
  vec3 col = vCol * uExposure * (1.0 + vK * 0.5);
  gl_FragColor = vec4(col, a * uA * vA);
}`;

export const DepthCloud: React.FC<
  DepthOpts & {
    t: number;
    release?: [number, number];
    order?: number;
    from?: [number, number, number];
    to?: [number, number, number];
    spread?: number;
    speed?: number;
    size?: number;
    opacity?: number;
    exposure?: number;
    glow?: THREE.ColorRepresentation;
    lift?: [number, number, number];
    rest?: boolean;
    keep?: number;
    maxPx?: number;
    cut?: number; // hide points whose depth value (0 far … 1 near) is below this
    jitter?: number; // seconds of random linger before a freed point lifts off
    cols?: number;
    farFirst?: boolean;
    layer?: number;
  }
> = ({ tex, aspect = 16 / 9, fov = 50, near = 2, far = 30, t, release, order = 0.35, from = [0, 0, 0], to = [0, 0, -1], spread = 0.5, speed = 0.25, size = 0.03, opacity = 1, exposure = 1, glow = "#8fdcff", lift = [0, 0.15, 0], rest = false, keep = 0.3, maxPx = 6, cut = -1, cols = 560, farFirst = true, layer = 0, jitter = 0 }) => {
  const { img, dep } = tex;
  const rows = Math.round(cols / aspect);
  const geo = useMemo(() => {
    const n = cols * rows;
    const uv = new Float32Array(n * 2);
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) uv.set([(i + 0.5) / cols, (j + 0.5) / rows], (j * cols + i) * 2);
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    g.setAttribute("aUv", new THREE.BufferAttribute(uv, 2));
    return g;
  }, [cols, rows]);
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: CLOUD_VERT,
        fragmentShader: CLOUD_FRAG,
        uniforms: {
          ...uniformsFor({ aspect, fov, near, far }, img, dep),
          uTime: { value: 0 },
          uT0: { value: 1e9 },
          uT1: { value: 1e9 },
          uOrder: { value: order },
          uFarFirst: { value: 1 },
          uGrid: { value: new THREE.Vector2(cols, rows) },
          uSize: { value: size },
          uFrom: { value: new THREE.Vector3() },
          uTo: { value: new THREE.Vector3() },
          uSpread: { value: spread },
          uSpeed: { value: speed },
          uRest: { value: 0 },
          uGlow: { value: new THREE.Color() },
          uLift: { value: new THREE.Vector3() },
          uKeep: { value: 0.3 },
          uCut: { value: -1 },
          uJitter: { value: 0 },
          uMaxPx: { value: 6 },
          uA: { value: 1 },
          uExposure: { value: 1 },
        },
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    [img, dep, aspect, fov, near, far, order, size, spread, speed, cols, rows],
  );
  mat.uniforms.uTime.value = t;
  mat.uniforms.uT0.value = release ? release[0] : 1e9;
  mat.uniforms.uT1.value = release ? release[1] : 1e9;
  (mat.uniforms.uFrom.value as THREE.Vector3).set(...from);
  (mat.uniforms.uTo.value as THREE.Vector3).set(...to);
  mat.uniforms.uRest.value = rest ? 1 : 0;
  mat.uniforms.uKeep.value = keep;
  mat.uniforms.uCut.value = cut;
  mat.uniforms.uMaxPx.value = maxPx;
  (mat.uniforms.uGlow.value as THREE.Color).set(glow);
  (mat.uniforms.uLift.value as THREE.Vector3).set(...lift);
  mat.uniforms.uA.value = opacity;
  mat.uniforms.uExposure.value = exposure;
  mat.uniforms.uFarFirst.value = farFirst ? 1 : 0;
  mat.uniforms.uJitter.value = jitter;
  const ref = useRef<THREE.Points>(null);
  useLayoutEffect(() => void ref.current?.layers.set(layer), [layer]);
  return <points ref={ref} geometry={geo} material={mat} frustumCulled={false} />;
};
