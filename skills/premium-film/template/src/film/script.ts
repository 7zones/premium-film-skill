// Every word that appears on screen, in every language the film ships in. Scenes never hard-code text: they read
// TEXT[lang]. Keep product/module names identical to the product's own UI wording in each language, and write
// numbers the way each language writes them (en 2,400,000 / de 2.400.000 / fr 2 400 000).

// The film's languages (ISO 639-1 codes; the first is the master). To ship another cut, add its code here, then give
// every TEXT block below and every narration line in timeline.ts that language too — TypeScript flags any you miss.
export const LANGS = ["en"] as const;
export type Lang = (typeof LANGS)[number];
export const MASTER: Lang = LANGS[0];

// EXAMPLE CONTENT — replace with the film's own.
export const TEXT: Record<Lang, { opening: { lead: string; accent: string }; proof: { value: string; label: string; line: string }; closing: { name: string; accent: string; tagline: string; url: string } }> = {
  en: {
    opening: { lead: "Every signal.", accent: "One story." },
    proof: { value: "2,400,000+", label: "checks every month", line: "Faster, clearer, safer." },
    closing: { name: "Your", accent: "Brand", tagline: "Safe, every day.", url: "example.com" },
  },
};
