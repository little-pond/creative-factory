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
flag the rest" mechanical — which is the whole premise.

Stdlib only.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formats as fmt  # noqa: E402

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sha256_bytes(b):
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _sha256_obj(obj):
    return _sha256_bytes(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def _jaccard(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


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
        path = os.path.join(c, "check.py")
        if os.path.exists(path):
            sys.path.insert(0, c)
            try:
                import check as brand_check  # type: ignore
                return brand_check.check, brand_check.verdict_of, path
            except Exception:
                continue
    return None, None, None


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
        "production": campaign.get("production", {}),  # carry cost/hours/days through to build's lift handoff
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

    brand_check, verdict_of, gate_path = load_brand_gate()
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

    # P3 — differentiation check: shippable variants that share format+pillar but differ by audience and
    # still have near-identical copy mean the audience axis isn't earning its combinatorial cost.
    dup_pairs = find_near_duplicates(shippable, args.dedup_threshold)

    # P4 — reproducibility: a compliance batch is only auditable if you can prove WHICH rules gated it.
    provenance = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "brand_profile": bp_raw,
        "brand_profile_hash": _sha256_obj(brand_profile) if brand_profile else None,
        "gate_ruleset_hash": _sha256_bytes(open(gate_path, "rb").read()) if (gate_available and gate_path) else None,
        "format_registry_hash": _sha256_obj(fmt.FORMATS),
        "_use": "reproducibility — same brand_profile_hash + gate_ruleset_hash ⇒ the same rules gated "
                "this batch. Record it with a compliance sign-off.",
    }

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
            "near_duplicate_pairs": len(dup_pairs),
            "gate": "brand-system check.py" if gate_available else "UNAVAILABLE (install brand-system / pass --brand)",
        },
        "provenance": provenance,
        "differentiation": {
            "_use": "audience axes earn their cost only if copy actually changes per segment; these pairs "
                    "share format+pillar, differ by audience, but read near-identical — collapse or rewrite.",
            "threshold": args.dedup_threshold,
            "near_duplicate_pairs": dup_pairs,
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
    if dup_pairs:
        print(f"  ⚠ {len(dup_pairs)} near-duplicate audience pair(s) — the audience axis isn't differentiating:")
        for dp in dup_pairs:
            print(f"    - {dp['a']} ≈ {dp['b']}  (sim {dp['similarity']}, {dp['pillar']}: "
                  f"{' / '.join(str(x) for x in dp['audiences'])})")
    print(f"  provenance: brand {provenance['brand_profile_hash']}  ·  gate {provenance['gate_ruleset_hash']}")
    print(f"  wrote {os.path.join(outdir, 'generation-manifest.json')} (+ compliance-report.md)")
    if args.render_prompts:
        write_render_prompts(manifest, outdir)


def write_render_prompts(manifest, outdir):
    """Emit shippable image/video variants' prompts as a ready-to-render list (the hybrid --render
    half: feed these to generate-image / Gen Studio / Celtra to produce the real hero assets). Carries
    the placement + its safe zone so render.py --layout-ref can draw a layout wireframe per item."""
    prompts = []
    for r in manifest["variants"]:
        if not (r["shippable"] and r["asset_type"] in ("image", "video")):
            continue
        spec = fmt.spec_for(r["platform"], r.get("placement", ""))
        prompts.append({"id": r["id"], "dims": r.get("dims"), "platform": r["platform"],
                        "placement": r.get("placement"), "safe": spec.get("safe"),
                        "image_prompt": r.get("image_prompt")})
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
    dup = (m.get("differentiation") or {}).get("near_duplicate_pairs") or []
    if dup:
        L += ["### Under-differentiated audience pairs (P3)\n",
              "_Same format + pillar, different audience, near-identical copy — the audience axis isn't "
              "earning its cost. Rewrite for the segment or collapse._\n",
              "| A | B | Pillar | Audiences | Similarity |", "|---|---|---|---|---|"]
        for dp in dup:
            L.append(f"| {dp['a']} | {dp['b']} | {dp['pillar']} | "
                     f"{' / '.join(str(x) for x in dp['audiences'])} | {dp['similarity']} |")
        L.append("")
    L += ["### Production efficiency (for the lift readout)\n",
          "| Metric | Value |", "|---|---|"]
    for k, val in m["production_efficiency"].items():
        if not k.startswith("_"):
            L.append(f"| {k} | {val} |")
    prov = m.get("provenance") or {}
    if prov:
        L += ["", "### Provenance (reproducibility)\n",
              f"- Built: `{prov.get('created_at')}`",
              f"- Brand profile: `{prov.get('brand_profile_hash')}`",
              f"- Gate ruleset: `{prov.get('gate_ruleset_hash')}`",
              "- _Same two hashes ⇒ the same rules gated this batch — record with the compliance sign-off._"]
    L += ["", "_Next: fill the perf fields in `lift_handoff` after the flight and run "
          "`lift-scorecard` for incremental new customers / iROAS vs the agency arm._"]
    return "\n".join(L)


def find_near_duplicates(results, threshold):
    """P3 — flag variant pairs that share (platform, placement, pillar) but differ in audience yet carry
    near-identical copy (token Jaccard >= threshold). Those pairs mean the audience axis isn't
    differentiating — the personalization the loop is trying to prove pays off didn't actually happen."""
    def copy_tokens(r):
        return _tokens(" ".join(str(val) for k, val in (r.get("copy") or {}).items() if k != "cta"))
    groups = {}
    for r in results:
        groups.setdefault((r.get("platform"), r.get("placement"), r.get("pillar")), []).append(r)
    pairs = []
    for rs in groups.values():
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                if a.get("audience") == b.get("audience"):
                    continue
                sim = _jaccard(copy_tokens(a), copy_tokens(b))
                if sim >= threshold:
                    pairs.append({"a": a["id"], "b": b["id"], "pillar": a.get("pillar"),
                                  "audiences": [a.get("audience"), b.get("audience")],
                                  "similarity": round(sim, 3)})
    return sorted(pairs, key=lambda p: -p["similarity"])


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in str(s).lower()).strip("_")


