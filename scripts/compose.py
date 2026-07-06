#!/usr/bin/env python3
"""
compose.py — the finishing step of the hybrid render path: take a rendered hero (the pure visual layer)
plus a variant's approved copy, and lay them up into a finished-ad mockup at the exact platform size.

Copy is laid out to a LAYOUT FORMULA from 《排版的力量·54个排版公式》 (see scripts/formulas.py): the
formula sets margins, alignment, line-spacing, negative-space ratio and headline opacity, and a small
metadata line is added (the book's "小字当肌理" scale-jump craft rule). Pick one with --formula
(id like 43, or an intent like premium/minimal/centered); default is the zone's natural formula.

It also ENFORCES two gates:
  P0 safe zone — pass --placement meta:stories and the layout is INSET to safe_zone_px, then re-checked;
                 a residual violation fails the compose (exit 2) unless --warn-safe.
  P2 contrast — samples the hero under the copy and ramps a text plate until it clears --contrast-min.

Fonts: Helvetica Neue / Arial as a stand-in for the brand display font (Inter) — swap for production.
Requires Pillow. Example:

    python3 scripts/compose.py --image assets/heroes/hero.png --dims 1080x1920 --zone bottom \\
        --placement meta:stories --formula 43 --headline "File with confidence" \\
        --body "First time filing? We guide every step." --cta "Start for free" \\
        --brand "#1E5EB8" --wordmark "Northwind" --out out/ad.png
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formats as fmt  # noqa: E402
import formulas as flib  # noqa: E402

FONT_CANDIDATES = {
    "bold": ["/System/Library/Fonts/HelveticaNeue.ttc",
             "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "regular": ["/System/Library/Fonts/HelveticaNeue.ttc",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def load_font(kind, size):
    for p in FONT_CANDIDATES[kind]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cover(img, w, h):
    src_w, src_h = img.size
    scale = max(w / src_w, h / src_h)
    nw, nh = int(src_w * scale + 0.5), int(src_h * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def align_x(tx, max_tw, line_w, align):
    if align == "center":
        return tx + (max_tw - line_w) / 2
    if align == "right":
        return tx + (max_tw - line_w)
    return tx


# ---- P2: WCAG contrast helpers ----
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(rgb):
    r, g, b = (_lin(rgb[i]) for i in range(3))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def region_mean(rgb_img, box):
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(rgb_img.width, max(x1, x0 + 1)), min(rgb_img.height, max(y1, y0 + 1))
    return rgb_img.crop((x0, y0, x1, y1)).resize((1, 1), Image.BILINEAR).getpixel((0, 0))[:3]


def compose(args):
    w, h = (int(x) for x in args.dims.lower().split("x"))
    brand = hexrgb(args.brand)
    img = cover(Image.open(args.image).convert("RGB"), w, h)
    scratch = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    # ---- pick the layout formula (from 《排版的力量·54个排版公式》) ----
    fid, F = flib.resolve(args.formula, args.zone)
    align = F["align"]
    pad = int(w * F["margin_pct"])
    line_mult = F["line_spacing"]
    copy_frac = min(0.5, max(0.30, 1 - F["negative_space"]))  # how much of the canvas copy may occupy
    head_op = int(255 * F.get("headline_opacity", 1.0))

    head_f = load_font("bold", int(w * 0.062))
    body_f = load_font("regular", int(w * 0.032))
    cta_f = load_font("bold", int(w * 0.034))
    mark_f = load_font("bold", int(w * 0.030))
    meta_f = load_font("bold", max(11, int(w * 0.012)))  # scale-jump: hero ≫ metadata (book §1)

    # ---- P0: safe insets ----
    safe = {}
    if args.placement:
        plat, _, plc = args.placement.partition(":")
        spec = fmt.spec_for(plat, plc)
        if not spec:
            print(f"  warn: unknown placement '{args.placement}' — safe zone not applied")
        else:
            safe = spec.get("safe") or {}
    st, sb = safe.get("top", 0), safe.get("bottom", 0)
    sl, sr = safe.get("left", 0), safe.get("right", 0)
    top_lim, bot_lim, left_lim, right_lim = st, h - sb, sl, w - sr

    is_panel = args.zone in ("left", "right")
    if is_panel:
        col_w = int(w * 0.46)
        x0 = max(pad, left_lim + pad) if args.zone == "left" else min(w - col_w, right_lim - col_w)
        tx, max_tw, text_color = x0, col_w - pad, hexrgb("#1A1A1A")
    else:
        tx = max(pad, left_lim + pad)
        max_tw, text_color = (right_lim - pad) - tx, (255, 255, 255)

    head_adv = int(head_f.size * 1.18)
    body_adv = int(body_f.size * line_mult)
    gap_body, gap_cta = int(w * 0.012), int(w * 0.025)
    pill_h = int(cta_f.size * 2.0)

    head_lines = wrap(scratch, args.headline, head_f, max_tw)
    body_lines = wrap(scratch, args.body, body_f, max_tw) if args.body else []
    copy_h = len(head_lines) * head_adv + (gap_body + len(body_lines) * body_adv if body_lines else 0)
    block_h = copy_h + (gap_cta + pill_h if args.cta else 0)

    if is_panel:
        head_y = min(max(int(h * 0.18), top_lim + pad), bot_lim - pad - block_h)
    elif args.zone == "top":
        head_y = top_lim + pad
    else:  # bottom
        head_y = max(top_lim + pad, (bot_lim - pad) - block_h)

    positions, y = [], head_y
    for ln in head_lines:
        positions.append((head_f, ln, y, head_op))
        y += head_adv
    if body_lines:
        y += gap_body
        for ln in body_lines:
            positions.append((body_f, ln, y, 255))
            y += body_adv
    copy_box = (tx, head_y, tx + max_tw, y)

    cta_box = None
    if args.cta:
        y += gap_cta
        ctw = scratch.textlength(args.cta, font=cta_f)
        pill_w = int(ctw + w * 0.06)
        cx = align_x(tx, max_tw, pill_w, align)
        cta_box = (cx, y, cx + pill_w, y + pill_h)

    mw = scratch.textlength(args.wordmark, font=mark_f)
    mx = min(right_lim - pad - mw, w - pad - mw) if args.zone in ("left", "top") else max(left_lim + pad, pad)
    my = (top_lim + pad) if args.zone == "bottom" else (bot_lim - pad - mark_f.size)
    mark_box = (mx, my, mx + mw, my + mark_f.size)

    # metadata micro-line (book §4 "小字当肌理"): a real, small tag opposite the wordmark
    meta_txt = args.meta or f"CF · {fid} {F['zh']}·{F['en']}"

    # ---- P2: base scrim + a text plate that ramps until contrast clears the floor ----
    band_h = int(h * (copy_frac + 0.02))

    def base_scrim():
        ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(ov)
        if is_panel:
            dd.rectangle([tx - pad, 0, tx + max_tw + pad, h], fill=(255, 255, 255, 205))
        else:
            for i in range(band_h):
                a = int(150 * (1 - i / band_h)) if args.zone == "top" else int(150 * (i / band_h))
                yy = i if args.zone == "top" else h - band_h + i
                dd.line([(0, yy), (w, yy)], fill=(20, 30, 60, a))
        return ov

    light_text = rel_lum(text_color) > 0.5
    plate_rgb = (12, 16, 30) if light_text else (255, 255, 255)
    m = int(w * 0.02)
    plate_box = (copy_box[0] - m, copy_box[1] - m, copy_box[2] + m, copy_box[3] + m)

    overlay, ratio = base_scrim(), 0.0
    for plate_a in (0, 120, 150, 185, 215, 242):
        overlay = base_scrim()
        if plate_a:
            ImageDraw.Draw(overlay).rounded_rectangle(list(plate_box), radius=int(w * 0.02),
                                                      fill=plate_rgb + (plate_a,))
        comp = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        ratio = contrast_ratio(text_color, region_mean(comp, copy_box))
        if ratio >= args.contrast_min:
            break

    # ---- draw copy onto the chosen overlay, aligned per the formula ----
    d = ImageDraw.Draw(overlay)
    for f, ln, ly, op in positions:
        lw = scratch.textlength(ln, font=f)
        d.text((align_x(tx, max_tw, lw, align), ly), ln, font=f, fill=text_color + (op,))
    if cta_box:
        x0c, y0c, x1c, y1c = cta_box
        d.rounded_rectangle([x0c, y0c, x1c, y1c], radius=(y1c - y0c) // 2, fill=brand + (255,))
        ctw = scratch.textlength(args.cta, font=cta_f)
        d.text((x0c + (x1c - x0c - ctw) / 2, y0c + (y1c - y0c - cta_f.size) / 2 - 2),
               args.cta, font=cta_f, fill=(255, 255, 255))
    d.text((mark_box[0], mark_box[1]), args.wordmark, font=mark_f,
           fill=brand if is_panel else (255, 255, 255))
    # metadata line in the corner opposite the wordmark
    meta_w = scratch.textlength(meta_txt, font=meta_f)
    meta_x = max(left_lim + pad, pad) if args.zone in ("left", "top") else min(right_lim - pad - meta_w, w - pad - meta_w)
    meta_y = (top_lim + pad) if args.zone == "bottom" else (bot_lim - pad - meta_f.size)
    d.text((meta_x, meta_y), meta_txt, font=meta_f, fill=(text_color + (150,)) if not is_panel else brand + (170,))

    out = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    out.save(args.out)

    # ---- P0: re-check final boxes against the safe zone ----
    boxes = [("copy", *copy_box)] + ([("cta", *cta_box)] if cta_box else []) + [("wordmark", *mark_box)]
    violations = fmt.safe_zone_violations(spec, boxes, w, h) if safe else []

    cflag = "OK" if ratio >= args.contrast_min else f"LOW (best {ratio:.1f})"
    print(f"composed {args.dims} ad -> {args.out}  ·  formula {fid} {F['zh']}·{F['en']} "
          f"(align {align}, 留白 {F['negative_space']:.0%})  ·  contrast {ratio:.1f}:1 {cflag}")
    if violations:
        for name, edge, over in violations:
            print(f"  SAFE-ZONE VIOLATION: '{name}' intrudes {over}px into the {edge} band "
                  f"({args.placement} — platform UI would cover it)")
        if not args.warn_safe:
            sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--dims", required=True, help="WxH, e.g. 1080x1080")
    ap.add_argument("--zone", default="top", choices=["top", "bottom", "left", "right"])
    ap.add_argument("--formula", help="layout formula id (e.g. 43) or intent (premium/minimal/centered/"
                    "asymmetric/fullbleed/module); default = the zone's natural formula")
    ap.add_argument("--meta", help="small metadata line (book §4 texture); default = the formula tag")
    ap.add_argument("--placement", help="platform:placement (e.g. meta:stories) → inset to + enforce safe zone")
    ap.add_argument("--warn-safe", action="store_true", help="report safe-zone violations but don't fail")
    ap.add_argument("--contrast-min", type=float, default=4.5, help="WCAG contrast floor for copy on hero")
    ap.add_argument("--headline", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--cta", default="")
    ap.add_argument("--brand", default="#1E5EB8", help="brand hex for CTA/wordmark")
    ap.add_argument("--wordmark", default="Northwind")
    ap.add_argument("--out", required=True)
    compose(ap.parse_args())


if __name__ == "__main__":
    main()
