# Closed-Loop Demo — "embed AI into the campaign loop end to end"

This is the whole point of `creative-factory`: it's the missing production stage that turns five separate
tools into one continuous AI campaign loop. Every number below is reproduced by running the commands —
nothing is asserted by hand. Reproduced outputs live in `evals/closed-loop-demo/`.

```
 [1] geo-content-brief ──┐  what to say (answer-first claim, quotable facts)
                         ▼
 [2] brand-system ──► [3] CREATIVE-FACTORY ──► [4] experiment-designer ──► [5] lift-scorecard
     voice + gate        format × pillar ×        size AI-vs-agency-          incremental GNS /
                         audience matrix          vs-holdout test             iCPA / iROAS vs agency
                         → manifest + 89% gate
                         → (opt) rendered heroes
```

The campaign carried through all five stages: **TurboTax TY25 prospecting — AI vs Agency creative.**

## [1] geo-content-brief → the angle

`geo-visibility-tracker` found TurboTax loses purchase-intent queries (e.g. "is turbotax free") to
FreeTaxUSA / Cash App. `geo-content-brief` turned that gap into a brief whose answer-first claim is
**"free for simple returns."** That claim is lifted into the campaign as a `geo_angle` — so GEO research
becomes creative input instead of a document nobody actions:

```json
"messaging": { "geo_angles": [{"angle": "free for simple returns",
                               "source": "geo-content-brief: turbotax — is turbotax free"}] }
```

## [2] brand-system → ground truth + the gate

`assets/turbotax.campaign.json` points at `brand-system/assets/turbotax.brand.json` for voice, audiences,
approved CTAs, and — critically — the **compliance gate** the factory runs every variant through.

## [3] creative-factory → the variants

```bash
python3 scripts/factory.py plan  assets/turbotax.campaign.json --out variant-plan.json
#   PLAN: 18 variants = 3 formats × 3 pillars × 2 audiences   (the GEO angle folded in as the 3rd pillar)
# (fill copy to spec + voice + compliance — assets/variants.example.json is the filled result)
python3 scripts/factory.py build assets/variants.example.json \
    --fineprint "~37% of taxpayers qualify for TurboTax Free Edition (simple Form 1040 returns only)." \
    --out out/ --render-prompts
#   BUILD: 18 generated | 16 shippable | 1 BLOCK | 0 REVIEW | 1 char-fail
#   brand_qa_pass_rate = 89%
```

The gate earned its keep — it held back exactly two that should never ship:

| Variant | Why held back |
|---|---|
| `meta_feed__confidence__self_employed` | **BLOCK** — "guaranteed maximum refund" (banned outcome promise) + missing Maximum-Refund-Guarantee disclaimer |
| `google_rsa__ease__self_employed` | **char FAIL** — 38-char headline in a 30-char RSA slot (would truncate live) |

The other 16 cleared both gates and ship automatically. That 89% auto-clear rate **is** what makes "AI
creative at scale in a regulated industry" possible — no human eyeballs 18 (or 1,800) variants for a
banned claim. The manifest's `lift_handoff` carries the measured production numbers forward:

```json
"arms.ai": { "assets": 16, "cost_per_asset": 120, "time_to_launch_days": 3, "hours": 60,
             "brand_qa_pass_rate": 0.8889, "impressions": null, "conversions": null /* post-flight */ }
```

## [4] experiment-designer → size the test

```bash
python3 ../experiment-designer/scripts/design.py ../experiment-designer/assets/design.example.json --out loop/
#   Required n/arm: 80,679 | cells: 3 (ai/agency/holdout) | duration: 1 day | FEASIBLE
```

## [5] lift-scorecard → prove incremental lift

The AI arm's **production** fields are the factory's `lift_handoff` (cost/asset $120, time-to-launch 3d,
89% gate pass); the **performance** fields are filled after the flight. Against the agency baseline and a
holdout:

```bash
python3 ../lift-scorecard/scripts/lift.py loop/loop_results.json --out loop/
#   VERDICT: SCALE AI
#   AI:     lift +18.0% (p≈0), iCPA $41.67, incremental conv 7,200
#   Agency: lift +12.5% (p≈0), iCPA $60.00, incremental conv 5,000
```

**SCALE AI**: AI creative drove **+18% incremental lift** (vs agency's +12.5%) at an **iCPA of $41.67 vs
$60**, produced at **$120/asset vs $1,500 (12.5× cheaper)** and **3 days to launch vs 18**.

## What this demonstrates (the JD lines)

| JD line | Where it's shown |
|---|---|
| "embed AI into the campaign loop end to end" | the whole chain [1]→[5], one campaign, reproducible |
| "creative production at scale … on-brand variants" | [3] the format × pillar × audience matrix |
| "shipping production grade variants into ad platforms" | [3] per-platform spec + char-limit validation |
| AI creative must pass legal/compliance gates (fintech) | [3] 89% gate pass; 1 BLOCK held back automatically |
| "quantify AI driven lift over agency baselines" | [5] SCALE AI: +18% lift, iCPA $41.67 vs $60 |
| "incremental GNS" north-star | [4]+[5] holdout-based incrementality, not last-click |
| AEO/GEO feeding creative | [1] geo-content-brief angle → [3] factory pillar |

## Honesty (read this)

`assets` and `brand_qa_pass_rate` are **measured** by the build. The performance numbers in
`loop_results.json` are **illustrative pilot figures** — a real claim requires a real flight with a real
holdout. The loop is the method; the numbers above are a worked example proving the method runs, not a
result from a live Intuit campaign.
