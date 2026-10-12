import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { useThree } from "@react-three/fiber";
import { Reflector } from "three/examples/jsm/objects/Reflector.js";
import { staticFile, useDelayRender } from "remotion";
import { clamp01 } from "../lib/anim";

// Shared 3D pieces for the film's sets: camera poses that the HTML overlays can follow, canvas-drawn
// textures (crisp type and UI inside 3D), dust in the air, light shafts, glows and a polished floor.

export type Pose = { pos: [number, number, number]; target: [number, number, number]; fov: number; roll?: number };

/** Puts the default camera at a pose every frame. */
export const PoseRig: React.FC<{ pose: Pose; near?: number; far?: number; layers?: number[] }> = ({ pose, near, far, layers }) => {
  const { camera } = useThree();
  useLayoutEffect(() => {
    const c = camera as THREE.PerspectiveCamera;
    layers?.forEach((l) => c.layers.enable(l));
    c.position.set(...pose.pos);
    const r = pose.roll ?? 0;
    c.up.set(Math.sin(r), Math.cos(r), 0);
    c.lookAt(...pose.target);
    let dirty = false;
    if (c.fov !== pose.fov) (c.fov = pose.fov), (dirty = true);
    if (near && c.near !== near) (c.near = near), (dirty = true);
    if (far && c.far !== far) (c.far = far), (dirty = true);
    if (dirty) c.updateProjectionMatrix();
  });
  return null;
};

const scratch = new THREE.PerspectiveCamera(50, 16 / 9, 0.01, 1000);
/** Screen position (px) and depth of a world point seen from a pose; for HTML that rides on 3D. */
export const project = (p: [number, number, number], pose: Pose, w = 1920, h = 1080) => {
  scratch.fov = pose.fov;
  scratch.aspect = w / h;
  scratch.updateProjectionMatrix();
  scratch.position.set(...pose.pos);
  const r = pose.roll ?? 0;
  scratch.up.set(Math.sin(r), Math.cos(r), 0);
  scratch.lookAt(...pose.target);
  scratch.updateMatrixWorld();
  const v = new THREE.Vector3(...p);
  const dist = v.distanceTo(scratch.position);
  v.project(scratch);
  return { x: (v.x * 0.5 + 0.5) * w, y: (-v.y * 0.5 + 0.5) * h, behind: v.z > 1, dist, scale: h / 2 / Math.tan((pose.fov * Math.PI) / 360) / dist };
};

/** Loads images for canvas drawing; the frame waits until all are decoded. */
export const useImages = (srcs: string[]) => {
  const key = srcs.join("|");
  const [imgs, setImgs] = useState<HTMLImageElement[] | null>(null);
  const { delayRender, continueRender } = useDelayRender();
  const handle = useRef<number | null>(null);
  if (!imgs && handle.current === null && typeof document !== "undefined") handle.current = delayRender(`Loading ${srcs.length} images`);
  useEffect(() => {
    let alive = true;
    Promise.all(
      srcs.map((s) => {
        const im = new Image();
        im.src = staticFile(s);
        return im.decode().then(() => im);
      }),
    ).then((r) => alive && setImgs(r));
    return () => {
      alive = false;
    };
  }, [key]);
  useEffect(() => {
    if (imgs && handle.current !== null) {
      continueRender(handle.current);
      handle.current = null;
    }
  }, [imgs, continueRender]);
  return imgs;
};

/** A texture drawn once with Canvas 2D (fonts are loaded before any frame renders). */
export const canvasTexture = (w: number, h: number, draw: (g: CanvasRenderingContext2D, w: number, h: number) => void, srgb = true) => {
  const cv = document.createElement("canvas");
  cv.width = w;
  cv.height = h;
  const g = cv.getContext("2d")!;
  draw(g, w, h);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.anisotropy = 16;
  t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.needsUpdate = true;
  return t;
};

