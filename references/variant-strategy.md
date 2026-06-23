# Variant Strategy

How to choose what the factory makes — so volume becomes lift, not just a big pile of assets.

## The matrix axes

The factory expands `format × message-pillar × audience`. Each axis earns its combinatorial cost only
if it changes the creative in a way that changes performance:

- **format** — non-negotiable. A Meta feed square, a TikTok 9:16 video, and a 728×90 banner are different
  creative objects; the same idea must be re-cut for each. This axis is about *fit*, not testing.
- **message-pillar** — the *idea* being tested. For TurboTax: confidence vs ease vs "free for simple
  returns". Different pillars are competing hypotheses about what moves the audience; the experiment will
  tell you which. Keep them genuinely distinct — two pillars that say the same thing waste impressions.
- **audience** — the *personalization* axis, and the one the JD cares most about ("moving from
  campaign-level testing toward audience-level personalization"). A first-time filer needs reassurance; a
  self-employed filer wants deductions. If the copy doesn't actually change for the segment, drop the
  axis — undifferentiated personalization is just duplication.

Matrix size is `formats × pillars × audiences`. It grows fast; that's the point (volume is a JD metric),
but every cell must be a creative someone would actually run. Prune before you generate, not after.

## Hooks (the first 1–3 seconds)

For video (Reels, TikTok in-feed) the hook decides everything — most of the audience is gone before the
value prop. When you write the `image_prompt` / opening frame, lead with the pattern interrupt or the
question, not the logo. `hook_rate` (3-second view / impression) is a field in the lift handoff precisely
because it's the leading indicator of whether the creative earns the watch.

## DCO and personalization at scale

Dynamic Creative Optimization is the productized version of this matrix: instead of shipping N finished
files, you ship the *components* (headlines, images, CTAs) and let the platform assemble per impression.
The factory's output maps to both:

- **Discrete variants** — ship each row as a finished asset (the default).
- **DCO feed** — treat the matrix as a component library: the pillar copy becomes the headline pool, the
  audience becomes the targeting key, the formats become the placements. Same manifest, assembled live.

Either way the brand gate runs first — DCO doesn't get to skip compliance just because a machine
assembles the final unit.

## The render step (hybrid)

The plan + manifest are deterministic and testable; rendering real images is optional and only for when
you need actual assets (a portfolio, a pitch, a real flight). Build with `--render-prompts` to emit
`render-queue.json`, then feed those prompts to an image tool — the `generate-image` skill for a quick
hero set, or Adobe Gen Studio / Celtra in a production org (where the brand profile becomes the trained
brand system and the templates the format scaffolds). Only render the *shippable* rows; the gate already
removed the rest, so you never spend render budget on a variant legal would block.

## Methodology honesty

This is the same discipline the rest of the portfolio holds to, and it's what separates a credible lift
claim from a marketing one:

- `assets` and `brand_qa_pass_rate` are **measured** by the build — trust them.
- `cost_per_asset`, `hours`, `time_to_launch_days` are **assumptions** until you measure them on a real
  flight. The manifest labels them; don't quietly turn a placeholder into a headline number.
- Volume and efficiency are production metrics. They are *not* lift. Only `lift-scorecard`, reading a real
  holdout, can say the AI creative drove *incremental* GNS. Carry the manifest all the way there before
  you claim the win — an unverified iROAS is worse than none.
