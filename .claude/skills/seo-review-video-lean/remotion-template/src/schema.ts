import { z } from "zod";

/**
 * Scene layouts for SEO Review Video pipeline.
 *
 * 8 layouts (7 from product-review-voiceover + tour-full):
 * - title-card: full-bleed gradient/broll with giant bold centered title + subtitle
 * - big-label: fullscreen red rotated callout
 * - product-full: full-frame broll/screenshot + top-center title band
 * - screenshot-burst: 2-4 screenshot sequence + top-center title band
 * - reddit-card: Reddit thread screenshot + pull-quote (fills right column)
 * - stat-card: left giant stat + right media pane
 * - vs-card: bullet list left + media pane right
 * - tour-full: authenticated tour MP4 full-frame + section label + narration subtitle
 */
export const SceneSchema = z.object({
  id: z.string(),
  layout: z.enum([
    "title-card",
    "big-label",
    "product-full",
    "screenshot-burst",
    "reddit-card",
    "stat-card",
    "vs-card",
    "tour-full",
  ]),
  // Path to the TTS audio WAV (resolved via staticFile())
  audio: z.string(),
  durationInFrames: z.number(),
  titleCard: z.string(),
  subtitle: z.string().optional(),
  bullets: z.array(z.string()).optional(),
  broll: z.string().optional(),
  screenshot: z.string().optional(),
  screenshots: z.array(z.string()).optional(),
  reddit: z
    .object({
      image: z.string(),
      quote: z.string().optional(),
      author: z.string().optional(),
      upvotes: z.number().optional(),
      subreddit: z.string().optional(),
    })
    .optional(),
  // Tour-specific fields
  tour: z.string().optional(),
  tourStart: z.number().optional(),
  tourEnd: z.number().optional(),
});

export type SceneProps = z.infer<typeof SceneSchema>;

export const SlideDeckSchema = z.object({
  scenes: z.array(SceneSchema),
});

export type SlideDeckProps = z.infer<typeof SlideDeckSchema>;
