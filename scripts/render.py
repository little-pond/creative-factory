#!/usr/bin/env python3
"""
render.py — the hybrid render step, driven by the LOCAL creative stack.

In a big org this is where Adobe Gen Studio / Celtra would sit. In this environment the available
equivalent is OpenRouter image models (via the `generate-image` skill, which reads OPENROUTER_API_KEY
from ~/.env). This reads a `render-queue.json` (the shippable hero prompts emitted by
`factory.py build --render-prompts`) and renders each one — model-selectable.

Models on this OpenRouter key (pick with --model):
  google/gemini-3-pro-image-preview   (default — best quality; rendered the demo heroes)
  google/gemini-3.1-flash-image       (faster)
  google/gemini-2.5-flash-image       (cheapest — good for bulk drafts)
  openai/gpt-5-image | gpt-5-image-mini | gpt-5.4-image-2   (OpenAI option)
NOTE: no Adobe Gen Studio / Celtra / FLUX creds in this env — those would be drop-in here, not wired.

  python3 scripts/render.py out/render-queue.json --model google/gemini-2.5-flash-image --out heroes/ --limit 3
  python3 scripts/render.py out/render-queue.json --dry-run     # print plan, spend nothing
"""
import argparse
import json
import os
import subprocess
import sys

GENIMG = os.path.expanduser("~/.claude/skills/generate-image/scripts/generate_image.py")
DEFAULT_MODEL = "google/gemini-3-pro-image-preview"


def main():
    ap = argparse.ArgumentParser(description="Render shippable hero prompts via the local OpenRouter stack.")
    ap.add_argument("queue", help="render-queue.json from factory.py build --render-prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter image model id")
    ap.add_argument("--out", default="heroes", help="output dir")
    ap.add_argument("--limit", type=int, default=0, help="render at most N (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan without spending")
    a = ap.parse_args()

    items = [v for v in json.load(open(a.queue)) if v.get("image_prompt")]
    if a.limit:
        items = items[:a.limit]
    os.makedirs(a.out, exist_ok=True)
    if not os.path.exists(GENIMG):
        sys.exit(f"generate-image skill not found at {GENIMG}")

    done = 0
    for v in items:
        out = os.path.join(a.out, v["id"] + ".png")
        if a.dry_run:
            print(f"  DRY  {v['id']:<48} {a.model} → {out}")
            continue
        print(f"  render {v['id']} via {a.model}")
        r = subprocess.run([sys.executable, GENIMG, v["image_prompt"], "--model", a.model, "--output", out])
        done += (r.returncode == 0)
    verb = "planned" if a.dry_run else f"rendered {done}/{len(items)}"
    print(f"{verb} hero(es) with {a.model} → {a.out}  (then compose copy with scripts/compose.py)")


if __name__ == "__main__":
    main()
