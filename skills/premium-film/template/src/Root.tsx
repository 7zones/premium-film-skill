import "./index.css";
import React from "react";
import { AbsoluteFill, Composition, Folder } from "remotion";
import { Film, type FilmProps } from "./film/Film";
import { SCENE_COMPONENTS } from "./film/scenes";
import { filmDuration } from "./film/voices";
import { FPS, POST, PRE, SCENE_ORDER, SCENES, type SceneKey, filmLength } from "./film/timeline";
import { LANGS, MASTER, type Lang } from "./film/script";
import { Thumb } from "./film/Thumb";
import { SceneClock } from "./lib/anim";
import { FontGate } from "./lib/FontGate";
import { GradeDefs } from "./components/Grade";
import { Finish } from "./components/Finish";
import { C } from "./theme";

/** One scene on its own, with its pre- and post-roll, for fast review in the studio and for preview renders. */
const Solo: React.FC<{ scene: SceneKey; lang: Lang }> = ({ scene, lang }) => {
  const S = SCENE_COMPONENTS[scene];
  const pre = SCENE_ORDER.indexOf(scene) === 0 ? 0 : PRE;
  return (
    <AbsoluteFill style={{ background: C.void }}>
      <GradeDefs />
      <FontGate>
        <SceneClock offset={pre}>
          <S lang={lang} />
        </SceneClock>
      </FontGate>
      <Finish />
    </AbsoluteFill>
  );
};

/** Each cut runs exactly as long as its narration needs (a voice version may be longer or shorter). */
const byCut = ({ props }: { props: FilmProps }) => ({ durationInFrames: Math.round(filmDuration(props.voice, props.lang) * FPS) });

export const RemotionRoot: React.FC = () => (
  <>
    {/* masters: 1080p60, one per language (Film-en, Film-de, …) */}
    {LANGS.map((l) => (
      <Composition key={l} id={`Film-${l}`} component={Film} durationInFrames={Math.round(filmLength(l) * FPS)} fps={FPS} width={1920} height={1080} defaultProps={{ lang: l, withAudio: true } as FilmProps} calculateMetadata={byCut} />
    ))}
    {/* a 30 fps draft for quick review renders (tools/preview.sh) */}
    <Composition id="FilmDraft" component={Film} durationInFrames={Math.round(filmLength(MASTER) * 30)} fps={30} width={1920} height={1080} defaultProps={{ lang: MASTER, withAudio: false } as FilmProps} calculateMetadata={({ props }) => ({ durationInFrames: Math.round(filmDuration(props.voice, props.lang) * 30) })} />
    <Folder name="Scenes">
      {SCENE_ORDER.map((k, i) => (
        <Composition
          key={k}
          id={`S-${k}`}
          component={Solo}
          durationInFrames={Math.round((SCENES[k].end - SCENES[k].start + (i === 0 ? 0 : PRE) + POST) * 30)}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ scene: k, lang: MASTER as Lang }}
        />
      ))}
    </Folder>
    {LANGS.map((l) => (
      <Composition key={l} id={`Thumb-${l}`} component={Thumb} durationInFrames={1} fps={30} width={1920} height={1080} defaultProps={{ lang: l as Lang }} />
    ))}
  </>
);
