import { Config } from "@remotion/cli/config";

Config.setRspack(true);
Config.setVideoImageFormat("png");
Config.setOverwriteOutput(true);
// WebGL through ANGLE: three.js scenes render the same in the studio and in headless renders.
Config.setChromiumOpenGlRenderer("angle");
// One tab. All tabs share the 4 GB of GPU memory Remotion gives Chrome; with several tabs holding full-frame
// canvases and WebGL, one tab can fall back to another drawing path and place centred text a pixel apart from
// the others, so titles flicker frame to frame. Per-chunk start-up dominates anyway: one tab is as fast.
Config.setConcurrency(1);
