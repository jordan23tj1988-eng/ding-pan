# -*- coding: utf-8 -*-
"""全量测试基线：夜间跑 pytest，把结果写进发布可读的基线文件。

用法:
  python _ops/test_baseline.py run     # 跑全量测试并落 _学习/_测试基线.json
  python _ops/test_baseline.py check   # 只读检查基线是否新鲜/通过
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
PY = Path(r"D:\股票数据\.venv312\Scripts\python.exe")
OUT = ROOT / "_学习" / "_测试基线.json"
MAX_AGE_HOURS = 36


def run() -> dict:
    started = dt.datetime.now()
    p = subprocess.run([str(PY), "-m", "pytest", "tests", "-q"], cwd=str(ROOT),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-12:]
    summary = tail[-1] if tail else ""
    rec = {"at": started.isoformat(timespec="seconds"), "rc": p.returncode,
           "summary": summary, "tail": tail, "duration_s": round((dt.datetime.now() - started).total_seconds(), 1),
           "failed": 0 if p.returncode == 0 else None}
    # 解析 "3 failed, 397 passed" 这类摘要；解析不到时 failed 保持 None，禁止猜。
    import re
    m = re.search(r"(\d+) failed", summary)
    if m:
        rec["failed"] = int(m.group(1))
    m = re.search(r"(\d+) passed", summary)
    if m:
        rec["passed"] = int(m.group(1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec


def check(now: dt.datetime | None = None) -> dict:
    if not OUT.is_file():
        return {"state": "missing", "reason": "无测试基线"}
    try:
        rec = json.loads(OUT.read_text(encoding="utf-8"))
        at = dt.datetime.fromisoformat(rec["at"])
    except (OSError, ValueError, KeyError) as exc:
        return {"state": "invalid", "reason": str(exc)}
    age = ((now or dt.datetime.now()) - at).total_seconds() / 3600
    if age > MAX_AGE_HOURS:
        return {"state": "stale", "age_hours": round(age, 1), "baseline": rec}
    if rec.get("failed") != 0:
        return {"state": "red", "baseline": rec}
    return {"state": "pass", "age_hours": round(age, 1), "baseline": rec}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run").set_defaults(func=lambda a: (print(json.dumps(run(), ensure_ascii=False)), 0)[1])
    sub.add_parser("check").set_defaults(func=lambda a: (print(json.dumps(check(), ensure_ascii=False)), 0)[1])
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
