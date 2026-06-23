#!/usr/bin/env python3
"""
factory.py — the AI creative factory: turn one campaign + one brand into a matrix of on-brand,
spec-valid, compliance-gated variants, and hand the production-efficiency numbers straight to the
incrementality experiment.

It does the deterministic half of "AI creative at scale". The judgment half — actually writing the
headline/body/CTA and the image prompt in brand voice — is the LLM's job (see SKILL.md). This script
owns everything a machine should own, so the human/LLM never does it by hand and never does it twice:

  plan   campaign.json  ->  variant-plan.json
         Expand format x pillar x audience into one row per variant, each pre-loaded with the exact
         format spec (dims, safe zone, char limits, required fields) so the copy gets written to spec
         the first time instead of being trimmed after.

  build  variants.json  ->  generation-manifest.json (+ compliance report + lift handoff)
         For each filled variant: validate char limits, run it through the BRAND COMPLIANCE GATE
         (the same brand-system check.py the rest of the portfolio uses — imported, not re-implemented,
         so the rule of record can't drift), compute brand_qa_pass_rate, and emit a manifest whose
         AI-arm production fields drop straight into experiment-designer / lift-scorecard.

Why this shape: in a regulated industry the bottleneck on AI creative isn't generation, it's trust and
spec-compliance at volume. A factory that emits 240 variants is worthless if you still have to eyeball
each one for a banned claim or a truncated headline. This makes "ship the safe ones automatically,
flag the rest" mechanical — which is the whole premise of the role.

Stdlib only.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formats as fmt  # noqa: E402

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_file(path, *bases):
    """Resolve a (possibly relative) path robustly: try it as-is (relative to CWD), then relative to
    each base dir given (e.g. the input file's dir, the skill root). Returns the first that exists, so
    a brand_profile written relative to one folder still resolves no matter where the script is run."""
    if not path:
        return None
    for c in [path] + [os.path.join(b, path) for b in bases if b]:
        if os.path.exists(c):
            return c
    return None


def resolve_brand_profile(bp_raw, input_file):
    """Find the brand-profile JSON across layouts: installed (brand-system is a sibling skill) or a
    standalone repo (brand-system vendored under vendor/). Tries the written path relative to the input
    file + skill root, then falls back to the vendored copy by basename — so the same asset path string
    works in both layouts without divergence."""
    if not bp_raw:
        return None
    bp = find_file(bp_raw, os.path.dirname(os.path.abspath(input_file)), SKILL_ROOT)
    if not bp:  # standalone repo: vendored copy located by filename
        bp = find_file(os.path.basename(bp_raw), os.path.join(SKILL_ROOT, "vendor", "brand-system", "assets"))
    return bp


# ----- locate the shared brand compliance gate (no drift: import brand-system's own check.py) -----
def load_brand_gate():
    """Import brand-system/scripts/check.py so the factory gates on the exact same rules of record.

    Returns (check_fn, verdict_fn) or (None, None) if brand-system isn't installed alongside. Tries
    the standard sibling-skill layout first, then a couple of fallbacks.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(here, "..", "..", "brand-system", "scripts")),  # sibling skill
        os.path.expanduser("~/.claude/skills/brand-system/scripts"),                   # installed skill
        os.path.join(SKILL_ROOT, "vendor", "brand-system", "scripts"),                # bundled in a standalone repo
    ]
    for c in candidates:
        if os.path.exists(os.path.join(c, "check.py")):
            sys.path.insert(0, c)
            try:
                import check as brand_check  # type: ignore
                return brand_check.check, brand_check.verdict_of
            except Exception:
                continue
    return None, None


