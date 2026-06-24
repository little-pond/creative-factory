import React from "react";
import {
  AbsoluteFill,
  Sequence,
  Img,
  staticFile,
  useCurrentFrame,
  interpolate,
  Easing,
} from "remotion";
import { SANS, MONO, C, FPS } from "./theme";

export { FPS };

const S = {
  cold: [0, 150],
  loop: [150, 270],
  geo: [420, 300],
  plan: [720, 330],
  gate: [1050, 420],
  ads: [1470, 330],
  lift: [1800, 330],
  bench: [2130, 300],
  close: [2430, 270],
} as const;
export const DEMO_DURATION = 2700;

// ---------- primitives ----------
const ease = Easing.out(Easing.cubic);

// editorial clip-wipe reveal (not a floaty fade)
const wipe = (frame: number, delay: number, dur = 13, dir: "up" | "down" | "left" = "up") => {
  const p = interpolate(frame, [delay, delay + dur], [100, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  if (dir === "up") return `inset(${p}% 0% 0% 0%)`;
  if (dir === "down") return `inset(0% 0% ${p}% 0%)`;
  return `inset(0% ${p}% 0% 0%)`;
};
const slide = (frame: number, delay: number, dist: number, dur = 16) =>
  interpolate(frame, [delay, delay + dur], [dist, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
const appear = (frame: number, delay: number, dur = 10) =>
  interpolate(frame, [delay, delay + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
const count = (frame: number, to: number, delay: number, dur = 28) =>
  Math.round(interpolate(frame, [delay, delay + dur], [0, to], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease }));

const Grain: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none", opacity: 0.07, mixBlendMode: "overlay" }}>
    <svg width="100%" height="100%">
      <filter id="grain">
        <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#grain)" />
    </svg>
  </AbsoluteFill>
);

const PAD = 96;
// strict corner metadata texture — the editorial credibility layer
const Meta: React.FC<{
  on: "paper" | "ink";
  kicker: string;
  idx: number;
  data: string[];
}> = ({ on, kicker, idx, data }) => {
  const frame = useCurrentFrame();
  const col = on === "paper" ? C.muted : C.mutedDk;
  const op = appear(frame, 2, 12);
  const lab = { fontFamily: MONO, fontSize: 17, letterSpacing: 2, color: col, opacity: op } as const;
  return (
    <>
      <div style={{ position: "absolute", top: PAD, left: PAD, ...lab }}>{kicker}</div>
      <div style={{ position: "absolute", top: PAD, right: PAD, ...lab, textAlign: "right" }}>
        {String(idx).padStart(2, "0")} / 09
      </div>
      <div
        style={{
          position: "absolute",
          bottom: PAD,
          left: PAD,
          right: PAD,
          display: "flex",
          gap: 28,
          flexWrap: "wrap",
          ...lab,
          fontSize: 16,
        }}
      >
        {data.map((d, i) => (
          <span key={i}>{d}</span>
        ))}
      </div>
    </>
  );
};

const Stage: React.FC<{ bg: string; children: React.ReactNode }> = ({ bg, children }) => (
  <AbsoluteFill style={{ backgroundColor: bg, fontFamily: SANS, overflow: "hidden" }}>
    {children}
    <Grain />
  </AbsoluteFill>
);

// huge display type, tracked tight, bleeds off the frame
const huge: React.CSSProperties = {
  fontFamily: SANS,
  fontWeight: 900,
  letterSpacing: "-0.04em",
  lineHeight: 0.86,
  textTransform: "uppercase",
};

// ---------- 1. cold open ----------
const ColdOpen: React.FC = () => {
  const frame = useCurrentFrame();
  const blockX = slide(frame, 6, 700);
  return (
    <Stage bg={C.paper}>
      {/* blue block bleeding off the top-right */}
      <div
        style={{
          position: "absolute",
          top: -120,
          right: -80,
          width: 760,
          height: 470,
          background: C.blue,
          transform: `translateX(${blockX}px)`,
        }}
      >
        <div style={{ position: "absolute", bottom: 34, left: 44, fontFamily: MONO, fontSize: 19, letterSpacing: 2, color: C.paper, opacity: appear(frame, 22), lineHeight: 1.7 }}>
          AI CREATIVE<br />PRODUCTION ENGINE
        </div>
      </div>
      {/* giant title, bleeds off bottom-left */}
      <div style={{ position: "absolute", left: PAD - 8, bottom: 84 }}>
        <div style={{ overflow: "hidden" }}>
          <div style={{ ...huge, fontSize: 250, color: C.ink, clipPath: wipe(frame, 16, 16) }}>creative</div>
        </div>
        <div style={{ overflow: "hidden", marginTop: -18 }}>
          <div style={{ ...huge, fontSize: 250, color: C.ink, clipPath: wipe(frame, 26, 16) }}>factory</div>
        </div>
      </div>
      <Meta on="paper" kicker="THE AI CAMPAIGN LOOP — END TO END" idx={1} data={["INTUIT · MARKETING FUTURES", "A WORKING SYSTEM, NOT SLIDES", "EST. 2026"]} />
    </Stage>
  );
};

// ---------- 2. loop diagram ----------
const stations = [
  ["01", "geo-content-brief", "what to say"],
  ["02", "brand-system", "voice + gate"],
  ["03", "creative-factory", "the variants"],
  ["04", "experiment-designer", "size the test"],
  ["05", "lift-scorecard", "prove the lift"],
];
const LoopDiagram: React.FC = () => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [12, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  return (
    <Stage bg={C.ink}>
      <div style={{ position: "absolute", left: PAD, top: 250 }}>
        <div style={{ overflow: "hidden" }}>
          <div style={{ ...huge, fontSize: 150, color: C.paper, clipPath: wipe(frame, 8, 14) }}>the loop</div>
        </div>
      </div>
      {/* baseline that draws across, bleeding both edges */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 620, height: 2, background: C.mutedDk, transform: `scaleX(${line})`, transformOrigin: "left" }} />
      <div style={{ position: "absolute", left: PAD, right: PAD, top: 470, display: "flex", justifyContent: "space-between" }}>
        {stations.map((s, i) => {
          const d = 26 + i * 12;
          const cf = s[1] === "creative-factory";
          return (
            <div key={s[0]} style={{ width: 300, transform: `translateY(${slide(frame, d, 40)}px)`, opacity: appear(frame, d) }}>
              {cf && <div style={{ position: "absolute", marginTop: -8, marginLeft: -16, width: 300, height: 150, background: C.blue }} />}
              <div style={{ position: "relative", fontFamily: SANS, fontWeight: 900, fontSize: 78, color: cf ? C.paper : C.mutedDk, letterSpacing: "-0.03em" }}>{s[0]}</div>
              <div style={{ position: "relative", fontFamily: MONO, fontSize: 22, color: cf ? C.paper : C.paper, marginTop: 8 }}>{s[1]}</div>
              <div style={{ position: "relative", fontFamily: MONO, fontSize: 17, color: cf ? C.paper : C.mutedDk, marginTop: 4, opacity: 0.8 }}>{s[2]}</div>
            </div>
          );
        })}
      </div>
      <Meta on="ink" kicker="ONE CAMPAIGN · FIVE STAGES · ALL SELF-BUILT" idx={2} data={["FROM SEARCH-GAP TO PROVEN LIFT", "03 = THIS REPO"]} />
    </Stage>
  );
};

// ---------- terminal (mono, no chrome — editorial) ----------
const Term: React.FC<{ cmd: string; lines: { t: string; c?: string; d: number }[] }> = ({ cmd, lines }) => {
  const frame = useCurrentFrame();
  const chars = Math.max(0, Math.min(cmd.length, Math.floor((frame - 8) * 2.4)));
  const caret = frame % 28 < 14 ? "_" : " ";
  return (
    <div style={{ fontFamily: MONO, fontSize: 25, lineHeight: 1.85 }}>
      <div style={{ color: C.paper }}>
        <span style={{ color: C.blue }}>▸ </span>
        {cmd.slice(0, chars)}
        <span style={{ color: C.blue }}>{chars < cmd.length ? caret : ""}</span>
      </div>
      {lines.map((l, i) => (
        <div key={i} style={{ color: l.c ?? C.mutedDk, opacity: appear(frame, l.d), marginTop: i === 0 ? 18 : 2 }}>
          {l.t}
        </div>
      ))}
    </div>
  );
};

// ---------- 3. geo angle ----------
const GeoAngle: React.FC = () => {
  const frame = useCurrentFrame();
  const strike = interpolate(frame, [30, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  return (
    <Stage bg={C.paper}>
      <div style={{ position: "absolute", left: PAD, top: 250 }}>
        <div style={{ fontFamily: MONO, fontSize: 20, color: C.muted, letterSpacing: 2, marginBottom: 18, opacity: appear(frame, 6) }}>THE GAP — “is turbotax free”</div>
        <div style={{ position: "relative", display: "inline-block" }}>
          <div style={{ ...huge, fontSize: 96, color: C.muted }}>is turbotax free</div>
          <div style={{ position: "absolute", top: "52%", left: -10, height: 10, width: `calc((100% + 20px) * ${strike})`, background: C.verm }} />
        </div>
      </div>
      {/* the angle, giant blue, bleeds right */}
      <div style={{ position: "absolute", left: PAD, top: 470 }}>
        {["free for", "simple", "returns →"].map((w, i) => (
          <div key={w} style={{ overflow: "hidden" }}>
            <div style={{ ...huge, fontSize: 188, color: C.blue, clipPath: wipe(frame, 58 + i * 9, 14), marginTop: i ? -20 : 0 }}>{w}</div>
          </div>
        ))}
      </div>
      <Meta on="paper" kicker="STAGE 01 — GEO FINDS THE ANGLE" idx={3} data={["SHARE OF AI VOICE: 0%", "LOST TO FREETAXUSA / CASH APP", "→ BECOMES A CAMPAIGN PILLAR"]} />
    </Stage>
  );
};

// ---------- 4. plan (left ink / right paper) ----------
const PlanScene: React.FC = () => {
  const frame = useCurrentFrame();
  const split = slide(frame, 4, -760, 18);
  const big = count(frame, 18, 60, 26);
  return (
    <Stage bg={C.paper}>
      {/* left ink panel */}
      <div style={{ position: "absolute", top: 0, bottom: 0, left: 0, width: 760, background: C.ink, transform: `translateX(${split}px)`, padding: `${PAD}px 60px` }}>
        <div style={{ fontFamily: MONO, fontSize: 18, color: C.mutedDk, letterSpacing: 2, marginBottom: 40 }}>STAGE 02+03 — BUILD THE MATRIX</div>
        <Term
          cmd="factory.py plan campaign.json"
          lines={[
            { t: "PLAN: 18 variants", c: C.paper, d: 64 },
            { t: "3 formats × 3 pillars", c: C.blue, d: 80 },
            { t: "× 2 audiences", c: C.blue, d: 88 },
            { t: "geo angle folded in", c: C.mutedDk, d: 104 },
          ]}
        />
      </div>
      {/* right: giant 18 bleeding + matrix */}
      <div style={{ position: "absolute", left: 820, top: 150 }}>
        <div style={{ display: "flex", alignItems: "flex-start" }}>
          <div style={{ ...huge, fontSize: 440, color: C.ink, marginTop: -60 }}>{big}</div>
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 40, color: C.ink, marginTop: 30, marginLeft: 10, letterSpacing: "-0.02em" }}>
            ON-BRAND<br />VARIANTS
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 60px)", gap: 12, marginTop: 8 }}>
          {Array.from({ length: 18 }).map((_, i) => (
            <div key={i} style={{ width: 60, height: 44, background: C.ink, opacity: appear(frame, 150 + i * 4) }} />
          ))}
        </div>
        <div style={{ fontFamily: MONO, fontSize: 18, color: C.muted, letterSpacing: 1.5, marginTop: 34, opacity: appear(frame, 150) }}>
          FORMAT × MESSAGE × AUDIENCE<br />META · GOOGLE · TIKTOK · LINKEDIN · DV360
        </div>
      </div>
      {/* split-bg-aware metadata (global Meta would fall on the dark panel) */}
      <div style={{ position: "absolute", top: PAD, right: PAD, fontFamily: MONO, fontSize: 17, letterSpacing: 2, color: C.muted }}>04 / 09</div>
      <div style={{ position: "absolute", bottom: PAD, left: 820, fontFamily: MONO, fontSize: 16, letterSpacing: 2, color: C.muted }}>EACH VARIANT WRITTEN TO EXACT PLATFORM SPEC</div>
    </Stage>
  );
};

// ---------- 5. gate (the money shot) ----------
const GateScene: React.FC = () => {
  const frame = useCurrentFrame();
  const pr = count(frame, 89, 70, 34);
  const strike = interpolate(frame, [150, 168], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const blockY = slide(frame, 150, 500, 16);
  return (
    <Stage bg={C.paper}>
      {/* left mono stats */}
      <div style={{ position: "absolute", left: PAD, top: 250, fontFamily: MONO, fontSize: 28, lineHeight: 1.9 }}>
        <div style={{ color: C.ink, opacity: appear(frame, 50) }}>18 generated</div>
        <div style={{ color: C.ink, opacity: appear(frame, 60) }}>16 shippable</div>
        <div style={{ color: C.verm, opacity: appear(frame, 70) }}>1 blocked</div>
        <div style={{ color: C.muted, opacity: appear(frame, 78) }}>1 char-fail</div>
        <div style={{ marginTop: 36, opacity: appear(frame, 88) }}>
          <span style={{ ...huge, fontFamily: SANS, fontSize: 200, color: C.ink }}>{pr}%</span>
          <div style={{ fontFamily: MONO, fontSize: 20, color: C.muted, marginTop: -10 }}>BRAND-QA PASS RATE</div>
        </div>
      </div>
      {/* vermillion BLOCK bleeding off the right */}
      <div style={{ position: "absolute", right: -60, top: 150, width: 920, transform: `translateY(${blockY}px)` }}>
        <div style={{ ...huge, fontSize: 320, color: C.verm }}>block</div>
        <div style={{ position: "relative", marginLeft: 12, marginTop: 6 }}>
          <span style={{ fontFamily: SANS, fontWeight: 800, fontSize: 46, color: C.ink, letterSpacing: "-0.02em" }}>“guaranteed maximum refund”</span>
          <div style={{ position: "absolute", top: "52%", left: -4, height: 8, width: `calc(100% * ${strike})`, background: C.verm }} />
        </div>
        <div style={{ fontFamily: MONO, fontSize: 22, color: C.muted, marginTop: 18, marginLeft: 14 }}>banned outcome promise · held back automatically</div>
      </div>
      <Meta on="paper" kicker="THE GATE BITES — REGULATED-INDUSTRY GUARDRAIL" idx={5} data={["EVERY VARIANT LINTED BEFORE SHIP", "THE MACHINE CATCHES IT, NOT A HUMAN"]} />
    </Stage>
  );
};

// ---------- 6. ads (real renders, filmstrip) ----------
const adData = [
  ["ad_meta-feed_confidence_first-time.png", "META · FEED", "1080×1080", false],
  ["ad_linkedin_ease_self-employed.png", "LINKEDIN", "1200×627", true],
  ["ad_meta-feed_free_first-time.png", "META · FEED", "1080×1080", false],
] as const;
const AdsScene: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Stage bg={C.ink}>
      {/* headline top-left */}
      <div style={{ position: "absolute", left: PAD - 6, top: 168 }}>
        <div style={{ overflow: "hidden" }}>
          <div style={{ ...huge, fontSize: 150, color: C.paper, clipPath: wipe(frame, 8, 14) }}>real.</div>
        </div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 32, color: C.blue, letterSpacing: "-0.02em", marginTop: 6, opacity: appear(frame, 26) }}>
          rendered visual + gate-passed copy, composited
        </div>
      </div>
      {/* filmstrip below, bleeds off the right */}
      <div style={{ position: "absolute", left: PAD, top: 440, display: "flex", gap: 30, alignItems: "flex-start" }}>
        {adData.map((a, i) => {
          const land = a[3];
          const w = land ? 560 : 400;
          const h = land ? 293 : 400;
          return (
            <div key={a[0] as string} style={{ transform: `translateY(${slide(frame, 30 + i * 14, 60)}px)`, opacity: appear(frame, 30 + i * 14), clipPath: wipe(frame, 30 + i * 14, 16, "up") }}>
              <div style={{ width: w, height: h, overflow: "hidden", border: `1px solid ${C.mutedDk}` }}>
                <Img src={staticFile(a[0] as string)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </div>
              <div style={{ fontFamily: MONO, fontSize: 16, color: C.mutedDk, marginTop: 12, letterSpacing: 1 }}>
                {a[1]} · {a[2]} · <span style={{ color: C.blue }}>GATE ✓</span>
              </div>
            </div>
          );
        })}
      </div>
      <Meta on="ink" kicker="STAGE 03 — REAL RENDERED CREATIVE" idx={6} data={["GENERATED → COMPOSITED AT EXACT PLATFORM SPEC", "ONLY GATE-PASSED VARIANTS RENDERED"]} />
    </Stage>
  );
};

