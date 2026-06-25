---
name: creative-factory
description: >-
  Mass-produce on-brand, spec-valid, compliance-gated ad creative variants from one campaign brief —
  the AI creative-production engine for Adobe Gen Studio / Celtra-style workflows. Expands a
  format x message-pillar x audience matrix into hundreds of variants, writes each to the exact platform
  spec (Meta, Google, TikTok, LinkedIn, DV360 dimensions, safe zones, and character limits), runs every
  one through the brand-system COMPLIANCE GATE so banned claims and missing disclaimers never ship, and
  emits a generation-manifest whose production-efficiency numbers (assets, cost-per-asset,
  brand-QA-pass-rate, time-to-launch) drop straight into experiment-designer / lift-scorecard to prove
  incremental lift over an agency baseline. This is the creative-production pillar that closes the
  end-to-end AI campaign loop: geo-content-brief (what to say) -> brand-system (voice + gate) ->
  creative-factory (the variants) -> experiment-designer + lift-scorecard (the incrementality readout).
  Use this whenever someone needs to generate ad creative at scale, build many on-brand variants, set up
  a Gen Studio / Celtra / DCO variant matrix, produce multi-format creative for paid social/search/
  programmatic, do audience-level creative personalization, batch-check generated ads for spec and
  compliance, or wire AI creative into a creative-volume / time-to-launch / lift experiment. Trigger on
  "generate ad variants", "creative at scale", "variant matrix", "Gen Studio", "Celtra", "DCO",
  "multi-format creative", "personalize creative by audience", "batch creative", "creative factory",
  "make 50 versions of this ad", "on-brand variants for Meta/TikTok/LinkedIn".
---

# Creative Factory

AI can write a thousand ad variants an hour. The job isn't generating them — it's that every one has to
hit the platform's character limit, stay out of the TikTok CTA bar, sound like the brand, and never
promise a guaranteed refund. A factory that emits 240 variants you still have to eyeball one-by-one
hasn't saved anyone anything. This skill makes "AI creative at scale" actually shippable: it owns the
mechanical half (matrix, specs, the compliance gate, the manifest) so the only thing left to human/LLM
judgment is the part that needs it — the actual words and the image.

It is the **creative-production pillar** of the campaign loop, and it plugs into the others:

```
 geo-content-brief ─┐  (what to say: answer-first claim, quotable facts)
                    ▼
 brand-system ─► CREATIVE-FACTORY ─► experiment-designer ─► lift-scorecard
 (voice + gate)   format × pillar ×   (size the AI-vs-       (incremental GNS /
                  audience matrix      agency test)           iROAS vs agency)
                  → manifest + gate
                  → (optional) rendered heroes
```

## Division of labor (read this first)

The script does what a machine should; you (the LLM) do what needs taste. Don't hand-build the matrix,
and don't ask the script to write copy.

- **`scripts/factory.py` (deterministic):** expands the matrix, injects each variant's exact format spec,
  validates character limits, runs the **brand compliance gate** (imports `brand-system`'s `check.py` —
  the same rule of record, not a copy, so it can't drift), computes `brand_qa_pass_rate`, and emits the
  manifest + the `lift-scorecard` handoff.
- **You (judgment):** write the headline / body / CTA and the image prompt for each cell, in brand voice,
  to spec, without tripping the compliance rules. The plan step hands you the exact constraints per cell
  so you write it right the first time instead of trimming after.

## Workflow

### Step 1 — Plan the matrix

Start from a `campaign.json` (clone `assets/campaign.template.json`; `assets/turbotax.campaign.json` is a
worked Intuit example). It points at a `brand-system` brand-profile for voice + audiences + the gate, then
names the formats and messaging axes. To close the GEO half of the loop, lift the answer-first claim and
quotable facts from a `geo-content-brief` into `messaging.geo_angles` — the factory treats them as extra
pillars, so GEO research becomes creative input instead of a dead-end document.

```bash
python3 scripts/factory.py plan assets/turbotax.campaign.json --out variant-plan.json
```

This expands `format × pillar × audience` into one row per variant, each pre-loaded with `dims`,
`safe_zone_px`, `char_limits`, the `fields_needed` for that placement, and empty `copy` slots. See
`references/format-specs.md` for the full registry and `references/variant-strategy.md` for how to choose
the axes (and why audience-level beats campaign-level).

### Step 2 — Fill the copy (this is your job)

For each variant in `variant-plan.json`, write the copy into its `copy` slots and an `image_prompt` for
image/video formats. Honor three constraints at once — they're all in the row:

1. **Spec** — stay under each field's `char_limits`; keep key elements out of `safe_zone_px`.
2. **Voice** — use the profile's `voice` (do/don't, tone) so 18 variants still sound like one brand.
3. **Compliance** — never write the profile's banned claims; include a required disclaimer's marker (or
   route it to fine print) when you use its trigger words. Writing to the gate is cheaper than getting
   blocked by it.

Make each cell genuinely *for* its pillar and audience — a first-time filer needs reassurance, a
self-employed filer wants deductions. Same offer, different angle: that's the personalization the loop is
trying to prove pays off. Save the filled file as `variants.json` (`assets/variants.example.json` shows a
filled TurboTax matrix, including a couple deliberately held back so you can see the gate bite).

### Step 3 — Build: validate, gate, manifest

```bash
python3 scripts/factory.py build variants.json --brand ../brand-system/assets/turbotax.brand.json --out out/
```

