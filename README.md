# creative-factory

> The AI **creative-production** engine: turn one campaign brief + one brand into a matrix of on-brand,
> spec-valid, compliance-gated ad variants — then hand the production numbers straight to an
> incrementality experiment. A Claude Code skill. Not slides — it runs, and every number below is
> reproduced by the included scripts.

Built for the kind of workflow Adobe Gen Studio / Celtra production sits in, and against the Intuit
*Marketing Futures — AI Marketing Manager* mandate ("creative production at scale", "production-grade
variants into ad platforms", "embed AI into the campaign loop end to end").

---

## The problem it solves

AI can write a thousand ad variants an hour. That's not the hard part. The hard part is that every one
has to hit the platform's character limit, stay out of the TikTok CTA bar, sound like the brand, and —
in a regulated industry like fintech — never promise a guaranteed refund. A factory that emits 240
variants you still have to eyeball one-by-one hasn't saved anyone anything.

`creative-factory` owns the mechanical half so the only thing left to judgment is the words and the image:

- **Matrix** — expands `format × message-pillar × audience` into one variant per cell.
- **Spec** — writes each to the exact platform spec (Meta / Google / TikTok / LinkedIn / DV360 dims,
  safe zones, character limits) and fails anything that would truncate or sit under platform UI.
- **Compliance gate** — runs every variant through a brand compliance gate (banned claims, missing
  disclaimers) so the safe ones ship automatically and the unsafe ones are held back. *That* is what makes
  "AI creative at scale in a regulated industry" possible.
- **Handoff** — emits a `generation-manifest.json` whose production numbers (assets, cost/asset,
  brand-QA-pass-rate, time-to-launch) drop straight into an A/B-vs-agency incrementality readout.

## Reproduce it (60 seconds)

**Prereqs:** Python 3.10+. The core is stdlib-only; the optional render step needs Pillow.

```bash
# 1) plan the matrix
python3 scripts/factory.py plan assets/turbotax.campaign.json --out /tmp/plan.json
#   PLAN: 18 variants = 3 formats × 3 pillars × 2 audiences   (a GEO angle folded in as the 3rd pillar)

# 2) build: validate spec + run the compliance gate + emit the manifest
python3 scripts/factory.py build assets/variants.example.json --out /tmp/cf --render-prompts
#   BUILD: 18 generated | 16 shippable | 1 BLOCK | 0 REVIEW | 1 char-fail   →   brand_qa_pass_rate = 89%

# 3) verify it end to end
python3 evals/factory_test.py
```

The gate held back exactly the two that should never ship: a **banned-claim BLOCK** ("guaranteed maximum
refund") and a **truncated headline** (38 chars in a 30-char RSA slot). The other 16 cleared automatically.

> **Blind-tested** on brands it had never seen (QuickBooks, Mailchimp): with the skill, a fresh agent
> scored **100%**; without it, **50%** — drifting off-brief and fabricating its agency comparison. See
> [`evals/BENCHMARK.md`](evals/BENCHMARK.md).

## Real rendered creative

The hybrid render path runs end to end — `--render-prompts` → `generate-image` (Gemini 3 Pro) for the
visual layer → `scripts/compose.py` to lay the gate-passed copy on top at exact platform dims:

| | |
|---|---|
| ![](assets/heroes/ads/ad_meta-feed_confidence_first-time.png) | ![](assets/heroes/ads/ad_meta-feed_free_first-time.png) |

![](assets/heroes/ads/ad_linkedin_ease_self-employed.png)

Each is a variant that **cleared the compliance gate**. See [`assets/heroes/`](assets/heroes/README.md).

## It closes the loop

`creative-factory` is the production stage that connects two otherwise-separate loops into one:

```
 geo-content-brief ──┐  what to say (answer-first claim, quotable facts)
                     ▼
 brand-system ──► creative-factory ──► experiment-designer ──► lift-scorecard
 voice + gate       format × pillar ×    size AI-vs-agency-      incremental GNS /
                    audience matrix      vs-holdout test         iCPA / iROAS vs agency
```

One TurboTax campaign carried through all five stages → **SCALE AI: +18% incremental lift, iCPA $41.67 vs
$60, $120/asset vs $1,500, 3 days vs 18.** Full walkthrough:
[`references/closed-loop-demo.md`](references/closed-loop-demo.md).

> The other four stages (`geo-content-brief`, `brand-system`, `experiment-designer`, `lift-scorecard`)
> live in the companion portfolio repo. `creative-factory` runs standalone for stages it owns — the brand
> compliance gate is **vendored** under [`vendor/brand-system/`](vendor/brand-system/) so the demo works
> on a fresh clone (source of truth is the `brand-system` skill; the vendored copy is byte-identical).

## Install as a Claude Code skill

```bash
./install.sh        # copies the skill into ~/.claude/skills/creative-factory
```

Then it triggers by intent — "generate on-brand ad variants", "creative at scale", "build a Gen
Studio / DCO variant matrix", "make 50 on-brand versions of this ad".

## Layout

```
creative-factory/
├── SKILL.md                     ← the skill (workflow + division of labor)
├── demo-script.md               ← 2-minute Loom storyboard of the closed loop
├── scripts/
│   ├── factory.py               ← plan (matrix) + build (validate + gate + manifest + lift handoff)
│   ├── formats.py               ← platform format registry (dims / safe zones / char limits)
│   └── compose.py               ← (opt, Pillow) copy-on-hero finished-ad composer
├── references/                  ← format-specs, variant-strategy, closed-loop-demo
├── assets/                      ← campaign template + worked TurboTax example + heroes/ gallery
├── evals/                       ← factory_test.py + reproduced closed-loop-demo outputs
└── vendor/brand-system/         ← vendored compliance gate (so it runs standalone)
```

## How it maps to the role

| JD line | Where |
|---|---|
| "creative production at scale … on-brand variants" | the `format × pillar × audience` matrix |
| "shipping production grade variants into ad platforms" | per-platform spec + char-limit validation |
| AI creative must pass legal/compliance gates (fintech) | the compliance gate; 89% auto-clear, BLOCKs held back |
| "embed AI into the campaign loop end to end" | the closed-loop demo (brief → factory → experiment → readout) |
| "incremental GNS", "AI lift over agency baselines" | the manifest → `lift-scorecard` handoff → SCALE AI |

## Honesty

`assets` and `brand_qa_pass_rate` are **measured** by the build. The performance numbers in the demo are
**illustrative pilot figures** — a real lift claim needs a real flight with a real holdout. The loop is
the method; the numbers are a worked example proving the method runs, not a result from a live account.

## License

MIT — see [LICENSE](LICENSE).

---

*A demonstration system. No API keys or real account data are included; all figures are from worked examples.*
