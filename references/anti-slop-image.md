# Anti-slop rules for the render layer

**Why this exists.** Image-generation models default to a recognizable "AI ad" look — yellow-tint cast,
purple/blue neon glow, floating gradient blobs, a centered dark hero, stock-photo-perfect people, generic
3-equal-card layouts, and Inter-on-everything. Left alone, every hero a factory renders collapses toward
that lowest-common-denominator aesthetic and stops looking like *the brand*. `render.py` injects the block
below into every prompt so the hero reads on-brand instead of generic.

This is the render-side twin of the copy-side compliance gate: the gate keeps unsafe *words* from
shipping; anti-slop keeps generic *visuals* from shipping.

## Two moves per render

1. **Ban the defaults** — append the universal banned list (below) as hard constraints.
2. **Commit, don't drift** — the prompt must commit to specific, named choices (composition, lighting,
   palette from the brand profile) rather than leaving them to the model. Committing creates intent;
   letting the model pick creates slop. `render.py` folds the brand palette in as an explicit directive;
   the copy author's `image_prompt` should already name a composition + lighting rather than say
   "a nice background."

## Universal banned list (always injected)

**Color / light**
- ❌ AI yellow-tint cast — force a neutral or brand-true white balance
- ❌ purple/blue neon glow, outer glow on UI elements, neon haze on backgrounds
- ❌ floating meaningless gradient blobs; a gradient must serve the composition
- ❌ pure `#000000` — use the brand's deep neutral

**Composition**
- ❌ centered dark hero with the subject dead-center (unless the brand is genuinely that symmetric)
- ❌ 3 equal cards in a row / generic dashboard-card spam — use asymmetric or 2-column instead
- ❌ the same section cloned 3× with different text
- ❌ overlapping elements with no clean spatial zones

**Typography in image**
- ❌ Inter (overused) unless the brand profile explicitly chooses it
- ❌ generic Times/Georgia/Garamond serif — use a distinctive serif only if the brand calls for one
- ❌ gradient text on large headers

**People / photography**
- ❌ sterile, overlit, "too professional" Shutterstock energy — allow natural grain and imperfection
- ❌ the middle-aged-exec-pointing-at-a-chart stock archetype
- ❌ plastic-retouched skin — keep real texture unless the brand demands flawless

**Copy inside the image**
- ❌ "Elevate / Seamless / Unleash / Reimagine / Next-Gen / Empower" and their cousins
- ❌ fake round numbers ("99.99%", "10x", "50% off") presented as real metrics
- ❌ placeholder names — "Acme", "John Doe", "Nexus", "TechCo"

## Per-brand augmentation

On top of the universal list, `render.py` appends the brand profile's own visual "don'ts" when a
`--brand <profile.json>` is passed — it reads `visual.imagery.dont` (e.g. "no stock-cliché handshakes",
"no fear/stress imagery") and the palette, so the ban list is specific to the brand, not just generic.

## When a constraint conflicts with the brand

**Brand wins.** If a brand's own profile chooses Inter, pure black, or a centered symmetric hero, that is
the brand's call and overrides the universal default. The brand profile's `visual` block is authoritative;
the universal list is the default you fall back to when the brand is silent.