/** Draws an image to cover a box (like CSS object-fit: cover), with an optional focus point. */
export const drawCover = (g: CanvasRenderingContext2D, im: HTMLImageElement, x: number, y: number, w: number, h: number, fx = 0.5, fy = 0.5) => {
  const s = Math.max(w / im.width, h / im.height);
  const sw = w / s;
  const sh = h / s;
  g.drawImage(im, (im.width - sw) * fx, (im.height - sh) * fy, sw, sh, x, y, w, h);
};

export const roundRect = (g: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) => {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
};

// ---------------------------------------------------------------------------------------------
// Dust motes: soft points drifting in a box, sized by distance (out-of-focus ones grow and fade).

const MOTE_VERT = /* glsl */ `
uniform float uTime; uniform vec3 uBox; uniform vec3 uCenter; uniform float uSize; uniform float uFocus; uniform float uDrift;
attribute vec3 aSeed; varying float vA; varying float vBlur;
void main(){
  vec3 p = (aSeed - 0.5) * uBox;
  p += vec3(sin(uTime * 0.21 + aSeed.y * 30.0), sin(uTime * 0.17 + aSeed.z * 30.0) + uTime * 0.04 * uDrift, cos(uTime * 0.19 + aSeed.x * 30.0)) * 0.25;
  p.y = mod(p.y + uBox.y * 0.5, uBox.y) - uBox.y * 0.5;
  vec4 mv = modelViewMatrix * vec4(p + uCenter, 1.0);
  float d = -mv.z;
  vBlur = clamp(abs(d - uFocus) / uFocus, 0.0, 1.0);
  float px = uSize * (0.5 + fract(aSeed.x * 13.7)) * projectionMatrix[1][1] * 540.0 / d;
  gl_PointSize = clamp(px * (1.0 + vBlur * 5.0), 1.0, 40.0);
  vA = (0.35 + 0.65 * fract(aSeed.z * 7.1)) / (1.0 + vBlur * 6.0) * smoothstep(0.3, 1.5, d);
  gl_Position = projectionMatrix * mv;
}`;
const MOTE_FRAG = /* glsl */ `
uniform vec3 uColor; uniform float uA; varying float vA; varying float vBlur;
void main(){ float d = length(gl_PointCoord - 0.5); float a = mix(exp(-d * d * 30.0), smoothstep(0.5, 0.35, d) * 0.6, vBlur) * vA * uA;
  if (a < 0.003) discard; gl_FragColor = vec4(uColor, a); }`;

export const Motes: React.FC<{ t: number; n?: number; box?: [number, number, number]; center?: [number, number, number]; size?: number; focus?: number; color?: THREE.ColorRepresentation; opacity?: number; drift?: number; seed?: number }> = ({
  t,
  n = 1500,
  box = [12, 6, 20],
  center = [0, 0, -8],
  size = 0.012,
  focus = 6,
  color = "#bfe8ff",
  opacity = 1,
  drift = 1,
  seed = 7,
}) => {
  const geo = useMemo(() => {
    const s = new Float32Array(n * 3);
    let x = seed * 9301 + 49297;
    const r = () => ((x = (x * 1664525 + 1013904223) >>> 0) / 4294967296);
    for (let i = 0; i < n * 3; i++) s[i] = r();
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    g.setAttribute("aSeed", new THREE.BufferAttribute(s, 3));
    return g;
  }, [n, seed]);
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: MOTE_VERT,
        fragmentShader: MOTE_FRAG,
        uniforms: { uTime: { value: 0 }, uBox: { value: new THREE.Vector3() }, uCenter: { value: new THREE.Vector3() }, uSize: { value: 0 }, uFocus: { value: 6 }, uDrift: { value: 1 }, uColor: { value: new THREE.Color() }, uA: { value: 1 } },
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    [],
  );
  mat.uniforms.uTime.value = t;
  (mat.uniforms.uBox.value as THREE.Vector3).set(...box);
  (mat.uniforms.uCenter.value as THREE.Vector3).set(...center);
  mat.uniforms.uSize.value = size;
  mat.uniforms.uFocus.value = focus;
  mat.uniforms.uDrift.value = drift;
  (mat.uniforms.uColor.value as THREE.Color).set(color);
  mat.uniforms.uA.value = opacity;
  return <points geometry={geo} material={mat} frustumCulled={false} />;
};

