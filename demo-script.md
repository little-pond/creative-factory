# 2-Minute Loom — the closed AI campaign loop

A shot-by-shot storyboard. Goal: in 2 minutes, show one campaign go from *AI-search gap* → *mass-produced
on-brand creative* → *proven incremental lift*, all through self-built tools. Screen-record a terminal
(left) + the rendered ads / a scorecard (right). Times are cumulative.

---

**[0:00–0:12] Cold open — the thesis**
> "Most 'AI marketing' demos stop at 'look, it made an ad.' Here's the whole campaign loop, end to end —
> find what to say, mass-produce it on-brand and compliant, and *prove* it beat the agency. One campaign,
> all my own tools."

Show the loop diagram (README) for 3 seconds.

**[0:12–0:30] Stage 1 — GEO finds the angle**
On screen: the `geo-visibility-tracker` scorecard — TurboTax losing "is turbotax free" to FreeTaxUSA.
> "My GEO tracker found TurboTax is invisible on a high-intent query — 'is turbotax free.' That gap
> becomes the campaign angle: *free for simple returns.*"

**[0:30–0:52] Stage 2+3 — the factory builds the matrix**
Type:
```bash
python3 scripts/factory.py plan assets/turbotax.campaign.json --out plan.json
# PLAN: 18 variants = 3 formats × 3 pillars × 2 audiences
```
> "The factory expands format × message × audience — and that GEO angle drops in as a pillar. Eighteen
> variants, each pre-loaded with the exact Meta / LinkedIn / Google spec: dimensions, safe zones,
> character limits."

**[0:52–1:14] The gate bites (the money shot)**
Type:
```bash
python3 scripts/factory.py build assets/variants.example.json --out out --render-prompts
# 18 generated | 16 shippable | 1 BLOCK | 1 char-fail | brand_qa_pass_rate = 89%
```
> "Every variant runs the brand compliance gate. Sixteen ship automatically. It held back two: one that
> promised a 'guaranteed maximum refund' — a banned claim — and one headline that would truncate in a
> Google slot. *That's* what makes AI creative at scale safe in fintech — the machine catches the
> regulator-bait, not a human eyeballing 1,800 variants."

Cut to the 3 rendered hero ads (`assets/heroes/ads/`).
> "And these are real — rendered, then composited with the gate-passed copy at exact ad dimensions."

**[1:14–1:40] Stage 4+5 — prove the lift**
Type:
```bash
python3 ../experiment-designer/scripts/design.py ... # 80,679/arm — feasible
python3 ../lift-scorecard/scripts/lift.py loop_results.json
# VERDICT: SCALE AI | AI +18.0% lift | iCPA $41.67 vs $60
```
> "The factory's production numbers feed an incrementality test against the agency. Verdict: **scale AI** —
> eighteen percent incremental lift, cost per acquisition forty-two dollars versus sixty, at a twelfth of
> the agency's cost per asset and three days to launch instead of eighteen."

**[1:40–1:58] The proof-of-proof — benchmark**
Flash `evals/BENCHMARK.md`.
> "And I A/B-tested the tool itself on brands it had never seen — QuickBooks, Mailchimp. With the skill:
> a hundred percent. Without it, a fresh agent invented a fake brand and fabricated the agency number.
> The skill exists to stop exactly those two mistakes."

**[1:58–2:05] Close**
> "GEO to creative to proven lift — one loop, built to graduate from skill to MCP to production. That's
> AI-native campaign ops."

---

## Written-application version (2 sentences)

> I built an end-to-end AI campaign loop as working Claude Code tools: a GEO tracker finds the high-intent
> query a brand is losing, a creative-factory mass-produces on-brand variants to each platform's spec and
> auto-gates them for compliance (89% ship; banned claims held back), and an incrementality scorecard
> proves the lift — one TurboTax run came out **SCALE AI: +18% incremental lift, iCPA $41.67 vs $60, at
> 1/12 the agency's cost-per-asset**. Blind-tested on brands it had never seen, the factory scored 100%
> vs a 50% baseline that drifted off-brief and fabricated its agency comparison — the two failure modes
> the tool is designed to prevent.