// ---------- 7. lift ----------
const LiftScene: React.FC = () => {
  const frame = useCurrentFrame();
  const lift = count(frame, 18, 40, 30);
  return (
    <Stage bg={C.ink}>
      <div style={{ position: "absolute", left: PAD, top: 200 }}>
        <div style={{ overflow: "hidden" }}>
          <div style={{ ...huge, fontSize: 150, color: C.paper, clipPath: wipe(frame, 8, 14) }}>scale ai</div>
        </div>
      </div>
      {/* enormous +18% bleeding right */}
      <div style={{ position: "absolute", left: PAD - 10, top: 330, display: "flex", alignItems: "flex-start" }}>
        <div style={{ ...huge, fontSize: 460, color: C.blue }}>+{lift}%</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 40, color: C.paper, marginTop: 40, letterSpacing: "-0.02em" }}>
          INCREMENTAL<br />LIFT vs AGENCY
        </div>
      </div>
      <div style={{ position: "absolute", left: PAD, bottom: 170, display: "flex", gap: 40, fontFamily: MONO, fontSize: 22, color: C.paper, opacity: appear(frame, 70) }}>
        <span>iCPA <b style={{ color: C.blue }}>$41.67</b> vs $60</span>
        <span style={{ color: C.mutedDk }}>/</span>
        <span><b style={{ color: C.blue }}>12.5×</b> cheaper/asset</span>
        <span style={{ color: C.mutedDk }}>/</span>
        <span><b style={{ color: C.blue }}>3d</b> to launch vs 18</span>
      </div>
      <Meta on="ink" kicker="STAGE 04+05 — PROVE THE LIFT" idx={7} data={["HOLDOUT-BASED INCREMENTALITY, NOT LAST-CLICK", "VERDICT: SCALE AI"]} />
    </Stage>
  );
};

