# Creative Factory — Northwind Tax TY25 prospecting — AI (Gen Studio) creative pilot (Northwind Tax)

## ⛔ 16/18 shippable · brand QA pass rate 89%

- Blocked: 1  ·  Review required: 0  ·  Char-limit fails: 1
- Compliance gate: brand-system check.py

### Held back (fix upstream, then regenerate)

| Variant | Char | Compliance | Issue |
|---|---|---|---|
| meta_feed__confidence__self_employed | PASS | BLOCK | outcome_promise (`guaranteed maximum refund`); guarantee_word (`guarantee`); missing_disclaimer:max_refund (`maximum refund`) |
| google_rsa__ease__self_employed | FAIL | PASS | headline: 38/30 |

### Production efficiency (for the lift readout)

| Metric | Value |
|---|---|
| assets | 16 |
| variants_generated | 18 |
| brand_qa_pass_rate | 0.8889 |
| cost_per_asset | 120 |
| hours | 60 |
| time_to_launch_days | 3 |

### Provenance (reproducibility)

- Built: `2026-07-06T22:12:53+00:00`
- Brand profile: `sha256:160ca87c7bb98d9f274c7b5fdd537dadeb86d130039b313c0b40729212a7753f`
- Gate ruleset: `sha256:5748ad2e7831ecbd6aea86c7b5b3c98772c7e72e5b7f2d4515598092b892bc88`
- _Same two hashes ⇒ the same rules gated this batch — record with the compliance sign-off._

_Next: fill the perf fields in `lift_handoff` after the flight and run `lift-scorecard` for incremental new customers / iROAS vs the agency arm._