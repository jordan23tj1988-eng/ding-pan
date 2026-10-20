# -*- coding: utf-8 -*-
"""可观测性快照：把分散的守卫/看板/账本/预测状态聚合成一个 JSON。

只做聚合与口径统一，不产生新判断；页面和日报都从这里取数，避免各页各算一套。
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
LEARN = ROOT / "_学习"
OPS = LEARN / "_运维"
CRON_DB = Path(r"C:\Users\66353\AppData\Local\hermes\profiles\a\cron\executions.db")
REQUIRED = ["总审", "推演", "复盘链健康", "能力消费审计"]


def _load(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _freshness(d: str) -> dict:
    files = {}
    for prefix in REQUIRED:
        path = LEARN / f"{prefix}_{d}.json"
        files[prefix] = {"exists": path.is_file(),
                         "mtime": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
                         if path.is_file() else None}
    day_dir = ROOT / d
    files["daily_dir"] = {"exists": day_dir.is_dir(),
                          "files": len(list(day_dir.glob("*"))) if day_dir.is_dir() else 0}
    cutoff = dt.datetime.strptime(d, "%Y%m%d").replace(hour=20, minute=0)
    hours = round((dt.datetime.now() - cutoff).total_seconds() / 3600, 1)
    return {"files": files, "hours_since_cutoff": hours}


def _releases(d: str) -> dict:
    base = ROOT / "releases"
    items = []
    for path in sorted(base.glob(f"{d}-*")):
        manifest = _load(path / "manifest.json", {}) or {}
        items.append({"id": path.name, "created_at": manifest.get("created_at") or manifest.get("built_at"),
                      "release_state": manifest.get("release_state"),
                      "release_policy": manifest.get("release_policy"),
                      "tests_baseline": (manifest.get("tests_baseline") or {}).get("state")
                      if isinstance(manifest.get("tests_baseline"), dict) else manifest.get("tests_baseline")})
    return {"count": len(items), "items": items[-3:]}


def _cron(d: str) -> dict:
    if not CRON_DB.is_file():
        return {"error": "executions.db 不存在"}
    try:
        jobs = _load(CRON_DB.parent / "jobs.json", {})
        if isinstance(jobs, dict):
            jobs = jobs.get("jobs", [])
        names = {j.get("id"): j.get("name") for j in (jobs or [])}
        con = sqlite3.connect(f"file:{CRON_DB}?mode=ro", uri=True, timeout=5)
        rows = con.execute(
            "select job_id,status,started_at,finished_at,error from executions "
            "order by started_at desc limit 40").fetchall()
        con.close()
    except sqlite3.Error as exc:
        return {"error": str(exc)}
    runs = []
    for job_id, status, started, finished, error in rows:
        dur = None
        try:
            dur = round((dt.datetime.fromisoformat(finished) - dt.datetime.fromisoformat(started)).total_seconds(), 1)
        except (TypeError, ValueError):
            pass
        runs.append({"job_id": job_id, "name": names.get(job_id, job_id), "status": status,
                     "started_at": started, "duration_s": dur, "error": (error or "")[:160]})
    return {"recent": runs}


def build(d: str | None = None) -> dict:
    target = d or "20261016"
    out = {
        "as_of": target,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "guard": _load(OPS / "guard_state.json", {}),
        "assignments": _load(LEARN / "_任务看板" / "最新.json", {}),
        "cognition": _load(LEARN / "_认知清算" / "最新.json", {}),
        "predictions": _load(LEARN / "_预测审计" / "最新.json", {}),
        "ledger_weekly": _load(LEARN / "_模拟盘" / f"周统计_{target}.json", {}),
        "freshness": _freshness(target),
        "releases": _releases(target),
        "cron": _cron(target),
    }
    OPS.mkdir(parents=True, exist_ok=True)
    (OPS / f"可观测性_{target}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (OPS / "可观测性_最新.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def summary(d: str | None = None) -> dict:
    r = build(d)
    guard_issues = r["guard"].get("issues") or []
    return {
        "as_of": r["as_of"],
        "guard_issues": len(guard_issues),
        "guard_kinds": sorted({x.get("kind") for x in guard_issues}),
        "assignments_critical": (r["assignments"].get("counts") or {}).get("critical"),
        "prediction_coverage": r["predictions"].get("coverage"),
        "prediction_judgeable": r["predictions"].get("judgeable"),
        "cognition_counts": r["cognition"].get("counts"),
        "releases": r["releases"].get("count"),
        "freshness_hours": r["freshness"].get("hours_since_cutoff"),
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(summary(sys.argv[1] if len(sys.argv) > 1 else None), ensure_ascii=False, indent=1))
