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

# P1 — the universal anti-slop tail injected into every prompt so the hero doesn't come out as generic
# AI stock. Canonical list + rationale live in references/anti-slop-image.md; this is the compact form.
ANTI_SLOP = (
    " HARD CONSTRAINTS (do not relax): neutral / brand-true white balance, no AI yellow-tint cast; "
    "no purple or blue neon glow, no outer glow; no floating gradient blobs; no pure #000000 (use a deep "
    "neutral); no centered dark hero unless intended; no 3-equal-card row or generic dashboard spam; "
    "no Inter font unless brand-specified; no gradient text on headers; no sterile over-lit stock-photo "
    "look (allow natural grain and real texture); no plastic-retouched skin; no 'Elevate / Seamless / "
    "Unleash / Next-Gen / Reimagine' copy; no fake round numbers; no Acme / John Doe placeholder names."
)


def brand_constraints(brand_path):
    """Per-brand augmentation: pull the profile's palette + visual don'ts so the ban list is specific to
    this brand, not just the universal defaults. Returns '' if no usable profile."""
    if not brand_path or not os.path.exists(brand_path):
        return ""
    try:
        vis = json.load(open(brand_path)).get("visual", {})
    except Exception:
        return ""
    parts = []
    pal = vis.get("palette", {})
    if pal:
        parts.append("Use ONLY the brand palette (" + ", ".join(f"{k} {v}" for k, v in pal.items())
                     + "); do not invent new colors.")
    donts = (vis.get("imagery", {}) or {}).get("dont", [])
    if donts:
        parts.append("Brand visual don'ts: " + "; ".join(donts) + ".")
    return (" " + " ".join(parts)) if parts else ""


# --layout-ref — pass the placement layout to the model AS A VISUAL REFERENCE, so it reserves the copy
# space instead of only being asked in prose. The wireframe marks three zones; the instruction tells the
# model to treat it as structure, not content.
LAYOUT_INSTRUCTION = (
    " Use the attached image ONLY as a LAYOUT REFERENCE, not as content to copy. Generate a fresh "
    "photographic hero at the same proportions. Keep the focal subject inside the region marked FOCAL "
    "SUBJECT, and render the region marked COPY as simple, low-detail, uncluttered negative space suitable "
    "for text overlaid later. Keep important detail out of the PLATFORM UI bands. Do NOT reproduce any "
    "lines, boxes, labels, or text from the reference — output only the photograph."
)


