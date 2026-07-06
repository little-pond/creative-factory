# creative-factory

> The AI **creative-production** engine: turn one campaign brief + one brand into a matrix of on-brand,
> spec-valid, compliance-gated ad variants — then hand the production numbers straight to an
> incrementality experiment. A Claude Code skill. Not slides — it runs, and every number below is
> reproduced by the included scripts.

Built for the kind of production workflow Adobe Gen Studio / Celtra sit in: creative production at
scale, production-grade variants shipped to ad-platform spec, and AI embedded into the campaign loop
end to end. Vendor- and brand-agnostic — the worked example uses a fictional brand ("Northwind Tax").

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
python3 scripts/factory.py plan assets/northwind.campaign.json --out /tmp/plan.json
#   PLAN: 18 variants = 3 formats × 3 pillars × 2 audiences   (a GEO angle folded in as the 3rd pillar)

# 2) build: validate spec + run the compliance gate + emit the manifest
python3 scripts/factory.py build assets/variants.example.json --out /tmp/cf --render-prompts
#   BUILD: 18 generated | 16 shippable | 1 BLOCK | 0 REVIEW | 1 char-fail   →   brand_qa_pass_rate = 89%

# 3) verify it end to end
python3 evals/factory_test.py
```

The gate held back exactly the two that should never ship: a **banned-claim BLOCK** ("guaranteed maximum
refund") and a **truncated headline** (38 chars in a 30-char RSA slot). The other 16 cleared automatically.

> **Blind-tested** on brands it had never seen (FreshBooks, Klaviyo): with the skill, a fresh agent
> scored **100%**; without it, **50%** — drifting off-brief and fabricating its agency comparison. See
> [`evals/BENCHMARK.md`](evals/BENCHMARK.md).

## The render path (produce real assets)

The hybrid render path runs end to end and is **opt-in** — no rendered assets are committed, so a fresh
clone renders its own, for any brand:

```bash
python3 scripts/factory.py build assets/variants.example.json --out out/ --render-prompts  # → out/render-queue.json
python3 scripts/render.py  out/render-queue.json --go --max-cost 0.50                       # OpenRouter image models → heroes/
python3 scripts/compose.py --image heroes/<id>.png --dims 1080x1080 --zone top \
    --headline "File with confidence" --cta "Start for free" --brand "#1E5EB8" \
    --wordmark "Northwind" --out out/ad.png                                                 # gate-passed copy on top
```

`render.py` drives **OpenRouter image models** (Gemini 3 Pro Image by default, or Gemini Flash / OpenAI
`gpt-5-image`) as the local Adobe-Gen-Studio-equivalent, and injects an anti-slop constraint block so the
hero isn't generic stock. `compose.py` (Pillow) lays the gate-passed copy on at exact platform dims,
**keeps it out of the placement's safe zone, and checks legibility contrast**. Only the *shippable* rows
render — the gate filtered the rest. See [`assets/heroes/`](assets/heroes/README.md) for the how-to.

## It closes the loop

`creative-factory` is the production stage that connects two otherwise-separate loops into one:

```
 geo-content-brief ──┐  what to say (answer-first claim, quotable facts)
                     ▼
 brand-system ──► creative-factory ──► experiment-designer ──► lift-scorecard
 voice + gate       format × pillar ×    size AI-vs-agency-      incremental new customers /
                    audience matrix      vs-holdout test         iCPA / iROAS vs agency
```

One Northwind Tax campaign carried through all five stages → **SCALE AI: +18% incremental lift, iCPA $41.67 vs
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
├── scripts/
│   ├── factory.py               ← plan (matrix) + build (validate + gate + dedup + manifest + lift handoff) + ingest
│   ├── formats.py               ← platform format registry (dims / safe zones / char limits) + safe-zone check
│   ├── render.py                ← (opt) render shippable hero prompts via OpenRouter image models (anti-slop injected)
│   └── compose.py               ← (opt, Pillow) copy-on-hero composer (safe-zone + contrast enforced)
├── references/                  ← format-specs, variant-strategy, anti-slop-image, closed-loop-demo
├── assets/                      ← campaign template + worked (fictional) Northwind Tax example
├── evals/                       ← factory_test.py + reproduced closed-loop-demo outputs
└── vendor/brand-system/         ← vendored compliance gate (so it runs standalone)
```

## What it gives you

| Capability | Where |
|---|---|
| Creative production at scale — on-brand variants | the `format × pillar × audience` matrix |
| Production-grade variants to ad-platform spec | per-platform spec + char-limit validation |
| Legal/compliance gating for regulated industries | the compliance gate; 89% auto-clear, BLOCKs held back |
| AI embedded in the campaign loop end to end | the closed-loop demo (brief → factory → experiment → readout) |
| Incremental lift vs an agency baseline | the manifest → `lift-scorecard` handoff |

## Honesty

`assets` and `brand_qa_pass_rate` are **measured** by the build. The performance numbers in the demo are
**illustrative pilot figures** — a real lift claim needs a real flight with a real holdout. The loop is
the method; the numbers are a worked example proving the method runs, not a result from a live account.

## License

MIT — see [LICENSE](LICENSE).

---

*A demonstration system. No API keys or real account data are included; all figures are from worked examples.*
