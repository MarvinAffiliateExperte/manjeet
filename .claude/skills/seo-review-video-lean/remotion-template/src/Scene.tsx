import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from "remotion";
import { loadFont as loadBarlow } from "@remotion/google-fonts/BarlowCondensed";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import type { SceneProps } from "./schema";

const { fontFamily: headlineFont } = loadBarlow("normal", {
  weights: ["700", "800", "900"],
});
const { fontFamily: bodyFont } = loadInter("normal", {
  weights: ["500", "600", "700"],
});

const RED = "#ff3020";
const INK = "#0f0f12";

/* ---------- Studio gradient background ---------- */
const StudioBackground: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(circle at 30% 20%, #f5f5f7 0%, #e8e8ec 40%, #d8d8df 100%)",
    }}
  />
);

/* ---------- Camera viewfinder HUD ---------- */
const ViewfinderHUD: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sec = frame / fps;
  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(Math.floor(sec % 60)).padStart(2, "0");
  const ff = String(Math.floor((sec % 1) * fps)).padStart(2, "0");
  const pulse = (Math.sin(frame * 0.25) + 1) / 2;
  const bracketColor = "rgba(255,255,255,0.85)";
  const bracket: React.CSSProperties = {
    position: "absolute",
    width: 60,
    height: 60,
    borderColor: bracketColor,
    borderStyle: "solid",
  };
  return (
    <AbsoluteFill
      style={{ pointerEvents: "none", zIndex: 100, mixBlendMode: "difference" }}
    >
      <div style={{ ...bracket, top: 40, left: 40, borderWidth: "4px 0 0 4px" }} />
      <div style={{ ...bracket, top: 40, right: 40, borderWidth: "4px 4px 0 0" }} />
      <div style={{ ...bracket, bottom: 40, left: 40, borderWidth: "0 0 4px 4px" }} />
      <div style={{ ...bracket, bottom: 40, right: 40, borderWidth: "0 4px 4px 0" }} />
      <div
        style={{
          position: "absolute",
          top: 48,
          left: 120,
          display: "flex",
          alignItems: "center",
          gap: 12,
          color: "rgba(255,255,255,0.95)",
          fontFamily: bodyFont,
          fontSize: 24,
          fontWeight: 700,
          letterSpacing: 2,
        }}
      >
        <div
          style={{
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: `rgba(235,60,60,${0.6 + pulse * 0.4})`,
            boxShadow: `0 0 20px rgba(235,60,60,${0.4 + pulse * 0.4})`,
          }}
        />
        REC
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 48,
          left: 120,
          color: "rgba(255,255,255,0.95)",
          fontFamily: bodyFont,
          fontSize: 28,
          fontWeight: 700,
          letterSpacing: 3,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {mm}:{ss}:{ff}
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 48,
          right: 120,
          color: "rgba(255,255,255,0.95)",
          fontFamily: bodyFont,
          fontSize: 26,
          fontWeight: 800,
          letterSpacing: 3,
          border: "3px solid rgba(255,255,255,0.85)",
          padding: "4px 14px",
          borderRadius: 6,
        }}
      >
        4K
      </div>
    </AbsoluteFill>
  );
};

