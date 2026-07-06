# Benchmark — with-skill vs baseline

A blind A/B: the same two realistic tasks run by a fresh agent **with** `creative-factory` vs an
identical agent **without** it (general tooling only). Both on *new* brands the skill has never seen
(FreshBooks, Klaviyo) — so this measures generalization + whether the skill actually helps, not recall
of the worked example.

| Metric | With skill | Without skill | Δ |
|---|---|---|---|
| Assertion pass rate | **100%** | 50% | **+50 pts** |
| Eval-1 (FreshBooks, gated matrix) | 6/6 | 4/6 | |
| Eval-2 (Klaviyo, lift handoff) | 6/6 | 2/6 | |

## What the skill changed

| Assertion | With skill | Baseline |
|---|---|---|
| On-brief (right brand + medium) | ✓ both | ✗ eval-2 **invented a fake brand ("Solace Goods") and built emails, not ads** |
| Structured lift handoff for `lift-scorecard` | ✓ both (`arms.ai` ready to paste) | ✗ eval-1 ad-hoc markdown; eval-2 loose numbers |
| Gate actually held back risky variants | ✓ both (QB held a $-savings + a guaranteed-accuracy claim; MC held a deliverability guarantee) | ✗ both "all ship" — the gate never demonstrably bit |
| Methodology honesty | ✓ both (cost/time flagged as estimates) | ✗ eval-2 **fabricated an agency baseline ($450/asset, 7 days) and presented it as comparison** |

The two failure modes the skill prevented are exactly the ones that sink a real AI-creative pitch:
**drifting off-brief** and **fabricating the agency-comparison number**. The baseline was competent at
copywriting — it lost on the things that make AI creative *shippable and provable at scale*: a real
compliance gate that visibly bites, an output that plugs into the incrementality readout, and not
inventing the lift.

## Cost

With-skill runs spent ~90k tokens vs ~48k baseline — the skill does more work (builds the brand profile,
runs the gate, emits the manifest). That's the cost of producing a *provable, plug-compatible* batch
instead of a markdown deck. Reproduce: `evals/evals.json` holds the two prompts.

> Validated against a fresh agent — the skill also **triggered correctly** in both with-skill runs from
> its description alone.
