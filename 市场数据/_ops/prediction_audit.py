# -*- coding: utf-8 -*-
"""预测审计：逐日结算推演，统计“可机判覆盖率”和“已判命中率”。

两个口径必须分开，禁止混用：
- coverage = 有 field/op/threshold 的机器行 / 全部预测行
- judgeable = (true+false) / (true+false+unverifiable+ambiguous)  # 已到期样本

`--strict` 只约束 schema_version>=2 的新格式：覆盖率 <70% 退出 1。
历史 legacy 文件不追改、不补造，只如实统计。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
LEARN = ROOT / "_学习"
OUT = LEARN / "_预测审计"
sys.path.insert(0, str(ROOT))
import review_learning as rl  # noqa: E402
import trading_calendar as tc  # noqa: E402


def audit(target=None) -> dict:
    cal = tc.load_trading_calendar()
    target = target or (cal[-1] if cal else None)
    if not target:
        return {"status": "fail", "reason": "无交易日历"}
    days = []
    total = {"rows": 0, "machine": 0, "true": 0, "false": 0,
             "unverifiable": 0, "ambiguous": 0, "pending": 0, "not_triggered": 0}
    strict_fail = []
    for path in sorted(LEARN.glob("推演_2026*.json")):
        d = "".join(ch for ch in path.stem if ch.isdigit())
        if len(d) != 8 or d > target:
            continue
        try:
            rows = rl._prediction_rows(ROOT, d)
            settled = rl._settle_rows(ROOT, d, target)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            days.append({"d": d, "error": f"{type(exc).__name__}: {exc}"})
            continue
        counts = {key: sum(x["status"] == key for x in settled)
                  for key in ("true", "false", "unverifiable", "ambiguous", "pending", "not_triggered")}
        machine = sum(1 for x in rows if x.get("field") and x.get("op") and x.get("threshold") is not None)
        due = counts["true"] + counts["false"] + counts["unverifiable"] + counts["ambiguous"]
        item = {"d": d, "rows": len(rows), "machine": machine,
                "coverage": round(machine / len(rows), 4) if rows else None,
                "judgeable": round((counts["true"] + counts["false"]) / due, 4) if due else None,
                "status": counts, "schema_version": 1}
        days.append(item)
        total["rows"] += len(rows)
        total["machine"] += machine
        for key in counts:
            total[key] += counts[key]
        if path.name.startswith("推演_") and item["coverage"] is not None and item["coverage"] < 0.70:
            # legacy 文件不阻断；只在 schema_version>=2 时阻断。
            try:
                if int(json.loads(path.read_text(encoding="utf-8")).get("schema_version", 1)) >= 2:
                    strict_fail.append(d)
                    item["schema_version"] = 2
            except (OSError, ValueError, TypeError):
                pass
    due = total["true"] + total["false"] + total["unverifiable"] + total["ambiguous"]
    result = {
        "schema_version": 1, "status": "pass", "target": target,
        "coverage": round(total["machine"] / total["rows"], 4) if total["rows"] else None,
        "judgeable": round((total["true"] + total["false"]) / due, 4) if due else None,
        "totals": total, "days": days,
        "strict_fail": strict_fail,
        "definitions": {
            "coverage": "机器行(有 field/op/threshold) / 全部预测行；衡量多少预测可被机器判",
            "judgeable": "(true+false) / 已到期(true+false+unverifiable+ambiguous)；衡量已判样本的判定率",
            "target": "新格式 coverage>=70%；legacy 不追改不阻断",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"预测审计_{target}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "最新.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    result = audit(args.target)
    print(json.dumps({k: result.get(k) for k in ("status", "target", "coverage", "judgeable", "totals", "strict_fail")},
                     ensure_ascii=False, indent=1))
    if args.strict and result.get("strict_fail"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
