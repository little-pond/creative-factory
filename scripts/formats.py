#!/usr/bin/env python3
"""
formats.py — the ad-format registry the creative factory builds against.

Each format = one platform placement with the things that decide whether an asset is shippable:
  - dims / aspect      : the canvas the creative renders on
  - safe (px margins)  : where platform UI (caption, CTA, profile icons) will sit on top of the
                         creative, so text/logo must stay OUT of these bands or it gets covered
  - limits (field->max): per-copy-field character ceilings (where exceeded text is truncated)
  - fields             : which copy fields this placement actually uses (Meta needs primary_text,
                         Google RSA doesn't; LinkedIn uses intro_text; TikTok a single caption)
  - asset              : "image" | "video" | "text" — drives whether an image_prompt is needed

These are the specs the JD means by "shipping production grade variants into ad platforms": a variant
isn't on-brand if its headline is 60 chars where the platform truncates at 40, or if the value prop
sits under the TikTok CTA bar. The factory validates every variant against this before it counts as
shippable.

NOTE: ad specs drift — platforms change limits and safe zones. Treat these as a sane, current-ish
default and verify against the live spec sheet before a real flight. Stdlib only.
"""

# platform -> placement -> spec
FORMATS = {
    "meta": {
        "feed": {
            "dims": [1080, 1080], "aspect": "1:1", "asset": "image",
            "safe": {"top": 0, "bottom": 0, "left": 0, "right": 0},
            "fields": ["primary_text", "headline", "description", "cta"],
            "limits": {"primary_text": 125, "headline": 40, "description": 30},
            "note": "Primary text truncates ~125 chars on mobile feed. 1:1 is the safe default; 4:5 (1080x1350) earns more real estate.",
        },
        "stories": {
            "dims": [1080, 1920], "aspect": "9:16", "asset": "image",
            "safe": {"top": 250, "bottom": 340, "left": 0, "right": 0},
            "fields": ["primary_text", "headline", "cta"],
            "limits": {"primary_text": 125, "headline": 40},
            "note": "Keep text/logo out of top ~14% (profile/close) and bottom ~18% (CTA). Full-bleed visual.",
        },
        "reels": {
            "dims": [1080, 1920], "aspect": "9:16", "asset": "video",
            "safe": {"top": 250, "bottom": 670, "left": 0, "right": 130},
            "fields": ["primary_text", "headline", "cta"],
            "limits": {"primary_text": 125, "headline": 40},
            "note": "Reels UI eats the bottom ~35% (caption + CTA + audio) and the right rail (icons). Hook in first 3s.",
        },
    },
    "google": {
        "rsa": {  # Responsive Search Ad — text only
            "dims": None, "aspect": None, "asset": "text",
            "safe": None,
            "fields": ["headline", "description"],
            "limits": {"headline": 30, "description": 90},
            "multiplicity": {"headline": 15, "description": 4},
            "note": "Search RSA: supply up to 15 headlines (30) + 4 descriptions (90); Google assembles. No image.",
        },
        "rda": {  # Responsive Display Ad
            "dims": [1200, 628], "aspect": "1.91:1", "asset": "image",
            "secondary_dims": [1200, 1200],
            "safe": None,
            "fields": ["headline", "long_headline", "description", "business_name", "cta"],
            "limits": {"headline": 30, "long_headline": 90, "description": 90, "business_name": 25},
            "note": "Provide landscape 1.91:1 + square 1:1 + a square logo. Don't bake text into the image — Google overlays its own.",
        },
    },
    "tiktok": {
        "infeed": {
            "dims": [1080, 1920], "aspect": "9:16", "asset": "video",
            "safe": {"top": 130, "bottom": 483, "left": 0, "right": 140},
            "fields": ["caption", "cta"],
            "limits": {"caption": 100},
            "note": "Native-first: looks like organic, not an ad. Right rail (icons) + bottom (handle/caption/CTA) are covered — keep key elements centred. Hook in 1-2s.",
        },
    },
    "linkedin": {
        "single_image": {
            "dims": [1200, 627], "aspect": "1.91:1", "asset": "image",
            "secondary_dims": [1200, 1200],
            "safe": None,
            "fields": ["intro_text", "headline", "cta"],
            "limits": {"intro_text": 150, "headline": 70},
            "note": "Intro text truncates ~150 on desktop; headline ~70 (less visible on mobile). B2B register, not consumer.",
        },
    },
    "dv360": {
        "display_300x250": {
            "dims": [300, 250], "aspect": "6:5", "asset": "image",
            "safe": None, "fields": ["headline", "cta"], "limits": {"headline": 35},
            "note": "Medium Rectangle — the workhorse. Text is baked into the HTML5/image; keep it to one line + CTA.",
        },
        "display_728x90": {
            "dims": [728, 90], "aspect": "8.09:1", "asset": "image",
            "safe": None, "fields": ["headline", "cta"], "limits": {"headline": 30},
            "note": "Leaderboard — very little height. One short line + CTA chip.",
        },
        "display_160x600": {
            "dims": [160, 600], "aspect": "4:15", "asset": "image",
            "safe": None, "fields": ["headline", "cta"], "limits": {"headline": 30},
            "note": "Wide Skyscraper — vertical; stack logo / headline / CTA.",
        },
        "display_320x50": {
            "dims": [320, 50], "aspect": "32:5", "asset": "image",
            "safe": None, "fields": ["headline", "cta"], "limits": {"headline": 25},
            "note": "Mobile banner — tiny. CTA-led, almost no body.",
        },
    },
}

