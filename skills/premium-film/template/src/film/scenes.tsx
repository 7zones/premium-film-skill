import type React from "react";
import type { Lang } from "./script";
import type { SceneKey } from "./timeline";
import { Opening } from "./scenes/Opening";
import { Proof } from "./scenes/Proof";
import { Closing } from "./scenes/Closing";

/** One component per chapter, in timeline order. */
export const SCENE_COMPONENTS: Record<SceneKey, React.FC<{ lang: Lang }>> = {
  opening: Opening,
  proof: Proof,
  closing: Closing,
};
