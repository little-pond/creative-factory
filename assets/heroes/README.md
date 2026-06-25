# Hero Gallery — real rendered creative

These are **real assets the factory produced**, not stock — the hybrid render path end to end:
`factory.py build --render-prompts` emitted the prompts → `scripts/render.py` rendered the visual layer
via **OpenRouter → Google Gemini 3 Pro Image** (the local Adobe-Gen-Studio-equivalent; key from `~/.env`)
→ `compose.py` laid the **gate-passed copy** onto each at exact platform spec.

Every ad here corresponds to a variant that **cleared the 18-cell TurboTax run's compliance gate**
(the 2 that didn't — the banned-claim BLOCK and the truncated headline — were never rendered).

| Finished ad | Format | Pillar × Audience | Headline | CTA |
|---|---|---|---|---|
| `ads/ad_meta-feed_confidence_first-time.png` | Meta feed 1080×1080 | confidence × first-time filers | "File with confidence" | Start for free |
| `ads/ad_meta-feed_free_first-time.png` | Meta feed 1080×1080 | free (GEO-fed) × first-time filers | "File simple returns free" | Start for free |
| `ads/ad_linkedin_ease_self-employed.png` | LinkedIn 1200×627 | ease × self-employed | "Self-employed taxes without the busywork" | File with TurboTax |

`heroes/*.png` = the raw rendered visual layer (no copy); `heroes/ads/*.png` = the composed finished ad.
The split is deliberate — one hero serves many headlines/audiences, which is exactly how DCO / Gen Studio
reuse a visual across a variant matrix.

**Notes**
- Brand palette shows through on purpose: TurboTax-blue CTA (#355EBE), warm accent (#FBB034 — the scarf).
- Display font is Helvetica Neue as a stand-in for the brand font (Avenir Next); swap for production.
- `compose.py` needs Pillow; it's the one optional non-stdlib piece (the render path is opt-in).
- Illustrative demo for a portfolio — not Intuit-approved creative.