/* ---------- Big bold title card ---------- */
const BigTitleCard: React.FC<{
  title: string;
  subtitle?: string;
  broll?: string;
  screenshot?: string;
}> = ({ title, subtitle, broll, screenshot }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const appear = spring({
    frame: frame - fps * 0.15,
    fps,
    config: { damping: 170, stiffness: 200 },
    durationInFrames: Math.floor(fps * 0.55),
  });
  const scale = interpolate(appear, [0, 1], [0.92, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(appear, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bgScale = interpolate(frame, [0, durationInFrames], [1.05, 1.14], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ background: "#060608", overflow: "hidden" }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${bgScale})`,
          transformOrigin: "center center",
          opacity: 0.55,
        }}
      >
        {broll ? (
          <OffthreadVideo
            src={staticFile(broll)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            muted
          />
        ) : screenshot ? (
          <Img
            src={staticFile(screenshot)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              background:
                "radial-gradient(ellipse at 30% 30%, #1a1a24 0%, #0a0a0f 70%, #050508 100%)",
            }}
          />
        )}
      </div>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.35) 40%, rgba(0,0,0,0.7) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: 120,
          right: 120,
          transform: `translateY(-50%) scale(${scale})`,
          opacity,
          textAlign: "center",
          zIndex: 30,
        }}
      >
        <div
          style={{
            display: "inline-block",
            background: INK,
            color: "#fff",
            fontFamily: headlineFont,
            fontWeight: 900,
            fontSize: 140,
            lineHeight: 0.95,
            letterSpacing: 1,
            textTransform: "uppercase",
            padding: "32px 60px",
            borderLeft: `14px solid ${RED}`,
            boxShadow: "0 24px 60px rgba(0,0,0,0.6)",
            maxWidth: 1600,
          }}
        >
          {title}
        </div>
        {subtitle && (
          <div
            style={{
              marginTop: 28,
              display: "inline-block",
              background: "rgba(255,255,255,0.97)",
              color: "#1a1a1f",
              fontFamily: bodyFont,
              fontWeight: 600,
              fontSize: 44,
              padding: "18px 32px",
              boxShadow: "0 12px 30px rgba(0,0,0,0.35)",
            }}
          >
            {subtitle}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

/* ---------- Big centered red rotated label ---------- */
const BigLabel: React.FC<{ label: string }> = ({ label }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({
    frame: frame - fps * 0.25,
    fps,
    config: { damping: 150, stiffness: 220 },
    durationInFrames: Math.floor(fps * 0.5),
  });
  const scale = interpolate(pop, [0, 1], [0.8, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(pop, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse at 50% 50%, #241010 0%, #0a0406 80%)",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: 0,
          right: 0,
          textAlign: "center",
          transform: `translateY(-50%) scale(${scale})`,
          opacity,
          zIndex: 60,
        }}
      >
        <div
          style={{
            display: "inline-block",
            background: RED,
            color: "#fff",
            fontFamily: headlineFont,
            fontWeight: 900,
            fontSize: 180,
            lineHeight: 0.95,
            letterSpacing: 2,
            textTransform: "uppercase",
            padding: "36px 70px",
            boxShadow: "0 30px 80px rgba(0,0,0,0.6)",
            transform: "rotate(-2deg)",
          }}
        >
          {label}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- Product full-frame ---------- */
const ProductFull: React.FC<{ broll?: string; screenshot?: string }> = ({
  broll,
  screenshot,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [1.05, 1.14], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ background: "#0a0a0c", overflow: "hidden" }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      >
        {broll ? (
          <OffthreadVideo
            src={staticFile(broll)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            muted
          />
        ) : screenshot ? (
          <Img
            src={staticFile(screenshot)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : null}
      </div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.25) 0%, transparent 40%, rgba(0,0,0,0.55) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

/* ---------- TitleBand ---------- */
const TitleBand: React.FC<{
  title: string;
  subtitle?: string;
  position?: "top-center" | "bottom-left";
}> = ({ title, subtitle, position = "top-center" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({
    frame: frame - fps * 0.2,
    fps,
    config: { damping: 170 },
    durationInFrames: Math.floor(fps * 0.5),
  });
  const translateY = interpolate(appear, [0, 1], [30, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(appear, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const posStyle: React.CSSProperties =
    position === "top-center"
      ? {
          top: 90,
          left: "50%",
          transform: `translate(-50%, ${translateY}px)`,
          textAlign: "center",
        }
      : {
          bottom: 140,
          left: 120,
          transform: `translateY(${translateY}px)`,
        };
  return (
    <div
      style={{
        position: "absolute",
        opacity,
        zIndex: 50,
        ...posStyle,
      }}
    >
      <div
        style={{
          display: "inline-block",
          background: INK,
          color: "#fff",
          fontFamily: headlineFont,
          fontWeight: 900,
          fontSize: 72,
          lineHeight: 1,
          letterSpacing: 1,
          textTransform: "uppercase",
          padding: "22px 36px",
          borderLeft: `10px solid ${RED}`,
          boxShadow: "0 14px 40px rgba(0,0,0,0.4)",
        }}
      >
        {title}
      </div>
      {subtitle && (
        <div
          style={{
            marginTop: 14,
            display: "inline-block",
            background: "rgba(255,255,255,0.97)",
            color: "#1a1a1f",
            fontFamily: bodyFont,
            fontWeight: 600,
            fontSize: 32,
            padding: "12px 24px",
            boxShadow: "0 8px 20px rgba(0,0,0,0.25)",
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};

/* ---------- Screenshot burst ---------- */
const ScreenshotBurst: React.FC<{ screenshots: string[] }> = ({
  screenshots,
}) => {
  const { durationInFrames } = useVideoConfig();
  const per = Math.floor(durationInFrames / screenshots.length);
  return (
    <AbsoluteFill style={{ background: "#0a0a0c" }}>
      {screenshots.map((src, i) => (
        <Sequence key={i} from={i * per} durationInFrames={per + 4}>
          <BurstShot src={src} index={i} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const BurstShot: React.FC<{ src: string; index: number }> = ({ src, index }) => {
  const frame = useCurrentFrame();
  const appear = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: "clamp",
  });
  const scale = interpolate(frame, [0, 120], [1.04, 1.12], {
    extrapolateRight: "clamp",
  });
  const panX = index % 2 === 0 ? 0 : 30;
  return (
    <AbsoluteFill
      style={{ opacity: appear, background: "#0a0a0c", overflow: "hidden" }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${scale}) translateX(${panX}px)`,
        }}
      >
        <Img
          src={staticFile(src)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.3) 0%, transparent 35%, rgba(0,0,0,0.55) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

/* ---------- StatCard ---------- */
const StatCard: React.FC<{
  title: string;
  subtitle?: string;
  broll?: string;
  screenshot?: string;
}> = ({ title, subtitle, broll, screenshot }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({
    frame: frame - fps * 0.2,
    fps,
    config: { damping: 170 },
    durationInFrames: Math.floor(fps * 0.55),
  });
  const translateX = interpolate(appear, [0, 1], [-80, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(appear, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill>
      <StudioBackground />
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: "48%",
          height: "100%",
          overflow: "hidden",
        }}
      >
        {broll ? (
          <OffthreadVideo
            src={staticFile(broll)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            muted
          />
        ) : screenshot ? (
          <Img
            src={staticFile(screenshot)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : null}
      </div>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "55%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          paddingRight: 80,
          opacity,
          transform: `translateX(${translateX}px)`,
          zIndex: 30,
        }}
      >
        <div style={{ textAlign: "right", maxWidth: 900 }}>
          <div
            style={{
              color: INK,
              fontFamily: headlineFont,
              fontWeight: 900,
              fontSize: 130,
              lineHeight: 0.95,
              letterSpacing: 1,
              textTransform: "uppercase",
            }}
          >
            {title}
          </div>
          {subtitle && (
            <div
              style={{
                marginTop: 24,
                color: RED,
                fontFamily: bodyFont,
                fontWeight: 700,
                fontSize: 44,
                lineHeight: 1.2,
              }}
            >
              {subtitle}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- VsCard ---------- */
const VsCard: React.FC<{
  title: string;
  bullets: string[];
  broll?: string;
  screenshot?: string;
}> = ({ title, bullets, broll, screenshot }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <StudioBackground />
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: "42%",
          height: "100%",
          overflow: "hidden",
        }}
      >
        {broll ? (
          <OffthreadVideo
            src={staticFile(broll)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            muted
          />
        ) : screenshot ? (
          <Img
            src={staticFile(screenshot)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : null}
      </div>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "58%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          paddingLeft: 120,
          zIndex: 30,
        }}
      >
        <div
          style={{
            color: INK,
            fontFamily: headlineFont,
            fontWeight: 900,
            fontSize: 88,
            lineHeight: 1,
            letterSpacing: 1,
            textTransform: "uppercase",
            marginBottom: 40,
            borderLeft: `10px solid ${RED}`,
            paddingLeft: 30,
          }}
        >
          {title}
        </div>
        {bullets.map((b, i) => {
          const start = fps * (0.6 + i * 0.35);
          const appear = spring({
            frame: frame - start,
            fps,
            config: { damping: 170 },
            durationInFrames: Math.floor(fps * 0.5),
          });
          const tx = interpolate(appear, [0, 1], [-40, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const op = interpolate(appear, [0, 1], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const highlight = b.startsWith("★") || b.startsWith("*");
          const cleanText = b.replace(/^[★*]\s*/, "");
          return (
            <div
              key={i}
              style={{
                opacity: op,
                transform: `translateX(${tx}px)`,
                marginBottom: 24,
                background: highlight ? INK : "rgba(255,255,255,0.95)",
                color: highlight ? "#fff" : "#1a1a1f",
                fontFamily: bodyFont,
                fontWeight: 700,
                fontSize: 44,
                padding: "18px 30px",
                display: "inline-block",
                width: "fit-content",
                boxShadow: "0 10px 26px rgba(0,0,0,0.18)",
                borderLeft: highlight
                  ? `10px solid ${RED}`
                  : "10px solid #888",
              }}
            >
              {cleanText}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ---------- RedditCard ---------- */
const RedditCard: React.FC<{
  image: string;
  quote?: string;
  author?: string;
  upvotes?: number;
  subreddit?: string;
  titleCard: string;
}> = ({ image, quote, author, upvotes, subreddit, titleCard }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appear = spring({
    frame,
    fps,
    config: { damping: 180 },
    durationInFrames: Math.floor(fps * 0.5),
  });
  const translateX = interpolate(appear, [0, 1], [-40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(appear, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const quoteAppear = spring({
    frame: frame - fps * 0.9,
    fps,
    config: { damping: 170 },
    durationInFrames: Math.floor(fps * 0.5),
  });
  const quoteOpacity = interpolate(quoteAppear, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const quoteY = interpolate(quoteAppear, [0, 1], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ background: "#0a0a0c" }}>
      <StudioBackground />
      <div
        style={{
          position: "absolute",
          top: 100,
          left: 80,
          width: 1120,
          maxHeight: 880,
          opacity,
          transform: `translateX(${translateX}px)`,
          borderRadius: 18,
          overflow: "hidden",
          boxShadow:
            "0 30px 70px rgba(0,0,0,0.35), 0 10px 25px rgba(0,0,0,0.22)",
          border: "4px solid #fff",
          background: "#fff",
        }}
      >
        <Img
          src={staticFile(image)}
          style={{
            width: "100%",
            height: "auto",
            display: "block",
            objectFit: "cover",
          }}
        />
      </div>
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 80,
          background: "#ff4500",
          color: "#fff",
          fontFamily: bodyFont,
          fontWeight: 800,
          fontSize: 22,
          padding: "8px 18px",
          borderRadius: 999,
          letterSpacing: 1,
          zIndex: 10,
          boxShadow: "0 6px 16px rgba(255,69,0,0.4)",
        }}
      >
        REDDIT • {subreddit ? `r/${subreddit}` : "TESTIMONIAL"}
        {upvotes ? ` • ↑ ${upvotes}` : ""}
      </div>
      {quote && (
        <div
          style={{
            position: "absolute",
            top: 180,
            right: 60,
            width: 640,
            opacity: quoteOpacity,
            transform: `translateY(${quoteY}px)`,
            zIndex: 30,
          }}
        >
          <div
            style={{
              background: INK,
              color: "#fff",
              fontFamily: headlineFont,
              fontWeight: 800,
              fontSize: 52,
              lineHeight: 1.15,
              padding: "32px 36px",
              borderLeft: `12px solid ${RED}`,
              boxShadow: "0 16px 40px rgba(0,0,0,0.4)",
            }}
          >
            "{quote}"
          </div>
          {author && (
            <div
              style={{
                marginTop: 16,
                color: INK,
                fontFamily: bodyFont,
                fontWeight: 700,
                fontSize: 30,
                letterSpacing: 1,
                textAlign: "right",
              }}
            >
              — u/{author}
            </div>
          )}
        </div>
      )}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          right: 60,
          zIndex: 40,
        }}
      >
        <div
          style={{
            background: INK,
            color: "#fff",
            fontFamily: headlineFont,
            fontWeight: 900,
            fontSize: 56,
            padding: "18px 28px",
            borderLeft: `8px solid ${RED}`,
            textTransform: "uppercase",
            letterSpacing: 1,
            boxShadow: "0 14px 40px rgba(0,0,0,0.35)",
          }}
        >
          {titleCard}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- TourFull — authenticated tour MP4 full-frame ---------- */
const TourFull: React.FC<{
  tour: string;
  titleCard: string;
  subtitle?: string;
  tourStart?: number;
  tourEnd?: number;
}> = ({ tour, titleCard, subtitle, tourStart, tourEnd }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const labelAppear = spring({
    frame: frame - fps * 0.2,
    fps,
    config: { damping: 170, stiffness: 200 },
    durationInFrames: Math.floor(fps * 0.5),
  });
  const labelOpacity = interpolate(labelAppear, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const labelY = interpolate(labelAppear, [0, 1], [-20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ background: "#0a0a0c", overflow: "hidden" }}>
      {/* Tour video full-frame — no Ken Burns, the tour provides its own motion */}
      <OffthreadVideo
        src={staticFile(tour)}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
        muted
        startFrom={tourStart ? Math.floor(tourStart * fps) : undefined}
        endAt={tourEnd ? Math.floor(tourEnd * fps) : undefined}
      />
      {/* Top gradient for label readability */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 200,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.7) 0%, transparent 100%)",
          zIndex: 20,
        }}
      />
      {/* Bottom gradient for subtitle readability */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 200,
          background:
            "linear-gradient(0deg, rgba(0,0,0,0.7) 0%, transparent 100%)",
          zIndex: 20,
        }}
      />
      {/* Section label strip at top */}
      <div
        style={{
          position: "absolute",
          top: 40,
          left: 80,
          opacity: labelOpacity,
          transform: `translateY(${labelY}px)`,
          zIndex: 50,
        }}
      >
        <div
          style={{
            display: "inline-block",
            background: INK,
            color: "#fff",
            fontFamily: headlineFont,
            fontWeight: 900,
            fontSize: 56,
            lineHeight: 1,
            letterSpacing: 1,
            textTransform: "uppercase",
            padding: "16px 28px",
            borderLeft: `8px solid ${RED}`,
            boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
          }}
        >
          {titleCard}
        </div>
      </div>
      {/* Floating narration subtitle at bottom */}
      {subtitle && (
        <div
          style={{
            position: "absolute",
            bottom: 60,
            left: 120,
            right: 120,
            textAlign: "center",
            zIndex: 50,
          }}
        >
          <div
            style={{
              display: "inline-block",
              background: "rgba(15,15,18,0.85)",
              color: "#fff",
              fontFamily: bodyFont,
              fontWeight: 600,
              fontSize: 36,
              padding: "14px 28px",
              borderRadius: 8,
              boxShadow: "0 8px 20px rgba(0,0,0,0.4)",
              maxWidth: 1400,
            }}
          >
            {subtitle}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

/* ---------- Main Scene dispatcher ---------- */
export const Scene: React.FC<SceneProps> = (props) => {
  const {
    layout,
    audio,
    titleCard,
    subtitle,
    bullets,
    broll,
    screenshot,
    screenshots,
    reddit,
    tour,
    tourStart,
    tourEnd,
  } = props;

  return (
    <AbsoluteFill>
      <Audio src={staticFile(audio)} />

      {layout === "title-card" && (
        <>
          <BigTitleCard
            title={titleCard}
            subtitle={subtitle}
            broll={broll}
            screenshot={screenshot}
          />
          <ViewfinderHUD />
        </>
      )}

      {layout === "big-label" && (
        <>
          <BigLabel label={titleCard} />
          <ViewfinderHUD />
        </>
      )}

      {layout === "product-full" && (
        <>
          <ProductFull broll={broll} screenshot={screenshot} />
          <TitleBand title={titleCard} subtitle={subtitle} position="top-center" />
          <ViewfinderHUD />
        </>
      )}

      {layout === "screenshot-burst" && (
        <>
          <ScreenshotBurst screenshots={screenshots || []} />
          <TitleBand title={titleCard} subtitle={subtitle} position="top-center" />
          <ViewfinderHUD />
        </>
      )}

      {layout === "reddit-card" && reddit && (
        <>
          <RedditCard
            image={reddit.image}
            quote={reddit.quote}
            author={reddit.author}
            upvotes={reddit.upvotes}
            subreddit={reddit.subreddit}
            titleCard={titleCard}
          />
          <ViewfinderHUD />
        </>
      )}

      {layout === "stat-card" && (
        <>
          <StatCard
            title={titleCard}
            subtitle={subtitle}
            broll={broll}
            screenshot={screenshot}
          />
          <ViewfinderHUD />
        </>
      )}

      {layout === "vs-card" && (
        <>
          <VsCard
            title={titleCard}
            bullets={bullets || []}
            broll={broll}
            screenshot={screenshot}
          />
          <ViewfinderHUD />
        </>
      )}

      {layout === "tour-full" && tour && (
        <>
          <TourFull
            tour={tour}
            titleCard={titleCard}
            subtitle={subtitle}
            tourStart={tourStart}
            tourEnd={tourEnd}
          />
          <ViewfinderHUD />
        </>
      )}
    </AbsoluteFill>
  );
};