def build_wireframe(dims, safe, copy_zone, path):
    """Draw a layout wireframe (needs Pillow): a COPY zone, a FOCAL-SUBJECT zone, and the platform-UI
    safe bands from formats.py. Fed to the image model via --input so it reserves the copy space."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = (dims or [1024, 1024])
    im = Image.new("RGB", (w, h), (232, 232, 230))
    d = ImageDraw.Draw(im, "RGBA")
    safe = safe or {}
    frac = 0.42
    if copy_zone == "top":
        cz = (0, 0, w, int(h * frac))
    elif copy_zone == "bottom":
        cz = (0, int(h * (1 - frac)), w, h)
    elif copy_zone == "left":
        cz = (0, 0, int(w * 0.5), h)
    else:  # right
        cz = (int(w * 0.5), 0, w, h)
    lw = max(2, w // 300)
    d.rectangle(cz, fill=(30, 94, 184, 55), outline=(30, 94, 184, 255), width=lw)
    # focal-subject region = the space opposite the copy band
    if copy_zone == "top":
        fz = (int(w * 0.08), cz[3], int(w * 0.92), int(h * 0.94))
    elif copy_zone == "bottom":
        fz = (int(w * 0.08), int(h * 0.06), int(w * 0.92), cz[1])
    elif copy_zone == "left":
        fz = (cz[2], int(h * 0.08), int(w * 0.94), int(h * 0.92))
    else:
        fz = (int(w * 0.06), int(h * 0.08), cz[0], int(h * 0.92))
    d.rectangle(fz, outline=(40, 160, 90, 255), width=lw)
    for edge, box in (("top", (0, 0, w, safe.get("top", 0))),
                      ("bottom", (0, h - safe.get("bottom", 0), w, h)),
                      ("left", (0, 0, safe.get("left", 0), h)),
                      ("right", (w - safe.get("right", 0), 0, w, h))):
        if safe.get(edge):
            d.rectangle(box, fill=(200, 40, 40, 70))
    try:
        f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", max(14, w // 34))
    except Exception:
        f = ImageFont.load_default()
    d.text((cz[0] + w * 0.02, cz[1] + h * 0.02), "COPY — simple negative space", fill=(20, 50, 110), font=f)
    d.text((fz[0] + w * 0.02, fz[1] + h * 0.02), "FOCAL SUBJECT", fill=(20, 90, 50), font=f)
    im.save(path)
    return path


def main():
    ap = argparse.ArgumentParser(description="Render shippable hero prompts via the local OpenRouter stack.")
    ap.add_argument("queue", help="render-queue.json from factory.py build --render-prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter image model id")
    ap.add_argument("--out", default="heroes", help="output dir")
    ap.add_argument("--limit", type=int, default=0, help="render at most N (0 = all)")
    ap.add_argument("--go", action="store_true", help="ACTUALLY render (spends on your OpenRouter key)")
    ap.add_argument("--max-cost", type=float, default=None, help="abort if the estimate exceeds this USD")
    ap.add_argument("--brand", help="brand-profile.json → inject its palette + visual don'ts (P1 anti-slop)")
    ap.add_argument("--no-anti-slop", action="store_true", help="disable the anti-slop prompt injection")
    ap.add_argument("--layout-ref", action="store_true",
                    help="pass a placement layout wireframe to the model as a visual reference (needs Pillow)")
    ap.add_argument("--copy-zone", default="bottom", choices=["top", "bottom", "left", "right"],
                    help="which zone the wireframe reserves for copy (default bottom)")
    a = ap.parse_args()

    if a.layout_ref:
        try:
            import PIL  # noqa: F401
        except Exception:
            sys.exit("--layout-ref needs Pillow (pip install pillow) to draw the wireframe.")

    items = [v for v in json.load(open(a.queue)) if v.get("image_prompt")]
    if a.limit:
        items = items[:a.limit]
    n = len(items)
    per = COST_PER_IMG.get(a.model, 0.02)
    est = per * n

    anti = "" if a.no_anti_slop else (ANTI_SLOP + brand_constraints(a.brand))

    print(f"model:      {a.model}")
    print(f"to render:  {n} hero(es)  ·  ~${per:.3f}/image")
    print(f"EST. COST:  ~${est:.2f}  (approximate — scales with resolution/tokens)")
    print(f"anti-slop:  {'OFF' if a.no_anti_slop else 'ON'}"
          f"{' + brand palette/donts' if (anti and a.brand) else ''}")
    print(f"layout-ref: {('ON (copy zone: ' + a.copy_zone + ')') if a.layout_ref else 'OFF'}")

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
        prompt = v["image_prompt"] + anti
        cmd = [sys.executable, GENIMG, "--model", a.model, "--output", out]
        if a.layout_ref:
            wf = os.path.join(a.out, v["id"] + ".layout.png")
            build_wireframe(v.get("dims"), v.get("safe"), a.copy_zone, wf)
            prompt += LAYOUT_INSTRUCTION
            cmd += ["--input", wf]
        cmd.append(prompt)
        r = subprocess.run(cmd)
        done += (r.returncode == 0)
        print(f"  {'✓' if r.returncode == 0 else '✗'} {v['id']}")
    print(f"\nrendered {done}/{n} → {a.out}  (compose copy with scripts/compose.py). "
          f"Actual spend ≈ ${per*done:.2f}.")


if __name__ == "__main__":
    main()
