# -*- coding: utf-8 -*-
"""指派看板：汇总所有 总审_*.json 的指派清单，算逾期与升级级别。

只读总审，不改原文件；输出唯一看板 JSON 供页面/告警消费。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
LEARN = ROOT / "_学习"
OUT = LEARN / "_任务看板"
DONE = {"完成", "已完成", "done", "closed", "已验收"}


def _date(text):
    text = str(text or "").strip()
    if len(text) != 8 or not text.isdigit():
        return None
    return dt.date(int(text[:4]), int(text[4:6]), int(text[6:]))


def collect(target: str | None = None) -> dict:
    target = target or dt.date.today().strftime("%Y%m%d")
    ref = _date(target) or dt.date.today()
    items = {}
    sources = 0
    for path in sorted(LEARN.glob("总审_2026*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows = payload.get("指派清单") or []
        if not isinstance(rows, list):
            continue
        sources += 1
        issued = str(payload.get("日期") or payload.get("date") or path.stem.split("_")[-1])
        for row in rows:
            if not isinstance(row, dict):
                continue
            aid = str(row.get("指派ID") or "").strip()
            if not aid:
                continue
            status = str(row.get("状态") or "未完成").strip()
            due = str(row.get("截止") or "").strip()
            due_date = _date(due)
            done = status in DONE
            overdue = 0 if done or not due_date else max(0, (ref - due_date).days)
            level = "done" if done else ("critical" if overdue > 2 else ("warn" if overdue else "open"))
            item = {
                "id": aid, "owner": row.get("指派给") or "unknown",
                "task": row.get("深挖任务") or "", "due": due, "status": status,
                "acceptance": row.get("可机械验收") or "", "issued": issued,
                "overdue_days": overdue, "level": level,
            }
            old = items.get(aid)
            if old is None or issued >= old["issued"]:
                items[aid] = item
    rows = sorted(items.values(), key=lambda x: (x["level"] != "critical", x["level"] != "warn", -x["overdue_days"], x["id"]))
    counts = Counter(x["level"] for x in rows)
    by_owner = {}
    for x in rows:
        by_owner.setdefault(x["owner"], Counter())[x["level"]] += 1
    result = {
        "as_of": target, "sources": sources, "total": len(rows),
        "counts": dict(counts), "by_owner": {k: dict(v) for k, v in sorted(by_owner.items())},
        "overdue": [x for x in rows if x["level"] in ("warn", "critical")],
        "open": [x for x in rows if x["level"] == "open"],
        "definitions": {"done": "状态∈完成/已验收", "critical": "逾期>2天", "warn": "已逾期", "open": "未到期"},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"任务看板_{target}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "最新.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target")
    args = ap.parse_args(argv)
    r = collect(args.target)
    print(json.dumps({k: r[k] for k in ("as_of", "sources", "total", "counts", "by_owner")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
