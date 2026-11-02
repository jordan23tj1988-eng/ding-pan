# -*- coding: utf-8 -*-
"""从当日结构化交易计划生成盘中 playbook，不继承旧日期旧 playbook。

master 交易计划是 buys/sells/notes 的唯一主来源；五路交易计划仅作为可追溯
route_plans 附录。没有结构化 watch 时严格输出空 watch，禁止从旧文件猜测。
"""
from __future__ import annotations
import argparse
import json
import os
import tempfile
from pathlib import Path

ROUTES = ("auction", "lhb", "theme", "logic", "limitup")


def _load(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build(root: Path, d: str, out: Path) -> dict:
    if not (isinstance(d, str) and len(d) == 8 and d.isdigit()):
        raise ValueError("d 必须为严格 YYYYMMDD")
    master_path = root / "_学习" / f"交易计划_master_{d}.json"
    if not master_path.is_file():
        raise FileNotFoundError(master_path)
    master = _load(master_path)
    if str(master.get("日期")) != d or master.get("路") != "master":
        raise ValueError("master 交易计划日期/路字段错配")
    for key in ("buys", "sells", "notes"):
        if key not in master:
            raise ValueError(f"master 缺少 {key}")
    if not isinstance(master["buys"], list) or not isinstance(master["sells"], list):
        raise ValueError("master buys/sells 必须为列表")
    route_plans = []
    for route in ROUTES:
        path = root / "_学习" / f"交易计划_{route}_{d}.json"
        if not path.is_file():
            continue
        obj = _load(path)
        if str(obj.get("日期")) != d or obj.get("路") != route:
            raise ValueError(f"{path.name} 日期/路字段错配")
        route_plans.append({
            "route": route,
            "source": f"_学习/{path.name}",
            "buys_count": len(obj.get("buys", [])) if isinstance(obj.get("buys", []), list) else None,
            "sells_count": len(obj.get("sells", [])) if isinstance(obj.get("sells", []), list) else None,
            "notes": obj.get("notes"),
        })
    result = {
        "date": d,
        "route": "master",
        "version": "2",
        "buys": master["buys"],
        "sells": master["sells"],
        "watch": master.get("watch") if isinstance(master.get("watch"), list) else [],
        "cash_pct": master.get("cash_pct"),
        "notes": master["notes"],
        "route_plans": route_plans,
        "sources": [f"_学习/交易计划_master_{d}.json"] + [x["source"] for x in route_plans],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="playbook-", suffix=".json", dir=str(out.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, out)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("d")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--out", type=Path)
    a = p.parse_args(argv)
    out = a.out or (a.root / "盘中" / a.d / "playbook.json")
    result = build(a.root, a.d, out)
    print(json.dumps({"status": "pass", "out": str(out), "date": a.d,
                      "watch_count": len(result["watch"]),
                      "route_plan_count": len(result["route_plans"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
