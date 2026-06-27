import { CalculateMetadataFunction } from "remotion";
import type { SlideDeckProps } from "./schema";

const FPS = 30;

export const calculateSlideDeckMetadata: CalculateMetadataFunction<
  SlideDeckProps
> = async ({ props }) => {
  if (!props.scenes || props.scenes.length === 0) {
    return { durationInFrames: 300 };
  }
  const totalFrames = props.scenes.reduce(
    (sum, s) => sum + s.durationInFrames,
    0
  );
  return {
    durationInFrames: Math.max(totalFrames, FPS),
    fps: FPS,
    width: 1920,
    height: 1080,
  };
};
