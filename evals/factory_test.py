#!/usr/bin/env python3
"""
factory_test.py — self-test for creative-factory. Asserts the matrix expands, the GEO angle folds in
as a pillar, the brand gate catches a banned claim, the spec check catches a truncated headline, and
the lift handoff carries the measured production numbers. Stdlib only. Run from anywhere:

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
CAMPAIGN = os.path.join(ROOT, "assets", "turbotax.campaign.json")
VARIANTS = os.path.join(ROOT, "assets", "variants.example.json")
FINEPRINT = "~37% of taxpayers qualify for TurboTax Free Edition (simple Form 1040 returns only)."


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
    # every cell carries the spec it must be written to
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

    print("PASS — creative-factory: 18-cell matrix (GEO angle folded in) | "
          "16/18 shippable | banned-claim BLOCK + truncation FAIL caught | "
          "lift handoff carries assets=16, brand_qa=89%")


if __name__ == "__main__":
    main()
