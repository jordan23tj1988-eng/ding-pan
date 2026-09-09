# -*- coding: utf-8 -*-
"""Fail-closed P3 production gate.

The controlled bridge is TEST ONLY. This script never turns controlled evidence
into a production registration and never invents provenance or settlement.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime
from pathlib import Path

REQUIRED = ["independent_provenance", "exchange_calendar", "real_registration_transaction", "production_call_site"]

def evaluate(evidence: dict) -> dict:
    remaining = list(evidence.get("remaining", []))
    flags = {
        "controlled_acceptance": evidence.get("status") == "accepted_controlled_only",
        "integration_bridge_installed": bool(evidence.get("integration_bridge_installed")),
        "production_deployed": bool(evidence.get("production_deployed")),
        "production_preregistration_allowed": bool(evidence.get("production_preregistration_allowed")),
    }
    missing = [x for x in REQUIRED if x in remaining]
    if not flags["integration_bridge_installed"]: missing.append("integration_bridge_installed")
    ok = flags["controlled_acceptance"] and not missing and flags["production_deployed"] and flags["production_preregistration_allowed"]
    return {"status": "pass" if ok else "blocked", "flags": flags, "missing": sorted(set(missing)), "controlled_test_method_count": evidence.get("controlled_test_method_count"), "production_action_taken": False}

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence", type=Path, required=True); ap.add_argument("--out", type=Path, required=True); args=ap.parse_args(argv)
    ev=json.loads(args.evidence.read_text(encoding="utf-8")); result=evaluate(ev); result["generated_at"]=datetime.now().isoformat(timespec="seconds")
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps(result,ensure_ascii=False)); return 0 if result["status"]=="pass" else 1
if __name__=="__main__": raise SystemExit(main())
