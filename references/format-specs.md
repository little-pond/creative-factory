# Ad Format Registry

The specs the factory builds and validates against, in human-readable form. The machine-readable source
of truth is `scripts/formats.py` (`FORMATS`); this doc explains the *why* behind each so the copy you
write actually survives contact with the placement.

> **Specs drift.** Platforms change character limits and safe zones regularly. These are a sane,
> current-ish default. Before a real flight, reconcile against the live spec sheet (Meta Ads Guide,
> Google Ads asset specs, TikTok Creative Center, LinkedIn Ads help, IAB display sizes).

## Table of contents
- [How to read a spec](#how-to-read-a-spec)
- [Meta](#meta) — feed, stories, reels
- [Google](#google) — RSA (search), RDA (display)
- [TikTok](#tiktok) — in-feed
- [LinkedIn](#linkedin) — single image
- [DV360 / programmatic display](#dv360--programmatic-display)
- [Adding a format](#adding-a-format)

## How to read a spec

| Field | Meaning |
|---|---|
| `dims` / `aspect` | the canvas the creative renders on; render image/video to these |
| `safe` (px) | margins where platform UI (caption, CTA, icons) overlays the creative — keep text/logo OUT |
| `limits` | per-field character ceilings; over the limit = truncated in the wild |
| `fields` | which copy fields this placement uses (this is why a plan row only asks for some fields) |
| `asset` | `image` / `video` / `text` — whether an `image_prompt` is needed |

The **safe zone** is the most-missed one. A headline that looks perfect in the design tool can sit
directly under the TikTok caption bar or behind the Reels audio chip in the feed. The factory carries the
safe-zone pixels into every relevant row so the image prompt can compose around them.

## Meta

- **feed** — 1080×1080 (1:1). `primary_text` ≤125 (truncates on mobile), `headline` ≤40, `description` ≤30.
  1:1 is the safe default; 4:5 (1080×1350) takes more feed height. Full canvas, no UI overlay.
- **stories** — 1080×1920 (9:16). Keep text/logo out of the **top ~250px** (profile + close button) and
  **bottom ~340px** (CTA + reply bar). Full-bleed, single dominant message.
- **reels** — 1080×1920 (9:16), video. The UI is hungrier: avoid the **bottom ~670px** (caption + CTA +
  audio title) and the **right ~130px** (like/comment/share rail). Hook in the first 3 seconds.

## Google

- **rsa** (Responsive Search Ad) — text only. Supply up to **15 headlines (≤30)** and **4 descriptions
  (≤90)**; Google's system assembles and tests combinations. No image. This is where keyword-echo
  headlines live (see the user's RSA practice: pin verbatim keyword-match headlines).
- **rda** (Responsive Display Ad) — provide a **landscape 1200×628 (1.91:1)**, a **square 1200×1200**, and
  a square logo. Text: `headline` ≤30, `long_headline` ≤90, `description` ≤90, `business_name` ≤25.
  **Don't bake copy into the image** — Google overlays its own text; embedded text fights it and can hurt
  approval. The image should be pure visual.

## TikTok

- **infeed** — 1080×1920 (9:16), video. Single `caption` ≤100. Safe zones: **top ~130px**, **bottom
  ~483px** (handle + caption + CTA), **right ~140px** (icon rail). The cardinal rule is *native-first*:
  it should look like organic TikTok, not a polished ad. Hook in 1–2 seconds or it's scrolled.

## LinkedIn

- **single_image** — 1200×627 (1.91:1) or 1200×1200 (1:1). `intro_text` ≤150 (truncates on desktop),
  `headline` ≤70 (less visible on mobile). Register is **B2B / professional**, not consumer — for an
  B2B context this is accountant-facing, not consumer.

## DV360 / programmatic display

Fixed IAB banner sizes; text is baked into the HTML5/image, so keep it to a line + CTA.

| Size | Name | headline ≤ | notes |
|---|---|---|---|
| 300×250 | Medium Rectangle | 35 | the workhorse; one line + CTA |
| 728×90 | Leaderboard | 30 | very short height; CTA chip |
| 160×600 | Wide Skyscraper | 30 | vertical; stack logo/headline/CTA |
| 320×50 | Mobile Banner | 25 | tiny; CTA-led, almost no body |

## Adding a format

Add an entry under the platform in `scripts/formats.py` `FORMATS`. Required keys: `dims` (or `None` for
text), `aspect`, `asset`, `safe` (or `None`), `fields`, `limits`. Optionally `secondary_dims`,
`multiplicity` (for RSA-style "up to N of this field"), and a `note`. Add it to `DEFAULT_PLACEMENT` if it
should expand from a bare platform name. Re-run `python3 scripts/formats.py` to print the registry and
sanity-check.