// ---------------------------------------------------------------------------------------------
// Volumetric light shaft: an open cone, bright along its axis and fading with length and at the rim.

const SHAFT_VERT = /* glsl */ `
varying vec3 vW; varying vec3 vN; varying float vL;
void main(){ vL = 1.0 - uv.y; vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; vN = normalize(mat3(modelMatrix) * normal); gl_Position = projectionMatrix * viewMatrix * w; }`;
const SHAFT_FRAG = /* glsl */ `
uniform vec3 uColor; uniform float uA; uniform float uTime; varying vec3 vW; varying vec3 vN; varying float vL;
float h(vec2 p){ return fract(sin(dot(p, vec2(41.3, 289.1))) * 45758.5); }
float n2(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
void main(){
  // multisampling can interpolate just outside a triangle, so every pow base is clamped (a NaN here
  // would be smeared over the whole frame by the bloom)
  vec3 v = normalize(cameraPosition - vW);
  float l = clamp(vL, 0.0, 1.0);
  float edge = pow(clamp(abs(dot(normalize(vN), v)), 0.0, 1.0), 1.6);
  float fall = pow(1.0 - l, 1.4) * smoothstep(0.0, 0.08, l);
  float grain = 0.75 + 0.25 * n2(vec2(vW.x * 3.0 + vW.z * 2.0, vW.y * 1.5 - uTime * 0.3));
  float a = edge * fall * grain * uA;
  gl_FragColor = vec4(uColor * a, a);
}`;

export const Shaft: React.FC<{ t: number; position: [number, number, number]; rotation?: [number, number, number]; length?: number; radius?: number; top?: number; color?: THREE.ColorRepresentation; opacity?: number }> = ({
  t,
  position,
  rotation = [0, 0, 0],
  length = 6,
  radius = 1.2,
  top = 0.06,
  color = "#cfeeff",
  opacity = 0.25,
}) => {
  const geo = useMemo(() => {
    const g = new THREE.CylinderGeometry(top, radius, length, 64, 1, true);
    g.translate(0, -length / 2, 0);
    return g;
  }, [length, radius, top]);
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: SHAFT_VERT,
        fragmentShader: SHAFT_FRAG,
        uniforms: { uColor: { value: new THREE.Color() }, uA: { value: 0 }, uTime: { value: 0 } },
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide,
        blending: THREE.CustomBlending,
        blendSrc: THREE.OneFactor,
        blendDst: THREE.OneFactor,
      }),
    [],
  );
  (mat.uniforms.uColor.value as THREE.Color).set(color);
  mat.uniforms.uA.value = opacity;
  mat.uniforms.uTime.value = t;
  return <mesh geometry={geo} material={mat} position={position} rotation={rotation} frustumCulled={false} />;
};

// ---------------------------------------------------------------------------------------------
// Additive glow that always faces the camera.

const GLOW_VERT = /* glsl */ `
varying vec2 vUv; uniform float uScale;
void main(){ vUv = uv; vec4 mv = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0); mv.xy += position.xy * uScale; gl_Position = projectionMatrix * mv; }`;
const GLOW_FRAG = /* glsl */ `
uniform vec3 uColor; uniform float uA; uniform float uCore; varying vec2 vUv;
void main(){ float d = length(vUv - 0.5) * 2.0; float g = exp(-d * d * 4.0) * 0.6 + exp(-d * 12.0) * uCore; g *= smoothstep(1.0, 0.7, d);
  gl_FragColor = vec4(uColor * g * uA, 0.0); }`;

