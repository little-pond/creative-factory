# Ad Format Registry

The specs the factory builds and validates against, in human-readable form. The machine-readable source
of truth is `scripts/formats.py` (`FORMATS`); this doc explains the *why* behind each so the copy you
write actually survives contact with the placement.

> **Specs drift.** Platforms change character limits and safe zones regularly. These are a sane,
> current-ish default. Before a real flight, reconcile against the live spec sheet (Meta Ads Guide,
> Google Ads asset specs, TikTok Creative Center, LinkedIn Ads help, IAB display sizes, X Ads specs,
> YouTube advertising specs, Pinterest Business, Snapchat Ads Manager, 小红书/蒲公英 官方规格).

## Table of contents
- [How to read a spec](#how-to-read-a-spec)
- [Meta](#meta) — feed, feed 4:5, stories, reels, carousel
- [Google](#google) — RSA (search), RDA (display)
- [TikTok](#tiktok) — in-feed, TopView
- [LinkedIn](#linkedin) — single image, carousel, video, document
- [DV360 / programmatic display](#dv360--programmatic-display)
- [X / Twitter](#x--twitter) — single image, carousel
- [YouTube](#youtube) — Shorts, in-stream, thumbnail
- [Pinterest](#pinterest) — standard pin, idea pin
- [Snapchat](#snapchat) — single
- [小红书 / Xiaohongshu](#小红书--xiaohongshu) — note cover, note square
- [Adding a format](#adding-a-format)

> **10 channels · 27 placements.** Run `python3 scripts/formats.py` for the live table.

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
- **feed_4x5** — 1080×1350 (4:5), image. Same limits as feed; **earns the most vertical feed real estate**
  on mobile — prefer over 1:1 when the visual is portrait-friendly.
- **carousel** — 2–10 cards, each 1080×1080 (or 1080×1350). `primary_text` is shared across cards;
  `headline`/`description` are per-card (`description` ≤20 here). Each card is its own hero.

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
- **topview** — 1080×1920 (9:16), video. Full-screen takeover on app open; less UI in the first seconds
  than in-feed, but still keep key content out of the **bottom ~20%** and the **right ~140px** rail.

## LinkedIn

- **single_image** — 1200×627 (1.91:1) or 1200×1200 (1:1). `intro_text` ≤150 (truncates on desktop),
  `headline` ≤70 (less visible on mobile). Register is **B2B / professional**, not consumer — in a
  B2B context this is accountant-facing, not consumer.
- **carousel** — 2–10 cards, each 1080×1080. Card `headline` ≤45. B2B register.
- **video** — 1:1 (feed) or 16:9; hook in the first 3s. Captions on — most B2B video is watched muted.
- **document** — multi-page PDF ad (each page 1080×1080 or 1620×1080). High dwell; treat each page as a slide.

## DV360 / programmatic display

Fixed IAB banner sizes; text is baked into the HTML5/image, so keep it to a line + CTA.

| Size | Name | headline ≤ | notes |
|---|---|---|---|
| 300×250 | Medium Rectangle | 35 | the workhorse; one line + CTA |
| 728×90 | Leaderboard | 30 | very short height; CTA chip |
| 160×600 | Wide Skyscraper | 30 | vertical; stack logo/headline/CTA |
| 320×50 | Mobile Banner | 25 | tiny; CTA-led, almost no body |

## X / Twitter

- **single_image** — 1600×900 (16:9), or 1200×628 (1.91:1). Tweet `copy` ≤280; website-card `headline` ~70.
- **carousel** — 2–6 cards, each 1:1 (800×800+) or 1.91:1. Shared tweet `copy` + per-card `headline`.

## YouTube

- **shorts** — 1080×1920 (9:16), video. Bottom **~320px** (title/handle/actions) + **right ~100px** rail
  covered. Hook in 1–2s; on-screen text is a minimal companion — the video carries the message.
- **in_stream** — 1920×1080 (16:9), video, skippable (skip at 5s). **Front-load** the brand + hook;
  bottom ~120px holds the skip/CTA overlay. `headline` ≤15, `description` ≤35 (companion).
- **thumbnail** — 1280×720 (16:9), image. A real design asset: **huge, minimal** text (≤4 words) that
  must read at 168×94 on mobile. Faces + high contrast win. This is where a bold layout formula earns its keep.

## Pinterest

- **standard_pin** — 1000×1500 (2:3), image. Native ratio; **text overlaid on the image** reads best.
  `title` ≤100 (~40 shows in feed), `description` ≤500. Long-life, search-driven — evergreen beats topical.
- **idea_pin** — 1080×1920 (9:16), multi-page image/video. Keep text out of the top ~7% / bottom ~10% UI.

## Snapchat

- **single** — 1080×1920 (9:16), image/video. Keep content out of the **top ~150px** (brand) and
  **bottom ~150px** (swipe-up CTA). `brand_name` ≤25, `headline` ≤34. Full-screen, sound-on, native.

## 小红书 / Xiaohongshu

- **note_cover** — 竖版 **3:4 (1080×1440)**, image. 封面最占版面。封面大标题 **≤20 字**;正文 ≤1000 字。
  真人实拍 / 生活化更原生,忌硬广感 —— 封面首图决定点击率。
- **note_square** — 1:1 (1080×1080), image. 同为封面用途,标题 **≤20 字**。多图笔记的首图即封面。

## Adding a format

Add an entry under the platform in `scripts/formats.py` `FORMATS`. Required keys: `dims` (or `None` for
text), `aspect`, `asset`, `safe` (or `None`), `fields`, `limits`. Optionally `secondary_dims`,
`multiplicity` (for RSA-style "up to N of this field"), and a `note`. Add it to `DEFAULT_PLACEMENT` if it
should expand from a bare platform name. Re-run `python3 scripts/formats.py` to print the registry and
sanity-check.
