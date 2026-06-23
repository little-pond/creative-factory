#!/usr/bin/env python3
"""
compose.py — the finishing step of the hybrid render path: take a rendered hero (the pure visual layer)
plus a variant's approved copy, and lay them up into a finished-ad mockup at the exact platform size.

This is deliberately the *last* mile and a separate step from generation, because that's how real DCO /
Gen Studio pipelines work: the model renders the image layer, and copy is composited on top per
placement (so one hero serves many headlines/audiences). Here it produces a believable preview of the
final unit — resized to spec, a legibility scrim over the copy zone, headline + body + a brand CTA pill.

Fonts: uses Helvetica Neue / Arial as a stand-in for the brand display font (Avenir Next) — swap in the
real brand font for production. Requires Pillow. Example:

    python3 scripts/compose.py --image assets/heroes/hero.png --dims 1080x1080 --zone top \\
        --headline "File with confidence" --body "First time filing? We guide every step." \\
        --cta "Start for free" --brand "#355EBE" --out out/ad.png
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

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
    """Resize+center-crop the image to exactly fill w×h (like CSS object-fit: cover)."""
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


def compose(args):
    w, h = (int(x) for x in args.dims.lower().split("x"))
    brand = hexrgb(args.brand)
    img = cover(Image.open(args.image).convert("RGB"), w, h)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    pad = int(w * 0.05)
    # copy column geometry by zone
    if args.zone in ("left", "right"):
        col_w = int(w * 0.46)
        x0 = pad if args.zone == "left" else w - col_w
        # soft white panel for legibility on the copy side
        panel = (255, 255, 255, 205)
        d.rectangle([x0 - pad, 0, x0 + col_w, h], fill=panel)
        tx, max_tw, text_color = x0, col_w - pad, hexrgb("#1A1A1A")
        head_y = int(h * 0.18)
    else:  # top / bottom — gradient scrim + light text
        band_h = int(h * 0.42)
        for i in range(band_h):
            a = int(150 * (1 - i / band_h)) if args.zone == "top" else int(150 * (i / band_h))
            y = i if args.zone == "top" else h - band_h + i
            d.line([(0, y), (w, y)], fill=(20, 30, 60, a))
        tx, max_tw, text_color = pad, w - 2 * pad, (255, 255, 255)
        head_y = int(h * 0.07) if args.zone == "top" else int(h * 0.60)

    head_f = load_font("bold", int(w * 0.062))
    body_f = load_font("regular", int(w * 0.032))
    cta_f = load_font("bold", int(w * 0.034))

    y = head_y
    for line in wrap(d, args.headline, head_f, max_tw):
        d.text((tx, y), line, font=head_f, fill=text_color)
        y += int(head_f.size * 1.18)
    if args.body:
        y += int(w * 0.012)
        for line in wrap(d, args.body, body_f, max_tw):
            d.text((tx, y), line, font=body_f, fill=text_color)
            y += int(body_f.size * 1.3)

    # CTA pill
    if args.cta:
        y += int(w * 0.025)
        tw = d.textlength(args.cta, font=cta_f)
        pill_w, pill_h = int(tw + w * 0.06), int(cta_f.size * 2.0)
        d.rounded_rectangle([tx, y, tx + pill_w, y + pill_h], radius=pill_h // 2, fill=brand + (255,))
        d.text((tx + (pill_w - tw) / 2, y + (pill_h - cta_f.size) / 2 - 2), args.cta,
               font=cta_f, fill=(255, 255, 255))

    # small brand wordmark, opposite corner from copy
    mark_f = load_font("bold", int(w * 0.030))
    mark = args.wordmark
    mw = d.textlength(mark, font=mark_f)
    mx = w - pad - mw if args.zone in ("left", "top") else pad
    d.text((mx, h - pad - mark_f.size), mark, font=mark_f,
           fill=brand if args.zone in ("left", "right") else (255, 255, 255))

    out = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    out.save(args.out)
    print(f"composed {args.dims} ad -> {args.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--dims", required=True, help="WxH, e.g. 1080x1080")
    ap.add_argument("--zone", default="top", choices=["top", "bottom", "left", "right"])
    ap.add_argument("--headline", required=True)
    ap.add_argument("--body", default="")
    ap.add_argument("--cta", default="")
    ap.add_argument("--brand", default="#355EBE", help="brand hex for CTA/wordmark")
    ap.add_argument("--wordmark", default="TurboTax")
    ap.add_argument("--out", required=True)
    compose(ap.parse_args())


if __name__ == "__main__":
    main()