/** `depthTest={false}` keeps a big glow from being cut by a floor or a wall it overlaps (a hard straight edge). */
export const Glow: React.FC<{ position?: [number, number, number]; scale?: number; color?: THREE.ColorRepresentation; opacity?: number; core?: number; renderOrder?: number; depthTest?: boolean }> = ({ position = [0, 0, 0], scale = 1, color = "#9fdcff", opacity = 1, core = 1, renderOrder, depthTest = true }) => {
  const geo = useMemo(() => new THREE.PlaneGeometry(1, 1), []);
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: GLOW_VERT,
        fragmentShader: GLOW_FRAG,
        uniforms: { uColor: { value: new THREE.Color() }, uA: { value: 1 }, uScale: { value: 1 }, uCore: { value: 1 } },
        transparent: true,
        depthWrite: false,
        blending: THREE.CustomBlending,
        blendSrc: THREE.OneFactor,
        blendDst: THREE.OneFactor,
      }),
    [],
  );
  (mat.uniforms.uColor.value as THREE.Color).set(color);
  mat.uniforms.uA.value = opacity;
  mat.uniforms.uScale.value = scale;
  mat.uniforms.uCore.value = core;
  mat.depthTest = depthTest;
  return <mesh geometry={geo} material={mat} position={position} frustumCulled={false} renderOrder={renderOrder} />;
};

// ---------------------------------------------------------------------------------------------
// Broadcast waves: soft rings of light leaving a point, facing the camera. Each ring is emitted at one of
// `at` (scene seconds), eases out to `reach` and thins away as it goes.

const WAVE_FRAG = /* glsl */ `
uniform vec3 uColor; uniform float uA; uniform float uR[6]; uniform float uW[6]; varying vec2 vUv;
void main(){
  float d = length(vUv - 0.5) * 2.0;
  float g = 0.0;
  // a crisp ring in a faint halo, widening a little as it travels
  for (int i = 0; i < 6; i++) { float x = d - uR[i]; float q = x / (0.003 + 0.007 * uR[i]); float hq = x / (0.02 + 0.03 * uR[i]); g += (exp(-q * q) + 0.18 * exp(-hq * hq)) * uW[i]; }
  gl_FragColor = vec4(uColor * g * uA, 0.0);
}`;

export const Waves: React.FC<{ t: number; at: number[]; position: [number, number, number]; reach?: number; life?: number; color?: THREE.ColorRepresentation; opacity?: number; renderOrder?: number }> = ({ t, at, position, reach = 4, life = 2.2, color = "#ffd08a", opacity = 1, renderOrder }) => {
  const geo = useMemo(() => new THREE.PlaneGeometry(1, 1), []);
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: GLOW_VERT,
        fragmentShader: WAVE_FRAG,
        uniforms: { uColor: { value: new THREE.Color() }, uA: { value: 1 }, uScale: { value: 1 }, uR: { value: new Array(6).fill(0) }, uW: { value: new Array(6).fill(0) } },
        transparent: true,
        depthWrite: false,
        blending: THREE.CustomBlending,
        blendSrc: THREE.OneFactor,
        blendDst: THREE.OneFactor,
      }),
    [],
  );
  const r = mat.uniforms.uR.value as number[];
  const w = mat.uniforms.uW.value as number[];
  for (let i = 0; i < 6; i++) {
    const age = i < at.length ? t - at[i] : -1;
    const p = clamp01(age / life);
    r[i] = 0.04 + 0.92 * (1 - Math.pow(1 - p, 2.4));
    // a few frames of attack, then the ring fades as it spreads
    w[i] = age > 0 && age < life ? clamp01(age / 0.08) * Math.pow(1 - p, 1.6) : 0;
  }
  (mat.uniforms.uColor.value as THREE.Color).set(color);
  mat.uniforms.uA.value = opacity;
  mat.uniforms.uScale.value = reach * 2;
  return <mesh geometry={geo} material={mat} position={position} frustumCulled={false} renderOrder={renderOrder} />;
};

