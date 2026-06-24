import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/SpaceMono";

export const { fontFamily: SANS } = loadInter("normal", {
  weights: ["400", "500", "700", "800", "900"],
});
export const { fontFamily: MONO } = loadMono("normal", { weights: ["400", "700"] });

export const FPS = 30;

// ≤3 colors per frame. Editorial: paper + ink + ONE pop (blue=brand/positive, verm=negative).
export const C = {
  paper: "#E9E5DC", // warm off-white
  paperEdge: "#D8D2C5",
  ink: "#151412", // near-black
  blue: "#1F38FF", // electric brand pop
  verm: "#E8412A", // vermillion — negative / block
  muted: "#8C8676", // metadata grey on paper
  mutedDk: "#6E6A60", // metadata grey on ink
};