// ---------- 8. benchmark ----------
const BenchScene: React.FC = () => {
  const frame = useCurrentFrame();
  const a = count(frame, 100, 24, 30);
  const b = count(frame, 50, 44, 30);
  return (
    <Stage bg={C.paper}>
      <div style={{ position: "absolute", left: PAD, top: 200, display: "flex", alignItems: "baseline", gap: 30 }}>
        <div style={{ ...huge, fontSize: 380, color: C.blue }}>{a}</div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 44, color: C.ink, letterSpacing: "-0.02em" }}>
          % — WITH<br />THE FACTORY
        </div>
      </div>
      <div style={{ position: "absolute", left: PAD, top: 600, display: "flex", alignItems: "baseline", gap: 30 }}>
        <div style={{ ...huge, fontSize: 230, color: C.paper, WebkitTextStroke: `3px ${C.verm}` }}>{b}</div>
        <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 30, color: C.verm, letterSpacing: "-0.01em" }}>
          % — BASELINE AGENT<br />
          <span style={{ color: C.muted, fontWeight: 500, fontSize: 24 }}>invented a brand · faked the agency number</span>
        </div>
      </div>
      <Meta on="paper" kicker="BLIND-TESTED ON BRANDS IT HAD NEVER SEEN" idx={8} data={["QUICKBOOKS + MAILCHIMP · 4 RUNS", "WITH-SKILL vs BASELINE, GRADED"]} />
    </Stage>
  );
};

