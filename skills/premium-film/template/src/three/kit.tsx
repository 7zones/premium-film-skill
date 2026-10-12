import React, { useEffect, useLayoutEffect, useMemo } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

// Before the bloom, every pixel is clamped and any NaN/Inf zeroed: one NaN pixel (a pow() of a negative number
// that multisampling evaluated just outside a triangle) is smeared over the whole frame by the bloom and blacks it
// out, and a razor-sharp specular glint thousands of times too bright flares into a white blob for one frame.
const ClampShader = {
  uniforms: { tDiffuse: { value: null as THREE.Texture | null }, maxV: { value: 3.0 } },
  vertexShader: /* glsl */ `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse; uniform float maxV; varying vec2 vUv;
    void main() {
      vec4 c = texture2D(tDiffuse, vUv);
      vec3 rgb = c.rgb;
      if (any(isnan(rgb)) || any(isinf(rgb))) rgb = vec3(0.0);
      float m = max(max(rgb.r, rgb.g), rgb.b);
      if (m > maxV) rgb *= maxV / m;
      gl_FragColor = vec4(rgb, c.a);
    }`,
};

/**
 * Bloom through three's own EffectComposer (@react-three/postprocessing renders black under Remotion). Remotion
 * renders R3F with frameloop "never" and advances once per frame; a priority-1 frame callback makes the composer
 * the one that draws. `knee` softens the threshold so a fading light's glow fades with it instead of switching off.
 * Keep thin bright lines a few px wide (a 2-px line near the threshold blinks as it moves between pixels) and keep
 * white surfaces (logo plates) below the threshold.
 */
export const Bloom: React.FC<{ strength?: number; radius?: number; threshold?: number; knee?: number; maxV?: number; samples?: number }> = ({
  strength = 0.9,
  radius = 0.6,
  threshold = 0.12,
  knee = 0.01,
  maxV = 3,
  samples = 4,
}) => {
  const { gl, scene, camera, size } = useThree();
  const { composer, bloom, clamp } = useMemo(() => {
    const rt = new THREE.WebGLRenderTarget(size.width, size.height, { type: THREE.HalfFloatType, samples });
    const c = new EffectComposer(gl, rt);
    c.addPass(new RenderPass(scene, camera));
    const cl = new ShaderPass(ClampShader);
    c.addPass(cl);
    const b = new UnrealBloomPass(new THREE.Vector2(size.width, size.height), strength, radius, threshold);
    c.addPass(b);
    c.addPass(new OutputPass());
    return { composer: c, bloom: b, clamp: cl };
  }, [gl, scene, camera, size.width, size.height, samples]);
  bloom.strength = strength;
  bloom.radius = radius;
  bloom.threshold = threshold;
  bloom.highPassUniforms["smoothWidth"].value = knee;
  clamp.uniforms.maxV.value = maxV;
  useEffect(() => () => composer.dispose(), [composer]);
  useFrame(() => composer.render(), 1);
  return null;
};

/** Drives the default camera from props every frame (deterministic: derive the props from useTime()). */
export const CameraRig: React.FC<{ position: [number, number, number]; target?: [number, number, number]; fov?: number; roll?: number }> = ({ position, target = [0, 0, 0], fov, roll = 0 }) => {
  const { camera } = useThree();
  useLayoutEffect(() => {
    camera.position.set(...position);
    camera.up.set(Math.sin(roll), Math.cos(roll), 0);
    camera.lookAt(...target);
    if (fov && camera instanceof THREE.PerspectiveCamera && camera.fov !== fov) {
      camera.fov = fov;
      camera.updateProjectionMatrix();
    }
  });
  return null;
};

/** A soft studio environment for glass and metal reflections (metal renders black without an environment). */
export const StudioEnv: React.FC<{ intensity?: number }> = ({ intensity = 1 }) => {
  const { gl, scene } = useThree();
  useLayoutEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = env;
    scene.environmentIntensity = intensity;
    return () => {
      scene.environment = null;
      env.dispose();
      pmrem.dispose();
    };
  }, [gl, scene, intensity]);
  return null;
};
