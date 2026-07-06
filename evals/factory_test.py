#!/usr/bin/env python3
"""
factory_test.py — self-test for creative-factory. Asserts the matrix expands, the GEO angle folds in
as a pillar, the brand gate catches a banned claim, the spec check catches a truncated headline, the
lift handoff carries the measured production numbers, and the hardening gates work: safe-zone geometry
(P0), image anti-slop injection (P1), audience-differentiation dedup (P3), reproducibility hashes (P4),
and URL ingest scaffolding (P5). Stdlib only. Run from anywhere:

    python3 evals/factory_test.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FACTORY = os.path.join(ROOT, "scripts", "factory.py")
CAMPAIGN = os.path.join(ROOT, "assets", "northwind.campaign.json")
VARIANTS = os.path.join(ROOT, "assets", "variants.example.json")
BRAND = os.path.join(ROOT, "vendor", "brand-system", "assets", "northwind.brand.json")
FINEPRINT = "~37% of taxpayers qualify for Northwind Free Edition (simple Form 1040 returns only)."

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import formats as fmt  # noqa: E402
import render  # noqa: E402
import formulas as flib  # noqa: E402


def run(*args):
    r = subprocess.run([sys.executable, FACTORY, *args], capture_output=True, text=True)
    assert r.returncode == 0, f"factory.py {args} failed:\n{r.stdout}\n{r.stderr}"
    return r.stdout


def main():
    tmp = tempfile.mkdtemp(prefix="cf_test_")
    plan_path = os.path.join(tmp, "plan.json")

    # 1) plan expands format x pillar x audience, and the GEO angle becomes a third pillar
    run("plan", CAMPAIGN, "--out", plan_path)
    plan = json.load(open(plan_path))
    assert plan["matrix"]["cells"] == 18, plan["matrix"]
    assert plan["matrix"] == {"formats": 3, "pillars": 3, "audiences": 2, "cells": 18}, plan["matrix"]
    assert "free for simple returns" in plan["axes"]["pillars"], "GEO angle should fold in as a pillar"
    assert all("char_limits" in v and "fields_needed" in v for v in plan["variants"])

    # 2) build validates + gates the filled matrix
    run("build", VARIANTS, "--fineprint", FINEPRINT, "--out", tmp)
    m = json.load(open(os.path.join(tmp, "generation-manifest.json")))
    s = m["summary"]
    assert s["variants_generated"] == 18, s
    assert s["shippable"] == 16, s
    assert s["blocked"] == 1, s
    assert s["char_fail"] == 1, s
    assert s["review_required"] == 0, f"no false-positive reviews expected (IRS-in-'first' bug): {s}"
    assert s["brand_qa_pass_rate"] == round(16 / 18, 4), s

    # 3) the gate catches the *right* two — a banned claim and a truncated headline
    by_id = {v["id"]: v for v in m["variants"]}
    blocked = by_id["meta_feed__confidence__self_employed"]
    assert blocked["compliance"] == "BLOCK", blocked
    assert any("outcome_promise" == f["rule"] for f in blocked["compliance_findings"])
    char = by_id["google_rsa__ease__self_employed"]
    assert char["char_check"] == "FAIL" and char["compliance"] == "PASS", char

    # 4) the lift handoff carries the measured production numbers for lift-scorecard's AI arm
    ai = m["lift_handoff"]["arms.ai"]
    assert ai["assets"] == 16, ai
    assert ai["brand_qa_pass_rate"] == round(16 / 18, 4), ai
    assert ai["impressions"] is None and ai["conversions"] is None, "perf fields are post-flight (null)"

    # 5) P4 — reproducibility provenance: the manifest records which rules gated the batch
    prov = m["provenance"]
    assert prov["brand_profile_hash"].startswith("sha256:"), prov
    assert prov["gate_ruleset_hash"].startswith("sha256:"), prov
    assert prov["format_registry_hash"].startswith("sha256:"), prov
    assert prov["created_at"], prov
    # the well-differentiated example run has no near-duplicate audience pairs
    assert s["near_duplicate_pairs"] == 0, m["differentiation"]

    # 6) P3 — the dedup check fires when two audiences get identical copy for the same pillar+format
    dup = {"campaign": "dup-test", "brand_profile": BRAND, "variants": [
        {"id": "meta_feed__ease__aud_a", "platform": "meta", "placement": "feed", "pillar": "ease",
         "audience": "aud_a", "asset_type": "image",
         "copy": {"primary_text": "File your taxes fast and simple online today.",
                  "headline": "File in minutes", "description": "Simple and quick", "cta": "Start"}},
        {"id": "meta_feed__ease__aud_b", "platform": "meta", "placement": "feed", "pillar": "ease",
         "audience": "aud_b", "asset_type": "image",
         "copy": {"primary_text": "File your taxes fast and simple online today.",
                  "headline": "File in minutes", "description": "Simple and quick", "cta": "Start"}},
    ]}
    dup_path = os.path.join(tmp, "dup.json")
    json.dump(dup, open(dup_path, "w"))
    run("build", dup_path, "--brand", BRAND, "--out", tmp)
    md = json.load(open(os.path.join(tmp, "generation-manifest.json")))
    assert md["summary"]["near_duplicate_pairs"] == 1, md["differentiation"]
    pair = md["differentiation"]["near_duplicate_pairs"][0]
    assert pair["similarity"] == 1.0 and set(pair["audiences"]) == {"aud_a", "aud_b"}, pair

    # 7) P0 — safe-zone geometry: an intruding box is caught, a clean one passes
    stories = fmt.spec_for("meta", "stories")  # top=250, bottom=340 on 1080x1920
    viol = fmt.safe_zone_violations(stories, [("headline", 60, 120, 1000, 300)], 1080, 1920)
    assert viol and viol[0][:2] == ("headline", "top") and viol[0][2] == 130, viol
    assert fmt.safe_zone_violations(stories, [("body", 60, 400, 1000, 700)], 1080, 1920) == []
    assert fmt.safe_zone_violations(fmt.spec_for("google", "rsa"), [("x", 0, 0, 9, 9)], 9, 9) == []  # no safe zone

    # 8) P1 — anti-slop injection: universal tail + brand palette/don'ts are present
    extra = render.brand_constraints(BRAND)
    assert "#1E5EB8" in extra and "don't" in extra.lower(), extra
    assert "yellow-tint" in render.ANTI_SLOP and "Inter" in render.ANTI_SLOP

    # 9) P5 — ingest scaffolds a campaign.json even when the URL can't be fetched
    scaffold = os.path.join(tmp, "scaffold.json")
    run("ingest", "northwindtax.invalid-tld-xyz", "--out", scaffold, "--timeout", "2")
    cj = json.load(open(scaffold))
    assert cj["formats"] and "brand_profile" in cj and cj["messaging"]["pillars"], cj

    # 10) layout formulas (《排版的力量·54个排版公式》): resolution by id/intent/zone + recipe wiring
    assert flib.resolve("54")[0] == "54", "explicit id"
    assert flib.resolve("premium")[0] == "54", "intent → formula"
    assert flib.resolve(None, "left")[0] == "44", "zone default"
    assert flib.resolve("nonsense", "top")[0] == "43", "fallback to zone default"
    F = flib.FORMULAS["43"]
    assert 0.0 < F["negative_space"] < 1.0 and F["align"] in ("left", "center", "right"), F
    rec = render.formula_recipe(flib.resolve("54"))
    assert "黄金比例" in rec and "Golden Ratio" in rec, rec  # book name flows into the render prompt

    print("PASS — creative-factory: 18-cell matrix (GEO folded in) | 16/18 shippable | "
          "banned-claim BLOCK + truncation FAIL caught | lift handoff assets=16, brand_qa=89% | "
          "P0 safe-zone + P1 anti-slop + P3 dedup + P4 provenance + P5 ingest + layout-formulas all green")


if __name__ == "__main__":
    main()