Every variant gets char-limit-checked and run through the compliance gate. The result is
`out/generation-manifest.json` + a readable `out/compliance-report.md`:

- **`summary.brand_qa_pass_rate`** = shippable / generated — your headline production-quality number.
- **`production_efficiency`** — `assets` (cleared both gates) and `brand_qa_pass_rate` are *measured here*;
  `cost_per_asset` / `hours` / `time_to_launch_days` come from the campaign's `production` block and must
  be real measured values before you claim lift (the skill labels them as such — don't fabricate).
- **`lift_handoff["arms.ai"]`** — paste straight into a `lift-scorecard` `results.json` as the AI arm.

A **BLOCK** doesn't ship — and it's a signal to fix the *prompt/template upstream*, not just that one line.
A recurring block means the brief is wrong. Log it, fix the generation instruction, regenerate.

### Step 4 — (Optional, hybrid) Render the hero variants

The matrix + manifest are pure-compute and testable. To produce real assets, add `--render-prompts` to the
build to emit `render-queue.json`, then render the visual layer and lay the gate-passed copy on top.

**Render — the production stack.** `scripts/render.py` drives the render via **OpenRouter image models**
(the locally-available equivalent of Adobe Gen Studio / Celtra — those would be a drop-in here but need
their own creds). It calls the `generate-image` skill, which reads `OPENROUTER_API_KEY` from `~/.env`:

```bash
python3 scripts/render.py out/render-queue.json --out heroes/ \
    --model google/gemini-3-pro-image-preview     # default: best quality (rendered the demo heroes)
# alternatives: google/gemini-2.5-flash-image (cheapest, bulk drafts) · google/gemini-3.1-flash-image
#               openai/gpt-5-image | gpt-5-image-mini | gpt-5.4-image-2 (OpenAI option)
python3 scripts/render.py out/render-queue.json --dry-run   # plan only, spends nothing
```

**Compose** the finished ad (copy on the rendered hero, exact platform dims) with `scripts/compose.py`:

```bash
python3 scripts/compose.py --image heroes/hero.png --dims 1080x1080 --zone top \
    --headline "File with confidence" --body "First time filing? We guide every step." \
    --cta "Start for free" --out out/ad.png
```

Render only the *shippable* rows — the gate filtered the rest. `assets/heroes/` holds a worked set
(3 heroes → 3 composed ads). `render.py` uses your OpenRouter key (costs per image); `compose.py` needs
Pillow. Both are the optional, non-stdlib render half.

### Step 5 — Close the loop

The manifest's `lift_handoff` is the bridge to incrementality:

1. Feed the matrix size + brand QA rate into **`experiment-designer`** to size an AI-vs-agency-vs-holdout
   test (clone its `design.json`, set the AI arm's production fields from the manifest).
2. After the flight, fill the performance fields and run **`lift-scorecard`** for incremental GNS / iCPA /
   iROAS vs the agency arm — the proof that AI creative drove *incremental* growth, not just volume.

That chain — geo-content-brief → brand-system → creative-factory → experiment-designer → lift-scorecard —
is "embed AI into the campaign loop end to end" made concrete.

## Quality bar

- **Spec compliance is binary, not a vibe.** A 47-char headline in a 40-char slot gets truncated mid-word
  in the wild. The factory fails it; so should you. Write to the limit in the row.
- **The gate has the final say on shipping.** Don't let a clever variant talk its way past a blocker.
  Safe variants flow automatically; unsafe ones route to legal. That automation *is* the scale.
- **One brand across N variants.** The point of feeding the brand profile in is that variant #200 sounds
  like variant #1. Drift is the failure mode of volume — voice is what makes it on-brand, not just a lot.
- **Personalize on a real difference.** Audience axes earn their combinatorial cost only if the copy
  actually changes for the segment. If two audiences get the same line, collapse them.
- **Volume is the input; lift is the output.** "We made 240 variants" is not a win. "240 variants, 96%
  cleared the gate, +18% incremental GNS at one-third the agency's cost-per-asset" is. Always carry the
  manifest through to the lift readout — that's the number the role is hired to move.
- **Don't fabricate efficiency numbers.** `assets` and `brand_qa_pass_rate` are measured; cost/hours/days
  must be real. An invented iROAS is worse than no iROAS.

## Files

- `scripts/factory.py` — `plan` (matrix → work order) and `build` (validate + gate + manifest + handoff).
- `scripts/formats.py` — the platform format registry (dims, safe zones, char limits) + validators.
- `scripts/render.py` — (optional) render shippable hero prompts via OpenRouter image models (Gemini 3 Pro Image default; Gemini Flash / OpenAI gpt-5-image selectable). The Adobe-Gen-Studio-equivalent in this env.
- `scripts/compose.py` — (optional, needs Pillow) lay gate-passed copy onto a rendered hero → finished ad.
- `references/format-specs.md` — the registry in human-readable form, with per-platform notes.
- `references/variant-strategy.md` — choosing the matrix axes, hooks, DCO, audience personalization,
  the render step, and methodology honesty.
- `assets/campaign.template.json` — blank campaign input to clone.
- `assets/turbotax.campaign.json` — worked Intuit example (with a GEO-fed angle).
- `assets/variants.example.json` — a filled TurboTax matrix (incl. variants the gate holds back).
- `assets/manifest.example.json` — example build output.
- `assets/heroes/` — a worked render set: 3 rendered heroes → 3 composed finished ads (+ gallery README).