# --------------------------------- ingest: scaffold a campaign.json from a URL --------------------
def cmd_ingest(args):
    """P5 — lower the activation energy: fetch a brand URL and scaffold a campaign.json (brand name,
    domain, a starter voice hint) so the operator fills pillars/audiences instead of authoring the whole
    file from a blank page. Best-effort + stdlib only; on any fetch failure it still writes a scaffold."""
    url = args.url if "://" in args.url else "https://" + args.url
    title = desc = ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "creative-factory-ingest/1.0"})
        html = urllib.request.urlopen(req, timeout=args.timeout).read().decode("utf-8", "ignore")
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I | re.S)
        desc = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    except Exception as e:
        print(f"  note: could not fetch {url} ({e.__class__.__name__}) — writing a blank scaffold.")

    host = re.sub(r"^www\.", "", urlparse(url).netloc)
    brand = (title.split("—")[0].split("|")[0].split("-")[0].strip() or host.split(".")[0].title())

    campaign = {
        "_comment": f"Scaffolded by `factory.py ingest {url}`. Fill pillars/audiences/formats, point "
                    f"brand_profile at a brand-system profile, then run: factory.py plan <this file>.",
        "_source": {"url": url, "title": title, "description": desc},
        "campaign": f"{brand} — TODO campaign name",
        "brand": brand,
        "brand_profile": "TODO: ../brand-system/assets/<brand>.brand.json (voice + audiences + gate)",
        "formats": ["meta:feed", "linkedin:single_image", "google:rsa"],
        "audiences": ["TODO audience A", "TODO audience B"],
        "messaging": {
            "pillars": ["TODO pillar 1", "TODO pillar 2"],
            "geo_angles": [{"angle": "TODO answer-first claim from a geo-content-brief", "source": ""}],
            "approved_ctas": ["TODO CTA"],
        },
        "production": {"_note": "Fill from the real flight.", "cost_per_asset": None, "hours": None,
                       "time_to_launch_days": None},
    }
    out = args.out or "campaign.scaffold.json"
    if os.path.dirname(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(campaign, f, indent=2, ensure_ascii=False)
    print(f"INGEST: {url}\n  brand guess: {brand!r}" + (f"\n  title: {title!r}" if title else ""))
    print(f"  wrote {out} — fill the TODO fields (pillars / audiences / brand_profile), then: "
          f"factory.py plan {out}")


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
    b.add_argument("--dedup-threshold", type=float, default=0.85,
                   help="flag same-pillar cross-audience variants whose copy Jaccard >= this (P3)")
    b.set_defaults(func=cmd_build)

    g = sub.add_parser("ingest", help="scaffold a campaign.json from a brand URL (fill pillars/audiences after)")
    g.add_argument("url", help="brand URL (e.g. northwindtax.example.com)")
    g.add_argument("--out", help="output campaign path (default campaign.scaffold.json)")
    g.add_argument("--timeout", type=float, default=10.0, help="fetch timeout seconds")
    g.set_defaults(func=cmd_ingest)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