// ---------------------------------------------------------------------------------------------
// Polished dark floor: a true planar reflection (three's Reflector) drawn with a wet-floor blur
// (long vertical streaks, short horizontal), fading with distance from the camera.

const MIRROR_VERT = /* glsl */ `
uniform mat4 textureMatrix; varying vec4 vUv; varying vec3 vW;
void main(){ vUv = textureMatrix * vec4(position, 1.0); vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const MIRROR_FRAG = /* glsl */ `
uniform vec3 color; uniform sampler2D tDiffuse; uniform float uStrength; uniform vec2 uBlur; uniform float uFade; uniform vec3 uBase; uniform float uA; uniform vec3 uHaze; uniform vec2 uHazeRange;
varying vec4 vUv; varying vec3 vW;
float hh(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void main(){
  vec2 uv = vUv.xy / vUv.w;
  float dist = length(cameraPosition.xz - vW.xz);
  vec2 b = uBlur * (0.6 + 0.4 * clamp(dist / 8.0, 0.0, 2.0));
  vec3 acc = vec3(0.0); float ws = 0.0;
  for (int i = -7; i <= 7; i++) {
    float f = float(i); float w = exp(-f * f / 24.0);
    acc += texture2D(tDiffuse, uv + vec2(0.0, f * b.y)).rgb * w; ws += w;
    acc += texture2D(tDiffuse, uv + vec2(f * b.x, f * b.y * 0.35)).rgb * w * 0.5; ws += w * 0.5;
  }
  vec3 refl = acc / ws * color * uStrength;
  float fade = exp(-dist / uFade);
  float grain = 0.94 + 0.06 * hh(floor(vW.xz * 40.0));
  vec3 col = (uBase + refl * fade) * grain;
  // far floor melts into the horizon's haze, so the horizon is a glow rather than an edge
  col = mix(col, uHaze, smoothstep(uHazeRange.x, uHazeRange.y, dist));
  gl_FragColor = vec4(col, uA);
}`;

export const MirrorFloor: React.FC<{ y?: number; size?: number; strength?: number; blur?: [number, number]; fade?: number; base?: THREE.ColorRepresentation; tint?: THREE.ColorRepresentation; opacity?: number; res?: number; haze?: THREE.ColorRepresentation; hazeRange?: [number, number] }> = ({
  y = 0,
  size = 200,
  strength = 0.55,
  blur = [0.0025, 0.006],
  fade = 14,
  base = "#020408",
  tint = "#ffffff",
  opacity = 1,
  res = 1024,
  haze = "#000000",
  hazeRange = [1e5, 2e5],
}) => {
  const mirror = useMemo(() => {
    const geo = new THREE.PlaneGeometry(size, size);
    const r = new Reflector(geo, {
      textureWidth: res,
      textureHeight: Math.round(res * 0.5625),
      color: 0xffffff,
      multisample: 4,
      shader: {
        name: "MirrorFloor",
        uniforms: { color: { value: null }, tDiffuse: { value: null }, textureMatrix: { value: null }, uStrength: { value: 0.5 }, uBlur: { value: new THREE.Vector2() }, uFade: { value: 14 }, uBase: { value: new THREE.Color() }, uA: { value: 1 }, uHaze: { value: new THREE.Color() }, uHazeRange: { value: new THREE.Vector2(1e5, 2e5) } },
        vertexShader: MIRROR_VERT,
        fragmentShader: MIRROR_FRAG,
      },
    });
    r.rotation.x = -Math.PI / 2;
    // the mirror camera is cloned from the scene camera; keep it on layer 0 so anything placed on
    // other layers (e.g. a photograph rebuilt in depth) is never reflected
    const before = r.onBeforeRender;
    const self = r as unknown as { _getReflectionCamera: (c: THREE.Camera) => THREE.Camera };
    r.onBeforeRender = function (renderer, scene, camera, ...rest) {
      self._getReflectionCamera(camera).layers.mask = 1;
      before.call(this, renderer, scene, camera, ...rest);
    };
    return r;
  }, [size, res]);
  useEffect(() => () => mirror.dispose(), [mirror]);
  const m = mirror.material as THREE.ShaderMaterial;
  m.uniforms.uStrength.value = strength;
  (m.uniforms.uBlur.value as THREE.Vector2).set(...blur);
  m.uniforms.uFade.value = fade;
  (m.uniforms.uBase.value as THREE.Color).set(base);
  (m.uniforms.color.value as THREE.Color).set(tint);
  m.uniforms.uA.value = opacity;
  // while fading in it must not hide what is behind it
  m.transparent = opacity < 0.999;
  m.depthWrite = opacity >= 0.999;
  (m.uniforms.uHaze.value as THREE.Color).set(haze);
  (m.uniforms.uHazeRange.value as THREE.Vector2).set(...hazeRange);
  mirror.position.y = y;
  return <primitive object={mirror} />;
};

// ---------------------------------------------------------------------------------------------
// Beams of light: a camera-facing ribbon along a segment, drawn on from the start.

const BEAM_VERT = /* glsl */ `
uniform vec3 uA; uniform vec3 uB; uniform float uWidth; varying vec2 vUv;
void main(){
  vUv = uv;
  vec3 p = mix(uA, uB, uv.x);
  vec3 dir = normalize(uB - uA);
  vec3 toCam = normalize(cameraPosition - p);
  vec3 side = normalize(cross(dir, toCam));
  p += side * (uv.y - 0.5) * uWidth;
  gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0);
}`;
const BEAM_FRAG = /* glsl */ `
uniform vec3 uColor; uniform float uDraw; uniform float uOp; uniform float uTime; varying vec2 vUv;
void main(){
  float across = abs(vUv.y - 0.5) * 2.0;
  float core = exp(-across * across * 60.0) * 1.6 + exp(-across * across * 6.0) * 0.35;
  float head = smoothstep(uDraw, uDraw - 0.02, vUv.x);
  float pulse = 1.0 + 0.25 * sin(vUv.x * 40.0 - uTime * 18.0);
  float tip = exp(-((vUv.x - uDraw) * 40.0) * ((vUv.x - uDraw) * 40.0)) * 2.5;
  vec3 col = uColor * (core * pulse * head + tip * core) * uOp;
  gl_FragColor = vec4(col, 0.0);
}`;

export const Ray: React.FC<{ a: [number, number, number]; b: [number, number, number]; color: THREE.ColorRepresentation; draw: number; opacity?: number; width?: number; t: number }> = ({ a, b, color, draw, opacity = 1, width = 0.12, t }) => {
  const geo = useMemo(() => new THREE.PlaneGeometry(1, 1, 64, 1).translate(0.5, 0.5, 0), []);
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: BEAM_VERT,
        fragmentShader: BEAM_FRAG,
        uniforms: { uA: { value: new THREE.Vector3() }, uB: { value: new THREE.Vector3() }, uWidth: { value: 0.1 }, uColor: { value: new THREE.Color() }, uDraw: { value: 0 }, uOp: { value: 1 }, uTime: { value: 0 } },
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide,
        blending: THREE.CustomBlending,
        blendSrc: THREE.OneFactor,
        blendDst: THREE.OneFactor,
      }),
    [],
  );
  mat.uniforms.uA.value.set(...a);
  mat.uniforms.uB.value.set(...b);
  mat.uniforms.uWidth.value = width;
  (mat.uniforms.uColor.value as THREE.Color).set(color);
  mat.uniforms.uDraw.value = draw;
  mat.uniforms.uTime.value = t;
  mat.uniforms.uOp.value = opacity;
  return draw > 0 ? <mesh geometry={geo} material={mat} frustumCulled={false} /> : null;
};