# --------------------------------- plan: expand the matrix ----------------------------------------
def cmd_plan(args):
    with open(args.campaign) as f:
        campaign = json.load(f)

    brand = {}
    bp_raw = campaign.get("brand_profile")
    bp = resolve_brand_profile(bp_raw, args.campaign)
    if bp:
        with open(bp) as f:
            brand = json.load(f)
    elif bp_raw:
        print(f"  note: brand_profile '{bp_raw}' not found — using campaign-provided axes only "
              f"(no voice/compliance). Fix the path to wire in the brand gate.")

    # axes: campaign overrides, else fall back to the brand profile
    pillars = campaign.get("messaging", {}).get("pillars") \
        or brand.get("messaging", {}).get("pillars", [])
    geo_angles = campaign.get("messaging", {}).get("geo_angles", [])  # optional GEO feeder
    pillars = list(pillars) + [g if isinstance(g, str) else g.get("angle", "") for g in geo_angles]
    pillars = [p for p in pillars if p]

    audiences = campaign.get("audiences")
    if not audiences:
        audiences = [a.get("segment") for a in brand.get("audience", [])]
    audiences = [a for a in audiences if a]

    fmt_list = campaign.get("formats") or campaign.get("platforms") or []
    resolved, skipped = fmt.resolve_formats(fmt_list)

    if not (pillars and audiences and resolved):
        sys.exit("plan needs at least one pillar, one audience, and one resolvable format. "
                 f"Got pillars={pillars}, audiences={audiences}, formats={[r['key'] for r in resolved]}.")

    ctas = campaign.get("messaging", {}).get("approved_ctas") \
        or brand.get("messaging", {}).get("approved_ctas", [])

    rows = []
    for r in resolved:
        for pillar in pillars:
            for aud in audiences:
                spec = r["spec"]
                vid = f"{r['platform']}_{r['placement']}__{slug(pillar)}__{slug(aud)}"
                rows.append({
                    "id": vid,
                    "platform": r["platform"], "placement": r["placement"], "format_key": r["key"],
                    "asset_type": spec["asset"],
                    "dims": spec.get("dims"), "aspect": spec.get("aspect"),
                    "safe_zone_px": spec.get("safe"),
                    "pillar": pillar, "audience": aud,
                    "fields_needed": spec["fields"],
                    "char_limits": spec.get("limits", {}),
                    "spec_note": spec.get("note", ""),
                    # copy slots for the LLM to fill (one per needed field) + an image prompt
                    "copy": {field: ("" if field != "cta" else (ctas[0] if ctas else ""))
                             for field in spec["fields"]},
                    "image_prompt": "" if spec["asset"] in ("image", "video") else None,
                })

    plan = {
        "campaign": campaign.get("campaign", "untitled"),
        "brand": brand.get("identity", {}).get("brand") or campaign.get("brand"),
        "brand_profile": bp_raw,  # keep the author's relative path (portable); build re-resolves it
        "matrix": {"formats": len(resolved), "pillars": len(pillars),
                   "audiences": len(audiences), "cells": len(rows)},
        "axes": {"formats": [r["key"] for r in resolved], "pillars": pillars, "audiences": audiences},
        "skipped_formats": skipped,
        "voice": brand.get("voice", {}),
        "approved_ctas": ctas,
        "variants": rows,
    }
    out = args.out or "variant-plan.json"
    if os.path.dirname(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"PLAN: {len(rows)} variants = {len(resolved)} formats x {len(pillars)} pillars x {len(audiences)} audiences")
    if skipped:
        print(f"  skipped unknown formats: {', '.join(skipped)}")
    print(f"  wrote {out}  (fill the empty copy + image_prompt slots, then run: factory.py build {out})")