// ---------- 9. close ----------
const Close: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Stage bg={C.ink}>
      <div style={{ position: "absolute", left: PAD - 8, top: 300 }}>
        <div style={{ overflow: "hidden" }}>
          <div style={{ ...huge, fontSize: 250, color: C.paper, clipPath: wipe(frame, 8, 16) }}>one loop.</div>
        </div>
        <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 46, color: C.paper, marginTop: 24, letterSpacing: "-0.02em", opacity: appear(frame, 30) }}>
          GEO → creative → <span style={{ color: C.blue }}>proven lift.</span>
        </div>
      </div>
      <div style={{ position: "absolute", left: -80, top: -100, width: 520, height: 360, background: C.blue, opacity: appear(frame, 4) }} />
      <div style={{ position: "absolute", left: PAD, bottom: 150, fontFamily: MONO, fontSize: 30, color: C.blue, opacity: appear(frame, 44) }}>
        github.com/little-pond/creative-factory
      </div>
      <Meta on="ink" kicker="SKILL → MCP → PRODUCTION" idx={9} data={["BUILT WITH CLAUDE CODE", "A WORKING SYSTEM"]} />
    </Stage>
  );
};

export const CreativeFactoryDemo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: C.paper }}>
    <Sequence from={S.cold[0]} durationInFrames={S.cold[1]}><ColdOpen /></Sequence>
    <Sequence from={S.loop[0]} durationInFrames={S.loop[1]}><LoopDiagram /></Sequence>
    <Sequence from={S.geo[0]} durationInFrames={S.geo[1]}><GeoAngle /></Sequence>
    <Sequence from={S.plan[0]} durationInFrames={S.plan[1]}><PlanScene /></Sequence>
    <Sequence from={S.gate[0]} durationInFrames={S.gate[1]}><GateScene /></Sequence>
    <Sequence from={S.ads[0]} durationInFrames={S.ads[1]}><AdsScene /></Sequence>
    <Sequence from={S.lift[0]} durationInFrames={S.lift[1]}><LiftScene /></Sequence>
    <Sequence from={S.bench[0]} durationInFrames={S.bench[1]}><BenchScene /></Sequence>
    <Sequence from={S.close[0]} durationInFrames={S.close[1]}><Close /></Sequence>
  </AbsoluteFill>
);