# Sensible default placement(s) per platform when a campaign names a platform but not a placement.
DEFAULT_PLACEMENT = {
    "meta": ["feed", "stories"],
    "google": ["rsa", "rda"],
    "tiktok": ["infeed"],
    "linkedin": ["single_image"],
    "dv360": ["display_300x250", "display_728x90"],
}


def resolve_formats(spec_list):
    """Turn campaign 'formats'/'platforms' entries into concrete (platform, placement, spec) keys.

    Accepts 'meta:feed' (explicit placement) or 'meta' (expand to DEFAULT_PLACEMENT[meta]).
    Returns list of dicts: {key, platform, placement, spec}. Unknown keys are skipped with a note
    so a typo doesn't silently shrink the matrix — the caller reports skips.
    """
    out, skipped = [], []
    for raw in spec_list:
        raw = raw.strip()
        if ":" in raw:
            platform, placement = raw.split(":", 1)
            placements = [placement]
        else:
            platform = raw
            placements = DEFAULT_PLACEMENT.get(platform, [])
            if not placements:
                skipped.append(raw)
                continue
        for pl in placements:
            spec = FORMATS.get(platform, {}).get(pl)
            if not spec:
                skipped.append(f"{platform}:{pl}")
                continue
            out.append({"key": f"{platform}:{pl}", "platform": platform, "placement": pl, "spec": spec})
    return out, skipped


def check_lengths(copy, spec):
    """Validate a variant's copy dict against a format's char limits.

    Returns (ok, issues). issues = list of "field: 47/40" overflow strings. Fields the format
    doesn't use are ignored; a required field that's missing is flagged so a half-filled variant
    can't sneak through as 'passing'.
    """
    issues = []
    limits = spec.get("limits", {})
    fields = spec.get("fields", [])
    for field in fields:
        if field == "cta":
            continue  # CTA comes from an approved list, length-checked separately if needed
        val = copy.get(field)
        if val is None or val == "":
            issues.append(f"{field}: missing")
            continue
        mx = limits.get(field)
        if mx and len(val) > mx:
            issues.append(f"{field}: {len(val)}/{mx}")
    return (len(issues) == 0), issues


if __name__ == "__main__":
    # quick introspection: print the registry as a table
    print(f"{'key':<26} {'asset':<6} {'dims':<12} fields")
    for platform, placements in FORMATS.items():
        for pl, spec in placements.items():
            dims = "x".join(map(str, spec["dims"])) if spec.get("dims") else "(text)"
            print(f"{platform + ':' + pl:<26} {spec['asset']:<6} {dims:<12} {','.join(spec['fields'])}")
