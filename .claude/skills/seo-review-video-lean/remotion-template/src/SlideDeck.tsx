import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { Scene } from "./Scene";
import type { SlideDeckProps } from "./schema";

export const SlideDeck: React.FC<SlideDeckProps> = ({ scenes }) => {
  if (!scenes || scenes.length === 0) {
    return (
      <AbsoluteFill
        style={{
          background: "#111",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ color: "#fff", fontSize: 48, fontFamily: "sans-serif" }}>
          No scenes loaded
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ background: "#0f0f12" }}>
      <Series>
        {scenes.map((scene) => (
          <Series.Sequence
            key={scene.id}
            durationInFrames={scene.durationInFrames}
          >
            <Scene {...scene} />
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
