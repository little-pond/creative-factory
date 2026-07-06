# heroes/ — the render output dir (nothing committed)

Rendered creative is **generated on demand, not checked in** — a fresh clone stays lean, and the assets
are always for *your* brand, not a bundled example. The hybrid render path produces them end to end:

```bash
# 1) emit the render queue for the shippable rows (the gate filtered the rest)
python3 scripts/factory.py build assets/variants.example.json --out out/ --render-prompts

# 2) render the visual layer via OpenRouter image models (spend-safe: no --go renders nothing)
python3 scripts/render.py out/render-queue.json --go --max-cost 0.50        # → assets/heroes/<id>.png

# 3) lay the gate-passed copy on top at exact platform dims
python3 scripts/compose.py --image assets/heroes/<id>.png --dims 1080x1080 --zone top \
    --headline "File with confidence" --body "First time filing? We guide every step." \
    --cta "Start for free" --brand "#1E5EB8" --wordmark "Northwind" --out assets/heroes/ads/<id>.png
```

## Why the two-step split (hero → composed ad)

`render.py` makes the **hero** (the visual layer, no copy). `compose.py` makes the **finished ad** (copy
laid on top). The split is deliberate: one hero serves many headlines/audiences — exactly how DCO / Gen
Studio reuse a single visual across a variant matrix.

## What the pipeline enforces for you

- **`render.py`** injects an anti-slop constraint block (`references/anti-slop-image.md`) into every
  prompt, so the hero reads on-brand instead of generic stock.
- **`compose.py`** keeps the copy **out of the placement's safe zone** (`formats.py` `safe_zone_px`) and
  checks a **legibility-contrast floor** against the hero pixels under the copy, auto-strengthening the
  scrim when it fails.

## Notes

- `render.py` bills your OpenRouter key (`OPENROUTER_API_KEY` in `~/.env`); `compose.py` needs Pillow.
  Both are the optional, non-stdlib render half — the core matrix/gate/manifest is pure stdlib.
- `compose.py`'s display font is Helvetica Neue / Arial as a stand-in — swap in the real brand font
  (`Inter` in the worked example) for production.
- Everything here is illustrative; the worked example brand ("Northwind Tax") is fictional.
