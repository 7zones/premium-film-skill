import React, { useEffect, useState } from "react";
import { cancelRender, useDelayRender } from "remotion";
import { fontsLoaded } from "../theme";

let loaded = false;

/**
 * Renders nothing until every web font has loaded. The film measures text to lay itself out (measureText caches
 * its first answer) and paints canvases with these fonts, so nothing may run earlier: a render tab that measured
 * with fallback fonts places cursors, labels and titles differently from the others, and the picture jitters
 * between frames. Wrap the whole film (and every solo-scene composition) in it.
 */
export const FontGate: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [ready, setReady] = useState(loaded);
  const { delayRender, continueRender } = useDelayRender();
  const [handle] = useState(() => (loaded ? null : delayRender("Loading fonts")));
  useEffect(() => {
    if (ready) return;
    let alive = true;
    fontsLoaded()
      .then(() => {
        loaded = true;
        if (alive) setReady(true);
      })
      .catch((err) => cancelRender(err));
    return () => {
      alive = false;
    };
  }, [ready]);
  useEffect(() => {
    if (ready && handle !== null) continueRender(handle);
  }, [ready, handle, continueRender]);
  return ready ? <>{children}</> : null;
};
