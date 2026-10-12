import React from "react";
import { AbsoluteFill, Html5Audio, Sequence, getStaticFiles, staticFile, useVideoConfig } from "remotion";
import { SceneClock } from "../lib/anim";
import { FontGate } from "../lib/FontGate";
import { CaptionedProvider, CaptionTrack } from "../components/Captions";
import { GradeDefs } from "../components/Grade";
import { Finish } from "../components/Finish";
import { C } from "../theme";
import type { Lang } from "./script";
import { POST, PRE, SCENE_ORDER, SCENES_OF } from "./timeline";
import { SCENE_COMPONENTS } from "./scenes";
import { voiceClock } from "./voices";

/**
 * `captions`: the captioned cut (subtitles burned in; low graphics make room, duplicated text hides).
 * `voice`: a version narrated by another voice (src/film/voices.ts); the whole film follows its timing.
 * `withAudio`: plays public/audio/mix-<lang>[-<voice>].wav when it exists. Finals are rendered silent and the mix
 * is muxed in afterwards (tools/release.sh).
 */
export type FilmProps = { lang: Lang; withAudio: boolean; captions?: boolean; voice?: string };

export const mixFile = (lang: Lang, voice?: string) => `audio/mix-${lang}${voice ? `-${voice}` : ""}.wav`;

export const Film: React.FC<FilmProps> = ({ lang, withAudio, captions = false, voice }) => {
  const { fps } = useVideoConfig();
  const clock = voiceClock(voice, lang);
  const T = clock ? clock.toNew : (t: number) => t;
  const mix = mixFile(lang, voice);
  const hasMix = withAudio && getStaticFiles().some((f) => f.name === mix);
  return (
    <AbsoluteFill style={{ background: C.void }}>
      <GradeDefs />
      <FontGate>
        <CaptionedProvider value={captions}>
          {SCENE_ORDER.map((key, i) => {
            const s = SCENES_OF[lang][key];
            const from = Math.max(0, Math.round(T(s.start - (i === 0 ? 0 : PRE)) * fps));
            const to = Math.round(T(s.end + POST) * fps);
            const Scene = SCENE_COMPONENTS[key];
            return (
              <Sequence key={key} from={from} durationInFrames={to - from} name={key} layout="none">
                <AbsoluteFill>
                  <SceneClock offset={s.start - from / fps} warp={clock ? { from: from / fps, start: s.start, toOld: clock.toOld } : undefined}>
                    <Scene lang={lang} />
                  </SceneClock>
                </AbsoluteFill>
              </Sequence>
            );
          })}
        </CaptionedProvider>
      </FontGate>
      <Finish />
      {captions ? <CaptionTrack lang={lang} voice={voice} /> : null}
      {hasMix ? <Html5Audio src={staticFile(mix)} /> : null}
    </AbsoluteFill>
  );
};
