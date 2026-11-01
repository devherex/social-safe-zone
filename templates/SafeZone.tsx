// Remotion component: everything inside <SafeZone> stays in the safe area.
// Put full-bleed video/background OUTSIDE it, text/logos/CTAs INSIDE it.
// Set debug to see the guide while editing, then remove it before rendering.
import React from "react";
import { AbsoluteFill } from "remotion";
import { ZONES, ZonePreset } from "./zones";

export const SafeZone: React.FC<{
  preset: ZonePreset;
  debug?: boolean;
  children: React.ReactNode;
}> = ({ preset, debug, children }) => {
  const z = ZONES[preset];
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: z.safe.top,
          bottom: z.safe.bottom,
          left: z.safe.left,
          right: z.safe.right,
          outline: debug ? "3px solid #28e678" : undefined,
        }}
      >
        {children}
      </div>
      {debug &&
        z.avoid.map((a, i) => (
          <div key={i} style={{ position: "absolute", left: a.x, top: a.y, width: a.w, height: a.h, background: "rgba(255,40,70,.35)" }} />
        ))}
    </AbsoluteFill>
  );
};

// <Composition width={1080} height={1920} ... />   then:
// <SafeZone preset="ig-reel"><h1>Headline</h1></SafeZone>
