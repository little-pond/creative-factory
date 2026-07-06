# Experiment Design — Northwind Tax TY25 prospecting — AI (Gen Studio) vs Agency creative

**Primary metric:** incremental new customers · **Confidence:** 95% · **Power:** 80%

## Hypothesis (pre-registered)

AI-produced creative drives >= 10% incremental lift in new customers at an iCPA <= the agency baseline.

## Design

- **Cells:** ai, agency, holdout
- **Randomization unit:** user
- **Method:** user-level holdout (incremental)

## Power & sizing

- Baseline conversion rate: 2.00%
- Target MDE (relative): 10%
- **Required sample per arm: 80,679**
- Total across 3 cells: 242,038
- Daily eligible per cell: 150,000
- **Estimated duration: 1 days**

## Pre-flight

**FEASIBLE — run ~1 days to detect 10% lift at 80% power.**

## Rough budget

- Assumptions: avg frequency 3, CPM $12
- Impressions per arm: 242,038 · Spend per exposed arm: ~$2,904
- **Total media (×2 exposed cells): ~$5,809**

## Guardrails

- Spend cap per arm; total cap.
- Compliance/brand-safety gate (fintech: legal-clear creative before serving).
- Kill criteria: pause an arm if iCPA exceeds {ceiling}, on policy violation, or brand-QA fail.

## Matching (kill confounds)

- Spend / audience / placement / flight parity across AI and agency arms.

## Analysis plan

Read out with **lift-scorecard** on the pre-registered primary metric and win condition. A results skeleton (`results_skeleton.json`) is generated to fill once the test completes.