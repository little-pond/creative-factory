#!/usr/bin/env python3
"""
formulas.py — a small, self-contained encoding of the STRUCTURAL layout formulas from
《排版的力量·54个排版公式》 (The Power of Layout — 54 Typography Formulas), used to drive the render
wireframe (where the hero reserves copy space) and the compose typesetting (how copy is laid out).

Only the 8 structure/composition formulas relevant to ad heroes are vendored here, each reduced to the
quantified knobs the pipeline actually consumes (margins, negative-space %, alignment, line-spacing,
headline opacity, focal rule). The prose, mnemonics, and the 261 例图 live in the `typography-formulas`
skill; example_image_path() resolves them if that skill is installed. Numbers are from the book's
「具体操作」 sections — see references/01-structure-composition.md there.

Craft rules (from 00-craft-and-impact.md) that the compose step honors regardless of formula:
  scale jump ≥ 10× (one hero, tiny metadata) · off-center focus (1/3 or golden) · 40–60% negative space,
  asymmetric · ≤ 3 colors · abundant real micro-copy as texture.
"""
import os

# scale contrast between the hero headline and the micro-metadata line (book §1: ≥ 10:1)
SCALE_JUMP = 10
NEG_SPACE_RANGE = (0.40, 0.60)   # book §8: keep 40–60% real negative space, biased to one side

# id -> formula knobs. `copy_zones` = which compose --zone this formula naturally supports.
FORMULAS = {
    "01": {"zh": "全屏排版", "en": "Full-screen", "mnemonic": "满而不塞,光做留白;文字浮,背景活",
           "use": "cover / hero / full-bleed image", "copy_zones": ["top", "bottom"],
           "align": "left", "margin_pct": 0.06, "negative_space": 0.35, "line_spacing": 1.5,
           "headline_opacity": 0.93, "mask_opacity": 0.20, "focal": "lower_third", "full_bleed": True,
           "recipe": "atmospheric full-bleed image (soft light / haze), subject offset leaving one empty "
                     "block; keep the reserved block a clean low-detail negative space for a huge headline"},
    "05": {"zh": "模块排版", "en": "Module", "mnemonic": "格定形,重分序,疏密见节,留白成韵",
           "use": "data slide / carousel / info-dense", "copy_zones": ["top", "bottom", "left", "right"],
           "align": "left", "margin_pct": 0.06, "negative_space": 0.30, "line_spacing": 1.5,
           "headline_opacity": 1.0, "grid_cols": 12, "row_gap": 0.12, "col_gap": 0.07, "focal": "grid",
           "recipe": "clean modular grid background, calm even lighting, room for a title module and "
                     "supporting blocks; no clutter"},
    "07": {"zh": "非对称排版", "en": "Asymmetry", "mnemonic": "偏不乱,重不坠;虚实对,线引势",
           "use": "art / fashion / editorial hero + headline", "copy_zones": ["left", "right", "bottom"],
           "align": "left", "margin_pct": 0.06, "negative_space": 0.50, "line_spacing": 1.5,
           "headline_opacity": 1.0, "focal": "third", "asymmetric": True,
           "recipe": "subject pushed off-center to one third / a corner, the opposite side a large empty "
                     "negative space for a headline; editorial tension"},
    "08": {"zh": "中心排版", "en": "Centered", "mnemonic": "中有点,边有气;虚带实,静生力",
           "use": "logo / launch key visual / welcome / empty state", "copy_zones": ["top", "bottom"],
           "align": "center", "margin_pct": 0.08, "negative_space": 0.60, "line_spacing": 1.5,
           "headline_opacity": 1.0, "focal": "center_up", "centered": True,
           "recipe": "single subject at the exact center (nudged up ~2%), even airflow on all sides, "
                     "50–70% calm negative space, soft center spotlight"},
    "11": {"zh": "留白排版", "en": "White Space", "mnemonic": "少不是缺,是力的聚焦",
           "use": "premium brand / editorial minimal", "copy_zones": ["top", "bottom", "left", "right"],
           "align": "left", "margin_pct": 0.10, "negative_space": 0.60, "line_spacing": 1.5,
           "headline_opacity": 1.0, "focal": "third", "minimal": True,
           "recipe": "a single object on a seamless background with a very large empty area; airy, calm, "
                     "8–12% wide margins of pure negative space"},
    "43": {"zh": "上下排版", "en": "Up-and-Down", "mnemonic": "上定焦,下定稳;距一算,轴不乱",
           "use": "brand / UI / portfolio — top-bottom split", "copy_zones": ["top", "bottom"],
           "align": "center", "margin_pct": 0.06, "negative_space": 0.50, "line_spacing": 1.5,
           "headline_opacity": 1.0, "focal": "band", "gap_rule": "top_zone_h * 0.8–1.6",
           "recipe": "subject held in the middle band, a clean horizontal negative-space band reserved "
                     "top or bottom for the copy; strong up/down hierarchy"},
    "44": {"zh": "左右排版", "en": "Left-and-Right", "mnemonic": "左讲逻辑,右给空间",
           "use": "poster / social cover / split", "copy_zones": ["left", "right"],
           "align": "left", "margin_pct": 0.06, "negative_space": 0.50, "line_spacing": 1.5,
           "headline_opacity": 1.0, "focal": "side", "recipe": "subject on one side (image-led → right), "
           "the other side a clean vertical negative-space column for the copy; a clear dividing axis"},
    "54": {"zh": "黄金比例排版", "en": "Golden Ratio", "mnemonic": "主辅分,焦点明;间有度,节奏轻",
           "use": "high-end brand / premium", "copy_zones": ["bottom", "left", "right"],
           "align": "left", "margin_pct": 0.06, "negative_space": 0.55, "line_spacing": 1.5,
           "headline_opacity": 1.0, "focal": "golden", "golden": True,
           "recipe": "compose on a golden grid (38.2% / 61.8%); subject and headline sit on the golden "
                     "lines, main element large and auxiliary small, natural 1:1.618 proportion"},
}

# which formula to default to for a given compose --zone when the user doesn't name one
ZONE_DEFAULT = {"top": "43", "bottom": "43", "left": "44", "right": "44"}
# named intents → formula (for render/compose --formula by feel)
INTENT_DEFAULT = {"minimal": "11", "centered": "08", "premium": "54", "asymmetric": "07",
                  "fullbleed": "01", "module": "05"}


def resolve(fid_or_intent, zone=None):
    """Pick a formula: explicit id → intent name → the zone default → 43. Returns (id, dict)."""
    key = (fid_or_intent or "").strip().lower()
    if key in FORMULAS:
        return key, FORMULAS[key]
    if key in INTENT_DEFAULT:
        fid = INTENT_DEFAULT[key]
        return fid, FORMULAS[fid]
    fid = ZONE_DEFAULT.get(zone, "43")
    return fid, FORMULAS[fid]


def example_image_path(fid, k=1):
    """Locate the book's 例图 NN_k.jpg from the typography-formulas skill, if installed; else None."""
    name = f"{int(fid):02d}_{k}.jpg"
    for base in (os.path.expanduser("~/.claude/skills/typography-formulas/references/images"),
                 os.path.expanduser("~/.agents/skills/typography-formulas/references/images")):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None


if __name__ == "__main__":
    for fid, F in FORMULAS.items():
        ex = example_image_path(fid)
        print(f"{fid} {F['zh']} / {F['en']:14} zones={','.join(F['copy_zones']):<20} "
              f"align={F['align']:<6} neg={F['negative_space']:.0%}  例图={'yes' if ex else 'no'}")
