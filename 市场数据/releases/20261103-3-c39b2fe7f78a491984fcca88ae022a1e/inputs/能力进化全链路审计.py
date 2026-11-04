# -*- coding: utf-8 -*-
"""自我深挖/认知迭代全链路审计。

只读审计，不负责创造证据、不晋升能力、不修改两本账本。
它把“发现存在”“验证通过”“实际复用”“后续命中”四件事拆开，
并在启用日后对每日能力消费产物执行 fail-closed 检查。
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROUTES = ("auction", "lhb", "theme", "logic", "limitup", "cycle", "master")
ACTIVATION_DATE = "20261001"
LEDGERS = {
    "自主拓展": "能力进化库_自主拓展.json",
    "认知迭代": "能力进化库_认知迭代.json",
}


def _date(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{8}", value):
        raise ValueError("日期必须是 YYYYMMDD")
    datetime.strptime(value, "%Y%m%d")
    return value


def _load(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def _records(doc: Any) -> list[dict]:
    rows = doc.get("records") if isinstance(doc, dict) else doc
    return [x for x in (rows or []) if isinstance(x, dict)]


def _strict(row: dict, as_of: str) -> bool:
    date = str(row.get("date", row.get("d", "00000000"))).replace("-", "")
    spec = row.get("validation_spec")
    return (
        date <= as_of
        and row.get("validation") == "validated"
        and row.get("capitalized") is True
        and bool(row.get("capability_rule") or row.get("falsifiable_rule"))
        and bool(row.get("boundary"))
        and isinstance(spec, dict)
        and bool(spec)
    )


def _audit(root: Path, d: str, require_daily: bool) -> dict:
    learn = root / "_学习"
    errors: list[str] = []
    warnings: list[str] = []
    ledger_rows: list[dict] = []
    ledger_summary: dict[str, dict] = {}
    for kind, filename in LEDGERS.items():
        path = learn / filename
        doc = _load(path)
        rows = _records(doc)
        if not rows:
            errors.append(f"{kind}账本缺失或records为空: {path}")
        ledger_rows.extend(rows)
        ledger_summary[kind] = {
            "records": len(rows),
            "strict_reusable": sum(_strict(x, d) for x in rows),
            "validation_passes": sum(int(x.get("validation_pass_count") or 0) for x in rows),
            "reused": sum(int(x.get("reused_count") or 0) for x in rows),
            "hits": sum(int(x.get("hit_count") or 0) for x in rows),
            "missing_boundary": sum(not bool(x.get("boundary")) for x in rows),
            "missing_validation_spec": sum(not isinstance(x.get("validation_spec"), dict) or not x.get("validation_spec") for x in rows),
        }
        if path.exists() and path.stat().st_size == 0:
            errors.append(f"账本为空文件: {path}")

    daily = {
        "preload": learn / f"能力预加载_{d}.json",
        "receipt": learn / f"能力使用回执_{d}.json",
        "consumption_audit": learn / f"能力消费审计_{d}.json",
    }
    daily_exists = {key: path.is_file() for key, path in daily.items()}
    daily_check = {"required": require_daily, "files": {k: str(v) for k, v in daily.items()}, "exists": daily_exists}
    if require_daily:
        for key, exists in daily_exists.items():
            if not exists:
                errors.append(f"启用日缺少能力链产物: {key} -> {daily[key]}")
        if all(daily_exists.values()):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("capability_wiring", root / "能力进化接线.py")
                module = importlib.util.module_from_spec(spec)
                assert spec and spec.loader
                spec.loader.exec_module(module)
                result = module.validate(root, d)
                daily_check["wiring_validate"] = result
            except Exception as exc:  # 审计必须把真实错误落到产物
                errors.append(f"能力进化接线validate失败: {exc}")
                daily_check["wiring_validate"] = {"status": "fail", "error": str(exc)}
            audit_doc = _load(daily["consumption_audit"])
            if not isinstance(audit_doc, dict) or audit_doc.get("status") != "pass":
                errors.append("能力消费审计不存在pass状态")

    # 计数语义自检：验证通过与命中必须分别有自己的证据计数。
    for row in ledger_rows:
        vp = int(row.get("validation_pass_count") or 0)
        hit = int(row.get("hit_count") or 0)
        if vp and hit > vp and not row.get("hit_log"):
            warnings.append(f"记录{row.get('id')} hit_count高于validation_pass_count且缺hit_log，需人工复核")
        if hit and not (row.get("hit_log") or row.get("reuse_log")):
            warnings.append(f"记录{row.get('id')}已有hit_count但缺hit_log/reuse_log，历史口径不完整")

    strict_total = sum(_strict(x, d) for x in ledger_rows)
    result = {
        "schema_version": 1,
        "as_of": d,
        "activation_date": ACTIVATION_DATE,
        "scope": "自我深挖与认知迭代发现→验证→能力化→预加载→七路消费→结算命中全链路只读审计",
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "routes": list(ROUTES),
        "ledger_summary": ledger_summary,
        "strict_reusable_total": strict_total,
        "daily": daily_check,
        "policy": {
            "validation_pass_is_not_hit": True,
            "hit_requires_followup_object_date_result": True,
            "missing_evidence_is_not_success": True,
            "candidate_pool_cannot_enter_preload": True,
        },
    }
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("d")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--require-daily", action="store_true")
    args = ap.parse_args(argv)
    try:
        d = _date(args.d)
        root = args.root.resolve()
        result = _audit(root, d, args.require_daily)
        out = args.out or root / "_学习" / f"能力全链路审计_{d}.json"
        out = out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "as_of": d, "artifact": str(out), "errors": len(result["errors"]), "warnings": len(result["warnings"]), "strict_reusable_total": result["strict_reusable_total"]}, ensure_ascii=False))
        return 0 if result["status"] == "pass" else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "fail", "as_of": args.d, "errors": [str(exc)]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
