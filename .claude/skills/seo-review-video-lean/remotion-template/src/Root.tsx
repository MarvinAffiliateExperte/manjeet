import { Composition } from "remotion";
import { SlideDeck } from "./SlideDeck";
import { calculateSlideDeckMetadata } from "./calculate-metadata";
import { SlideDeckSchema } from "./schema";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SlideDeck"
        component={SlideDeck}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        schema={SlideDeckSchema}
        calculateMetadata={calculateSlideDeckMetadata}
        defaultProps={{
          scenes: [],
        }}
      />
    </>
  );
};
