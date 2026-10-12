import React from "react";

/**
 * The film's colour grade as SVG filters, so real photographs and designed elements share one look.
 * Tune the tables to the palette in theme.ts (each table maps input 0→1 to output; lift the first value for
 * tinted shadows, lower the last for soft highlights). Mount <GradeDefs/> once per composition and apply with
 * `filter: url(#grade-photo)`. Keep real people's photos clean: grade and vignette only, never glows or rims.
 */
export const GradeDefs: React.FC = () => (
  <svg width={0} height={0} style={{ position: "absolute" }} aria-hidden>
    <defs>
      {/* night plates: tinted shadows, restrained saturation, clean highlights */}
      <filter id="grade-night" colorInterpolationFilters="sRGB">
        <feColorMatrix type="saturate" values="0.82" />
        <feComponentTransfer>
          <feFuncR type="table" tableValues="0 0.07 0.3 0.6 0.88 0.98" />
          <feFuncG type="table" tableValues="0.02 0.12 0.36 0.66 0.91 1" />
          <feFuncB type="table" tableValues="0.04 0.16 0.39 0.66 0.89 0.97" />
        </feComponentTransfer>
      </filter>
      {/* real event photos pulled into the palette without losing skin tones */}
      <filter id="grade-photo" colorInterpolationFilters="sRGB">
        <feColorMatrix type="saturate" values="0.88" />
        <feComponentTransfer>
          <feFuncR type="table" tableValues="0.01 0.1 0.35 0.65 0.9 0.99" />
          <feFuncG type="table" tableValues="0.02 0.13 0.39 0.68 0.92 1" />
          <feFuncB type="table" tableValues="0.04 0.15 0.39 0.65 0.88 0.97" />
        </feComponentTransfer>
      </filter>
      {/* duotone for photos used as texture behind type */}
      <filter id="grade-mono" colorInterpolationFilters="sRGB">
        <feColorMatrix type="matrix" values="0.3 0.59 0.11 0 0  0.3 0.59 0.11 0 0  0.3 0.59 0.11 0 0  0 0 0 1 0" />
        <feComponentTransfer>
          <feFuncR type="table" tableValues="0.01 0.06 0.3 0.75" />
          <feFuncG type="table" tableValues="0.04 0.14 0.45 0.9" />
          <feFuncB type="table" tableValues="0.07 0.2 0.52 0.92" />
        </feComponentTransfer>
      </filter>
    </defs>
  </svg>
);

export type GradeName = "night" | "photo" | "mono" | "none";
export const gradeFilter = (g: GradeName) => (g === "none" ? undefined : `url(#grade-${g})`);
