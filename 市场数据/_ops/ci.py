# -*- coding: utf-8 -*-
"""本地 CI 闸门：编译 → 全量测试基线 → 哨兵 → 守卫。

用途：在没有托管 CI 的生产机上，给每次改动一个统一入口。
- 默认跑全量 pytest（约 8 分钟）；
- `--quick` 在 36h 内已有绿色基线时跳过 pytest，只跑编译/哨兵/守卫；
- 任一步硬失败返回 1；守卫的 issues 只记录，不单独判失败。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
PY = Path(r"D:\股票数据\.venv312\Scripts\python.exe")
OUT = ROOT / "_学习" / "_运维"


def latest_day() -> str:
    days = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and re.fullmatch(r"[0-9]{8}", p.name))
    if not days:
        raise SystemExit("找不到任何 YYYYMMDD 数据目录")
    return days[-1]


def run(name: str, cmd: list[str], timeout: int = 900) -> dict:
    started = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        rc = p.returncode
    except subprocess.TimeoutExpired as exc:
        out = f"TIMEOUT after {timeout}s\n{exc}"
        rc = 124
    return {"name": name, "rc": rc, "duration_s": round(time.time() - started, 1),
            "tail": out.strip().splitlines()[-25:]}


def baseline_state() -> dict:
    path = ROOT / "_学习" / "_测试基线.json"
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        at = dt.datetime.fromisoformat(d["at"])
        age = (dt.datetime.now() - at).total_seconds() / 3600
        return {"state": "pass" if d.get("failed") == 0 and age <= 36 else "stale_or_red",
                "at": d.get("at"), "failed": d.get("failed"), "age_hours": round(age, 1)}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"state": "missing", "error": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="基线绿色且未过期时跳过全量 pytest")
    ap.add_argument("--day", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    day = args.day or latest_day()
    OUT.mkdir(parents=True, exist_ok=True)
    steps = []

    py_files = sorted(ROOT.glob("*.py")) + sorted((ROOT / "_ops").glob("*.py"))
    steps.append(run("compile", [str(PY), "-m", "py_compile", *map(str, py_files)], timeout=180))
    steps.append(run("exceptions", [str(PY), str(ROOT / "_ops" / "exception_audit.py"), "--check"], timeout=180))

    b = baseline_state()
    if args.quick and b["state"] == "pass":
        steps.append({"name": "pytest", "rc": 0, "duration_s": 0.0,
                      "tail": [f"skipped: fresh green baseline {b['at']} (age {b['age_hours']}h)"]})
    else:
        steps.append(run("pytest", [str(PY), str(ROOT / "_ops" / "test_baseline.py"), "run"], timeout=1200))

    sent = run("sentinel", [str(PY), str(ROOT / "复盘一致性哨兵.py"), day], timeout=300)
    # 哨兵历史上即便有 FAIL 也可能返回 0，必须看正文，不能被退出码骗。
    text = "\n".join(sent["tail"])
    if re.search(r"^\s*FAIL\s", text, re.M) or "项FAIL" in text or "结论: 1项FAIL" in text:
        sent["rc"] = 1
    steps.append(sent)

    steps.append(run("guard", [str(PY), str(ROOT / "_ops" / "guard.py"), "check"], timeout=180))

    hard = [s for s in steps if s["name"] in {"compile", "exceptions", "pytest", "sentinel"} and s["rc"] != 0]
    payload = {
        "at": dt.datetime.now().isoformat(timespec="seconds"),
        "day": day,
        "mode": "quick" if args.quick else "full",
        "status": "pass" if not hard else "fail",
        "baseline": b,
        "steps": steps,
        "hard_fail": [s["name"] for s in hard],
    }
    out = Path(args.out) if args.out else OUT / f"ci_{day}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    for s in steps:
        print(f"[{s['name']}] rc={s['rc']} {s['duration_s']}s :: {' | '.join(s['tail'][-2:])[:300]}")
    print(json.dumps({"status": payload["status"], "day": day, "out": str(out),
                      "hard_fail": payload["hard_fail"]}, ensure_ascii=False))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