# --------------------------------- build: validate + gate + manifest -------------------------------
def cmd_build(args):
    with open(args.variants) as f:
        plan = json.load(f)
    variants = plan["variants"] if isinstance(plan, dict) and "variants" in plan else plan

    brand_profile = None
    bp_raw = args.brand or (plan.get("brand_profile") if isinstance(plan, dict) else None)
    bp_path = resolve_brand_profile(bp_raw, args.variants)
    if bp_path:
        with open(bp_path) as f:
            brand_profile = json.load(f)
    elif bp_raw:
        print(f"  note: brand_profile '{bp_raw}' not found — compliance left UNCHECKED. "
              f"Pass --brand <path> or fix the plan's brand_profile to run the gate.")

    brand_check, verdict_of = load_brand_gate()
    gate_available = brand_check is not None and brand_profile is not None
    fineprint = (args.fineprint or "")

    results = []
    for v in variants:
        spec = fmt.FORMATS.get(v["platform"], {}).get(v["placement"], {})
        copy = v.get("copy", {})

        # 1) spec / char-limit validation
        if spec:
            ok_len, len_issues = fmt.check_lengths(copy, spec)
        else:
            ok_len, len_issues = False, ["unknown format"]

        # 2) brand compliance gate (the shared rule of record)
        if gate_available:
            assets = [{"id": f"{v['id']}:{k}", "type": "copy", "text": str(val)}
                      for k, val in copy.items() if k != "cta" and val]
            findings = brand_check(brand_profile, assets, fineprint)
            verdict = verdict_of(findings)
        else:
            findings, verdict = [], "UNCHECKED"

        shippable = ok_len and verdict in ("PASS", "PASS WITH WARNINGS")
        results.append({
            **{k: v[k] for k in ("id", "platform", "placement", "pillar", "audience", "asset_type", "dims") if k in v},
            "copy": copy,
            "image_prompt": v.get("image_prompt"),  # carry the render prompt through so render-queue works
            "char_check": "PASS" if ok_len else "FAIL",
            "char_issues": len_issues,
            "compliance": verdict,
            "compliance_findings": findings,
            "shippable": shippable,
        })

    total = len(results)
    shippable = [r for r in results if r["shippable"]]
    blocked = [r for r in results if r["compliance"] == "BLOCK"]
    review = [r for r in results if r["compliance"] == "REVIEW REQUIRED"]
    char_fail = [r for r in results if r["char_check"] == "FAIL"]
    qa_pass_rate = round(len(shippable) / total, 4) if total else 0.0

    # production-efficiency assumptions (measure these on a real flight — defaults are clearly labeled)
    prod = plan.get("production", {}) if isinstance(plan, dict) else {}
    production_efficiency = {
        "assets": len(shippable),                       # real: variants that cleared both gates
        "variants_generated": total,                    # real
        "brand_qa_pass_rate": qa_pass_rate,             # real: cleared gate / generated
        "cost_per_asset": prod.get("cost_per_asset"),   # fill with measured token/compute $
        "hours": prod.get("hours"),                     # fill with measured wall-clock effort
        "time_to_launch_days": prod.get("time_to_launch_days"),
        "_note": "assets + brand_qa_pass_rate are measured by this run; cost_per_asset / hours / "
                 "time_to_launch_days must be filled with real measured values before claiming lift.",
    }

    manifest = {
        "campaign": plan.get("campaign") if isinstance(plan, dict) else None,
        "brand": (brand_profile or {}).get("identity", {}).get("brand"),
        "matrix": plan.get("matrix") if isinstance(plan, dict) else None,
        "summary": {
            "variants_generated": total,
            "shippable": len(shippable),
            "blocked": len(blocked),
            "review_required": len(review),
            "char_fail": len(char_fail),
            "brand_qa_pass_rate": qa_pass_rate,
            "gate": "brand-system check.py" if gate_available else "UNAVAILABLE (install brand-system / pass --brand)",
        },
        "production_efficiency": production_efficiency,
        # the handoff: drop straight into lift-scorecard's results.json arms.ai (perf fields post-flight)
        "lift_handoff": {
            "_use": "Paste into a lift-scorecard results.json as arms.ai; fill impressions/clicks/"
                    "conversions/spend/exposed_users/hook_rate after the flight, then run lift.py.",
            "arms.ai": {
                "impressions": None, "clicks": None, "spend": None,
                "conversions": None, "exposed_users": None,
                "assets": len(shippable),
                "cost_per_asset": production_efficiency["cost_per_asset"],
                "time_to_launch_days": production_efficiency["time_to_launch_days"],
                "hours": production_efficiency["hours"],
                "brand_qa_pass_rate": qa_pass_rate,
                "hook_rate": None,
            },
        },
        "variants": results,
    }

    outdir = args.out or "."
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "generation-manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, "compliance-report.md"), "w") as f:
        f.write(render_report(manifest))

    print(f"BUILD: {total} generated  |  {len(shippable)} shippable  |  "
          f"{len(blocked)} BLOCK  |  {len(review)} REVIEW  |  {len(char_fail)} char-fail")
    print(f"  brand_qa_pass_rate = {qa_pass_rate:.0%}")
    for r in blocked + char_fail:
        why = (r["char_issues"] if r["char_check"] == "FAIL" else
               [f"{f['rule']}:{f['match']}" for f in r["compliance_findings"] if f["severity"] == "blocker"])
        print(f"  - {r['id']}: {r['compliance']}/{r['char_check']}  {why}")
    print(f"  wrote {os.path.join(outdir, 'generation-manifest.json')} (+ compliance-report.md)")
    if args.render_prompts:
        write_render_prompts(manifest, outdir)


