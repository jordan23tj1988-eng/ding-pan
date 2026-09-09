# -*- coding: utf-8 -*-
"""P1/P2 data-capability gate: missing capability must fail closed.

This gate distinguishes a real alternative from a complete capability. It is
intentionally strict: degraded alternatives are reported but cannot authorize
production completion.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

CAPABILITIES = {
    "risk_calendar": {"label": "风险日历", "files": ["风险日历.py", "_学习/风险日历_{d}.json"], "hard": True},
    "auction_cancel_diff": {"label": "竞价撤单差分", "files": ["竞价撤单差分.py", "_学习/竞价撤单差分_{d}.json"], "hard": True},
    "open_verification": {"label": "开盘验证维", "files": ["开盘验证维.py", "_学习/开盘验证维_{d}.json"], "hard": True},
    "intraday_temperature_curve": {"label": "日内温度曲线", "files": ["日内温度曲线.py", "_学习/日内温度曲线_{d}.json"], "hard": True},
    "intraday_rotation_graph": {"label": "日内轮动图谱", "files": ["日内轮动图谱.py", "_学习/日内轮动图谱_{d}.json"], "hard": True},
    "theme_relocation": {"label": "题材归位", "files": ["题材归位.py", "_学习/题材归位_{d}.json"], "hard": True},
    "cognition_pack": {"label": "认知库打包/蒸馏", "files": ["认知库打包.py", "_认知库蒸馏_五路.py", "review_learning.py"], "hard": False},
    "playbook": {"label": "playbook生成", "files": ["playbook生成.py", "盘中/{d}/playbook.json"], "hard": False},
}


def check(root: Path, d: str) -> dict:
    rows = []
    for key, spec in CAPABILITIES.items():
        found = []
        for rel in spec["files"]:
            rel = rel.format(d=d)
            p = root / rel
            if p.is_file():
                found.append(rel)
        complete = bool(found)
        rows.append({"key": key, "label": spec["label"], "hard": spec["hard"], "status": "available" if complete else "missing", "evidence": found})
    hard_missing = [r["key"] for r in rows if r["hard"] and r["status"] != "available"]
    return {"date": d, "generated_at": datetime.now().isoformat(timespec="seconds"), "status": "pass" if not hard_missing else "fail", "hard_missing": hard_missing, "capabilities": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("date", help="YYYYMMDD")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    if not re.fullmatch(r"\d{8}", args.date):
        ap.error("date must be YYYYMMDD")
    result = check(args.root, args.date)
    out = args.out or (args.root / "_学习" / f"p1_p2_capability_gate_{args.date}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
