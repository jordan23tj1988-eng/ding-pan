# -*- coding: utf-8 -*-
"""认知验证闭环。

目标不是把经验强行判成命中，而是让每条认知在到期/复核时留下明确的
"已验证 / 已证伪 / 不可验证"审计记录。无法机械解析的条件必须保持不可验证。
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LEARN = ROOT / "_学习"
DB = LEARN / "能力进化库_认知迭代.json"


def load(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic(path: Path, data: Any):
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def iso_today():
    return dt.date.today().isoformat()


def get_records(doc: Any) -> tuple[list[dict], str]:
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)], "list"
    if isinstance(doc, dict):
        for key in ("records", "认知迭代", "items", "data"):
            if isinstance(doc.get(key), list):
                return [x for x in doc[key] if isinstance(x, dict)], key
    return [], "list"


def text_of(r: dict, *keys: str) -> str:
    for k in keys:
        if r.get(k) not in (None, "", [], {}):
            return str(r[k])
    return ""


def has_mechanical_rule(rule: str) -> bool:
    # 只承认已具备明确比较符、指标和阈值的规则；自然语言条件不自动判命中。
    if not rule or len(rule.strip()) < 8:
        return False
    has_cmp = bool(re.search(r"(?:>=|<=|>|<|≥|≤|大于|小于|不少于|不低于|不超过|低于|高于)", rule))
    has_number = bool(re.search(r"\d+(?:\.\d+)?\s*%?", rule))
    has_metric = bool(re.search(r"涨幅|收益|胜率|封板|炸板|温度|成交额|连板|回撤|覆盖|高开|跌幅|价格|量能|样本", rule))
    return has_cmp and has_number and has_metric


def review_one(r: dict, as_of: str) -> dict | None:
    logs = r.get("review_log")
    if not isinstance(logs, list):
        logs = r.get("复核日志") if isinstance(r.get("复核日志"), list) else []
    rule = text_of(r, "falsifiable_rule", "可证伪条件", "可证伪规则")
    # 不重复写同一天同状态记录；历史验证/证伪记录原样保留。
    if any(isinstance(x, dict) and x.get("reviewed_at", "")[:10] == as_of and x.get("status") in {"unverifiable", "verified", "falsified"} for x in logs):
        return None
    if not rule:
        status, reason = "unverifiable", "缺少结构化可证伪条件，不能从自然语言经验推导结果"
    elif not has_mechanical_rule(rule):
        status, reason = "unverifiable", "已有条件但未达到机械解析要求（指标/比较符/阈值不完整）"
    else:
        # 有机械形态也不代表有结果；真正的行情证据尚未绑定时只能挂起。
        status, reason = "unverifiable", "规则可解析，但未找到与该认知绑定的目标日结果，禁止猜测命中"
    event = {
        "reviewed_at": as_of + "T00:00:00+08:00",
        "as_of": as_of,
        "status": status,
        "reason": reason,
        "evidence": [],
        "rule_snapshot": rule,
    }
    logs.append(event)
    r["review_log"] = logs
    r["review_status"] = status
    r["last_reviewed_at"] = event["reviewed_at"]
    return event


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default=iso_today())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    doc = load(DB, {})
    records, container = get_records(doc)
    if not records:
        print(json.dumps({"status": "no_records", "file": str(DB)}, ensure_ascii=False))
        return 0
    changed = events = 0
    counts = {}
    for r in records:
        event = review_one(r, args.as_of)
        if event:
            changed += 1; events += 1
            counts[event["status"]] = counts.get(event["status"], 0) + 1
    if not args.dry_run and changed:
        if container == "list":
            out = records
        else:
            out = dict(doc); out[container] = records
        out["last_review_run"] = {"as_of": args.as_of, "events": events, "policy": "不可验证不等于失败，不计入命中/能力化"}
        atomic(DB, out)
    print(json.dumps({"status": "pass", "as_of": args.as_of, "records": len(records), "new_review_events": events, "counts": counts, "dry_run": args.dry_run, "policy": "不自动判命中；无绑定证据保持unverifiable"}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
