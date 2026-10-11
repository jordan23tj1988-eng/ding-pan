# -*- coding: utf-8 -*-
"""认知迭代/自主拓展的到期审计 + T+1 机械验证与能力化（唯一真源入口）。

本文件保留原节点名（日链 `认知迭代全量更新.py` 与本图引用不变），
实现已统一到 `能力验证闭环.py`，避免出现两份验证逻辑各自漂移。

两条铁律：
1. **不猜命中**：没有绑定目标日证据的条件一律 `unverifiable`，绝不用自然语言
   经验或事后行情推成"已验证"。无法机械解析的条件永远保持不可验证。
2. **有证据才能力化**：只有结构化 `validation_spec` 的全部证据项在结算日
   （含当日）之前真实存在且判定算子通过，且该条目带能力规则/可证伪规则，
   才允许晋升 `state=capability` + `validation=validated` + `capitalized=True`。
   其余条目保持 experience/待验证——**不得进入次日判断层**。
"""
from __future__ import annotations
import argparse, datetime as dt, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from 能力验证闭环 import (  # noqa: E402  唯一真源
    LEDGERS, ROOT as _IMPL_ROOT, LEARN, evaluate, get_path, get_records,
    load, normalize_date, review_one, run, text_of,
)

__all__ = ["run", "review_one", "evaluate", "load", "get_records", "normalize_date", "LEDGERS", "LEARN"]


def iso_today():
    return dt.date.today().isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=dt.date.today().strftime("%Y%m%d"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        print(json.dumps(run(args.as_of, args.dry_run), ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "fail", "as_of": args.as_of, "errors": [str(exc)]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
