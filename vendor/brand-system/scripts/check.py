#!/usr/bin/env python3
"""
check.py — compliance gate for AI-generated creative against a brand-profile.json.

Lints copy (headlines / body / CTAs) for banned claim patterns, banned phrases, missing required
disclaimers, review-required topics, and off-voice tone words, then returns a verdict:
BLOCK / REVIEW REQUIRED / PASS WITH WARNINGS / PASS.

This is the shared compliance gate the geo-content-brief and lift-scorecard skills reference.
Stdlib only. Exit code: 1 if BLOCK (so it can fail a CI/release step), else 0.

INPUT:
  brand profile JSON (positional) +
  --text "..."            one or more lines (repeatable), OR
  --assets batch.json     where batch.json is {"assets":[{"id","type","text"}], "fineprint":"..."}
                          or a plain list of strings.
  --fineprint "..."       disclaimer text that lives elsewhere (so it isn't falsely flagged missing)

USAGE:
  python3 check.py turbotax.brand.json --text "Get your guaranteed maximum refund - 100% free!"
  python3 check.py turbotax.brand.json --assets batch.json --out workspace/
"""

import argparse
import json
import os
import re
import sys

SEV_ORDER = {"blocker": 3, "review": 2, "warning": 1}


def load_assets(args):
    assets = []
    if args.assets:
        with open(args.assets) as f:
            data = json.load(f)
        fineprint = ""
        if isinstance(data, dict):
            fineprint = data.get("fineprint", "")
            items = data.get("assets", [])
        else:
            items = data
        for i, it in enumerate(items):
            if isinstance(it, str):
                assets.append({"id": f"asset_{i}", "type": "copy", "text": it})
            else:
                assets.append({"id": it.get("id", f"asset_{i}"),
                               "type": it.get("type", "copy"), "text": it.get("text", "")})
        return assets, fineprint
    for i, t in enumerate(args.text or []):
        assets.append({"id": f"text_{i}", "type": "copy", "text": t})
    return assets, (args.fineprint or "")


def check(profile, assets, fineprint):
    comp = profile.get("compliance", {})
    voice = profile.get("voice", {})
    findings = []
    # Lint the CREATIVE COPY for violations (triggers + topics). Fine print is approved disclaimer
    # text — it must NOT be linted, or an approved disclaimer that mentions "guarantee" would flag
    # itself. Fine print is used ONLY to satisfy required-disclaimer markers (marker_lc below).
    copy_lc = (" \n ".join(a["text"] for a in assets)).lower()
    marker_lc = (copy_lc + " " + fineprint).lower()

    for a in assets:
        text, lc = a["text"], a["text"].lower()
        for rule in comp.get("banned_patterns", []):
            m = re.search(rule["pattern"], text, re.IGNORECASE)
            if m:
                findings.append({"asset": a["id"], "rule": rule["id"], "severity": rule["severity"],
                                 "reason": rule["reason"], "match": m.group(0)})
        for ph in comp.get("banned_phrases", []):
            if ph["phrase"].lower() in lc:
                findings.append({"asset": a["id"], "rule": "phrase:" + ph["phrase"],
                                 "severity": ph["severity"], "reason": ph["reason"],
                                 "match": ph["phrase"]})
        for w in voice.get("banned_tone_words", []):
            if w.lower() in lc:
                findings.append({"asset": a["id"], "rule": "tone:" + w, "severity": "warning",
                                 "reason": "Off-voice / banned tone word.", "match": w})

    # required disclaimers — triggered by the COPY; satisfied by marker in copy OR fine print
    for d in comp.get("required_disclaimers", []):
        triggered = next((k for k in d.get("trigger_keywords", []) if k.lower() in copy_lc), None)
        if triggered and d.get("marker", "").lower() not in marker_lc:
            findings.append({"asset": "(asset set)", "rule": "missing_disclaimer:" + d["id"],
                             "severity": "blocker",
                             "reason": f"{d['reason']} Triggered by '{triggered}'. Add: \"{d['required_text']}\"",
                             "match": triggered})

    # review-required topics — present in the COPY (not the approved fine print). Match on word
    # boundaries, not raw substring, so a topic like "IRS" doesn't false-fire inside "first" (f-IRS-t)
    # and flag every first-time-filer ad for legal review.
    for topic in comp.get("review_required_topics", []):
        if re.search(r"\b" + re.escape(topic.lower()) + r"\b", copy_lc) \
                and not any(f["rule"] == "topic:" + topic for f in findings):
            findings.append({"asset": "(asset set)", "rule": "topic:" + topic, "severity": "review",
                             "reason": "Review-required topic present — route to legal.", "match": topic})

    return findings


def verdict_of(findings):
    sevs = {f["severity"] for f in findings}
    if "blocker" in sevs:
        return "BLOCK"
    if "review" in sevs:
        return "REVIEW REQUIRED"
    if "warning" in sevs:
        return "PASS WITH WARNINGS"
    return "PASS"


def render(profile, assets, findings, verdict):
    brand = profile.get("identity", {}).get("brand", "Brand")
    icon = {"BLOCK": "⛔", "REVIEW REQUIRED": "🔶", "PASS WITH WARNINGS": "🟡", "PASS": "✅"}[verdict]
    L = [f"# Compliance Check — {brand}\n", f"## {icon} Verdict: {verdict}\n",
         f"Checked {len(assets)} asset(s) · {len(findings)} finding(s).\n"]
    by_sev = {"blocker": [], "review": [], "warning": []}
    for f in findings:
        by_sev[f["severity"]].append(f)
    labels = {"blocker": "⛔ Blockers (must fix before ship)",
              "review": "🔶 Review required (route to legal)",
              "warning": "🟡 Warnings (voice)"}
    for sev in ("blocker", "review", "warning"):
        if by_sev[sev]:
            L.append(f"### {labels[sev]}\n")
            L.append("| Asset | Rule | Match | Why |")
            L.append("|-------|------|-------|-----|")
            for f in by_sev[sev]:
                L.append(f"| {f['asset']} | {f['rule']} | `{f['match']}` | {f['reason']} |")
            L.append("")
    if not findings:
        L.append("_No issues found. Clears the gate._")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("--text", action="append", help="a line of copy (repeatable)")
    ap.add_argument("--assets", help="batch JSON")
    ap.add_argument("--fineprint", help="disclaimer text present elsewhere")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    with open(args.profile) as f:
        profile = json.load(f)
    assets, fineprint = load_assets(args)
    if not assets:
        sys.exit("No copy to check. Pass --text or --assets.")

    findings = check(profile, assets, fineprint)
    findings.sort(key=lambda x: -SEV_ORDER[x["severity"]])
    verdict = verdict_of(findings)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "brand_compliance_report.json"), "w") as f:
        json.dump({"brand": profile.get("identity", {}).get("brand"), "verdict": verdict,
                   "findings": findings}, f, indent=2)
    with open(os.path.join(args.out, "brand_compliance_report.md"), "w") as f:
        f.write(render(profile, assets, findings, verdict))

    print(f"VERDICT: {verdict}  ({len(findings)} finding(s) across {len(assets)} asset(s))")
    for f in findings:
        print(f"  [{f['severity']:<7}] {f['asset']}: {f['rule']} — \"{f['match']}\"")
    sys.exit(1 if verdict == "BLOCK" else 0)


if __name__ == "__main__":
    main()
