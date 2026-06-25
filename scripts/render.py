#!/usr/bin/env python3
"""
render.py — the hybrid render step, driven by the LOCAL creative stack.

In a big org this is where Adobe Gen Studio / Celtra would sit. Here the available equivalent is
OpenRouter image models (via the `generate-image` skill, which reads OPENROUTER_API_KEY from ~/.env).
Reads a `render-queue.json` (shippable hero prompts from `factory.py build --render-prompts`).

SPEND SAFETY: by default this renders NOTHING — it prints the plan + an estimated cost and stops.
You must pass --go to actually spend on the OpenRouter key. --max-cost aborts if the estimate exceeds it.

Models (pick with --model):
  google/gemini-3-pro-image-preview   (default — best quality)
  google/gemini-2.5-flash-image       (cheapest — bulk drafts)
  google/gemini-3.1-flash-image
  openai/gpt-5-image | gpt-5-image-mini | gpt-5.4-image-2
NOTE: no Adobe Gen Studio / Celtra / FLUX creds in this env — those would drop in here, not wired.

  python3 scripts/render.py out/render-queue.json                       # estimate only, spends $0
  python3 scripts/render.py out/render-queue.json --go --limit 3        # actually render 3
  python3 scripts/render.py out/render-queue.json --go --model google/gemini-2.5-flash-image
"""
import argparse
import json
import os
import subprocess
import sys

GENIMG = os.path.expanduser("~/.claude/skills/generate-image/scripts/generate_image.py")
DEFAULT_MODEL = "google/gemini-3-pro-image-preview"

# Approx USD per rendered image (~1024-1080px). Image models bill per output token (~1290 tok/Gemini
# image); these are rough — actual cost scales with resolution/tokens. Estimate only.
COST_PER_IMG = {
    "google/gemini-2.5-flash-image": 0.003,
    "google/gemini-3.1-flash-image": 0.004,
    "google/gemini-3-pro-image": 0.015,
    "google/gemini-3-pro-image-preview": 0.015,
    "openai/gpt-5-image-mini": 0.003,
    "openai/gpt-5-image": 0.02,
    "openai/gpt-5.4-image-2": 0.02,
}


def main():
    ap = argparse.ArgumentParser(description="Render shippable hero prompts via the local OpenRouter stack.")
    ap.add_argument("queue", help="render-queue.json from factory.py build --render-prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter image model id")
    ap.add_argument("--out", default="heroes", help="output dir")
    ap.add_argument("--limit", type=int, default=0, help="render at most N (0 = all)")
    ap.add_argument("--go", action="store_true", help="ACTUALLY render (spends on your OpenRouter key)")
    ap.add_argument("--max-cost", type=float, default=None, help="abort if the estimate exceeds this USD")
    a = ap.parse_args()

    items = [v for v in json.load(open(a.queue)) if v.get("image_prompt")]
    if a.limit:
        items = items[:a.limit]
    n = len(items)
    per = COST_PER_IMG.get(a.model, 0.02)
    est = per * n

    print(f"model:      {a.model}")
    print(f"to render:  {n} hero(es)  ·  ~${per:.3f}/image")
    print(f"EST. COST:  ~${est:.2f}  (approximate — scales with resolution/tokens)")

    if a.max_cost is not None and est > a.max_cost:
        sys.exit(f"ABORT: estimate ${est:.2f} exceeds --max-cost ${a.max_cost:.2f}")

    if not a.go:
        print("\nSpent $0. This was an estimate. Re-run with --go to actually render.")
        return

    if not os.path.exists(GENIMG):
        sys.exit(f"generate-image skill not found at {GENIMG}")
    os.makedirs(a.out, exist_ok=True)
    print(f"\n--go set → rendering {n} image(s)…")
    done = 0
    for v in items:
        out = os.path.join(a.out, v["id"] + ".png")
        r = subprocess.run([sys.executable, GENIMG, v["image_prompt"], "--model", a.model, "--output", out])
        done += (r.returncode == 0)
        print(f"  {'✓' if r.returncode == 0 else '✗'} {v['id']}")
    print(f"\nrendered {done}/{n} → {a.out}  (compose copy with scripts/compose.py). "
          f"Actual spend ≈ ${per*done:.2f}.")


if __name__ == "__main__":
    main()