def write_render_prompts(manifest, outdir):
    """Emit shippable image/video variants' prompts as a ready-to-render list (the hybrid --render
    half: feed these to generate-image / Gen Studio / Celtra to produce the real hero assets)."""
    prompts = [{"id": r["id"], "dims": r.get("dims"), "platform": r["platform"],
                "image_prompt": next((v.get("image_prompt") for v in manifest["variants"]
                                      if v["id"] == r["id"]), None)}
               for r in manifest["variants"] if r["shippable"] and r["asset_type"] in ("image", "video")]
    path = os.path.join(outdir, "render-queue.json")
    with open(path, "w") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    print(f"  wrote {path} ({len(prompts)} hero prompts ready for image gen)")


def render_report(m):
    s = m["summary"]
    icon = "⛔" if s["blocked"] else ("🔶" if s["review_required"] else "✅")
    L = [f"# Creative Factory — {m.get('campaign') or ''} ({m.get('brand') or ''})\n",
         f"## {icon} {s['shippable']}/{s['variants_generated']} shippable · "
         f"brand QA pass rate {s['brand_qa_pass_rate']:.0%}\n",
         f"- Blocked: {s['blocked']}  ·  Review required: {s['review_required']}  ·  "
         f"Char-limit fails: {s['char_fail']}",
         f"- Compliance gate: {s['gate']}\n"]
    bad = [r for r in m["variants"] if not r["shippable"]]
    if bad:
        L += ["### Held back (fix upstream, then regenerate)\n",
              "| Variant | Char | Compliance | Issue |", "|---|---|---|---|"]
        for r in bad:
            issue = ", ".join(r["char_issues"]) if r["char_check"] == "FAIL" else \
                "; ".join(f"{f['rule']} (`{f['match']}`)" for f in r["compliance_findings"])
            L.append(f"| {r['id']} | {r['char_check']} | {r['compliance']} | {issue} |")
        L.append("")
    L += ["### Production efficiency (for the lift readout)\n",
          "| Metric | Value |", "|---|---|"]
    for k, val in m["production_efficiency"].items():
        if not k.startswith("_"):
            L.append(f"| {k} | {val} |")
    L += ["", "_Next: fill the perf fields in `lift_handoff` after the flight and run "
          "`lift-scorecard` for incremental GNS / iROAS vs the agency arm._"]
    return "\n".join(L)


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in str(s).lower()).strip("_")


def main():
    ap = argparse.ArgumentParser(description="AI creative factory: campaign -> on-brand variant matrix.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="expand format x pillar x audience into a variant work order")
    p.add_argument("campaign")
    p.add_argument("--out", help="output plan path (default variant-plan.json)")
    p.set_defaults(func=cmd_plan)

    b = sub.add_parser("build", help="validate + compliance-gate filled variants -> manifest")
    b.add_argument("variants")
    b.add_argument("--brand", help="brand-profile.json (else read from the plan's brand_profile)")
    b.add_argument("--fineprint", help="approved disclaimer text living in fine print")
    b.add_argument("--out", help="output dir (default .)")
    b.add_argument("--render-prompts", action="store_true",
                   help="also emit render-queue.json for image gen (hybrid render step)")
    b.set_defaults(func=cmd_build)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
