# -*- coding: utf-8 -*-
"""认知清算：把“经验/规则/可验证规格”分层，过期未验证的如实归档。

不伪造验证结果：
- 只有 validation 里带 metric/op/threshold/due_d 且 review_log 有 true/false 的记录才算 verified；
- 有 falsifiable_rule 但没有结构化规格 → needs_spec（30 天内）或 expired（超期）；
- 没有可证伪规则 → open（14 天内）或 archived（超期经验）。
`--apply` 只新增 清算状态/清算依据/清算_at 三个字段，不改原 state，不删任何记录。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
LEARN = ROOT / "_学习"
SRC = LEARN / "能力进化库_认知迭代.json"
OUT = LEARN / "_认知清算"


def _age_days(date_text: str, target: str) -> int | None:
    try:
        day = dt.date(int(date_text[:4]), int(date_text[5:7]), int(date_text[8:10]))
        ref = dt.date(int(target[:4]), int(target[4:6]), int(target[6:]))
        return (ref - day).days
    except (ValueError, TypeError):
        return None


def _has_spec(record: dict) -> bool:
    val = record.get("validation")
    if not isinstance(val, dict):
        return False
    return all(val.get(k) is not None for k in ("metric", "op", "threshold", "due_d"))


def _verified(record: dict) -> bool:
    logs = record.get("review_log") or []
    return any(isinstance(x, dict) and x.get("status") in ("true", "false", "verified", "hit", "miss")
               for x in logs)


def classify(record: dict, target: str) -> tuple[str, str]:
    age = _age_days(str(record.get("date") or ""), target)
    rule = str(record.get("falsifiable_rule") or "").strip()
    if _verified(record):
        return "verified", "review_log 已有 true/false 判定"
    if _has_spec(record):
        return "needs_review", "已有结构化 validation_spec，等待到期判定"
    if rule:
        if age is None:
            return "needs_spec", "有可证伪规则但日期不可解析，需补规格"
        if age > 30:
            return "expired", f"有可证伪规则但 {age} 天未补规格/未验证"
        return "needs_spec", f"有可证伪规则，{age} 天内需补 metric/op/threshold/due_d"
    if age is None:
        return "open", "无可证伪规则且日期不可解析"
    if age > 14:
        return "archived", f"无可证伪规则的纯经验，已 {age} 天"
    return "open", f"新经验（{age} 天），暂保留待提炼"


def clear(target: str, apply: bool = False) -> dict:
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    records = payload.get("records") or []
    counts = Counter()
    by_route = {}
    expired_ids = []
    for record in records:
        status, reason = classify(record, target)
        counts[status] += 1
        by_route.setdefault(record.get("route") or "unknown", Counter())[status] += 1
        if status in ("expired", "needs_spec"):
            expired_ids.append(record.get("id"))
        if apply:
            record["清算状态"] = status
            record["清算依据"] = reason
            record["清算_at"] = target
    if apply:
        OUT.mkdir(parents=True, exist_ok=True)
        backup = OUT / f"backup_认知迭代_{target}.json"
        if not backup.exists():
            shutil.copy2(SRC, backup)
        payload["records"] = records
        payload["认知清算"] = {"at": target, "counts": dict(counts)}
        tmp = SRC.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(SRC)
    result = {
        "at": target, "applied": apply, "total": len(records),
        "counts": dict(counts),
        "routes": {k: dict(v) for k, v in sorted(by_route.items())},
        "needs_spec_or_expired": len(expired_ids),
        "sample_ids": expired_ids[:20],
        "definitions": {
            "verified": "review_log 有 true/false 或 validation 已判定",
            "needs_spec": "有 falsifiable_rule，30 天内需补 metric/op/threshold/due_d",
            "expired": "有规则但超 30 天未补规格，停止计入能力",
            "archived": "无可证伪规则的纯经验，超 14 天归档（不删除）",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"认知清算_{target}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "最新.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    target = args.target
    if not target:
        import sys
        sys.path.insert(0, str(ROOT))
        import trading_calendar as tc
        target = tc.load_trading_calendar()[-1]
    result = clear(target, args.apply)
    print(json.dumps({k: result[k] for k in ("at", "applied", "total", "counts", "needs_spec_or_expired")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
