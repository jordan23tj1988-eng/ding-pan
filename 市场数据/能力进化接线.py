# -*- coding: utf-8 -*-
"""自主拓展/认知迭代的先验加载、消费回执与复用记账。

这是判断链的机械接线层，不负责替任何路做业务判断：

1. prepare: 判断前读取历史双账本，生成日期化能力预加载快照；
2. consume: 判断后校验七路消费回执，并只为有明确证据的 applied 记录增加复用次数；
3. 缺预加载、缺路、缺消费回执或引用未知能力时 fail-closed。

严格口径：只有 validation=validated 且 capitalized=True 的记录才进入可复用能力池。
历史 state=capability 但缺少这两个证据字段的旧记录不会被冒充成能力。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTES = ("auction", "lhb", "theme", "logic", "limitup", "cycle", "master")
ACTIVATION_DATE = "20261001"
PRELOAD_NAME = "能力预加载_{d}.json"
RECEIPT_NAME = "能力使用回执_{d}.json"
AUDIT_NAME = "能力消费审计_{d}.json"
LEDGER_NAMES = {
    "自主拓展": "能力进化库_自主拓展.json",
    "认知迭代": "能力进化库_认知迭代.json",
}


def _date(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{8}", value):
        raise ValueError("日期必须是 YYYYMMDD")
    datetime.strptime(value, "%Y%m%d")
    return value


def _learn(root: Path) -> Path:
    p = root / "_学习"
    if not p.is_dir():
        raise ValueError(f"学习目录不存在: {p}")
    return p


def _load(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=False)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _records(doc: Any) -> list[dict]:
    rows = doc.get("records") if isinstance(doc, dict) else doc
    return [x for x in (rows or []) if isinstance(x, dict)]


def _is_reusable(row: dict, as_of: str) -> bool:
    """能力池门槛：旧的 capability 状态不足以单独进入判断层。"""
    if str(row.get("date", row.get("d", "00000000"))).replace("-", "") > as_of:
        return False
    return (
        row.get("validation") == "validated"
        and row.get("capitalized") is True
        and bool(row.get("capability_rule") or row.get("falsifiable_rule"))
    )


def _projection(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "kind": row.get("kind"),
        "route": row.get("route"),
        "title": row.get("title") or row.get("claim") or row.get("body"),
        "capability_rule": row.get("capability_rule") or row.get("falsifiable_rule"),
        "boundary": row.get("boundary"),
        "validation": row.get("validation"),
        "validation_evidence": row.get("validation_evidence") or row.get("evidence"),
        "source": row.get("source"),
        "last_validated_at": row.get("last_validated_at"),
    }


def _source_manifest(learn: Path) -> list[dict]:
    result = []
    for filename in LEDGER_NAMES.values():
        path = learn / filename
        if not path.is_file():
            result.append({"path": str(Path("_学习") / filename), "status": "missing"})
        else:
            result.append({
                "path": str(Path("_学习") / filename),
                "status": "valid",
                "sha256": _sha256(path),
            })
    return result


def prepare(root: Path, d: str, write: bool = True) -> dict:
    """在当日判断前生成能力预加载快照。"""
    d = _date(d)
    root = Path(root).resolve()
    learn = _learn(root)
    all_rows: list[dict] = []
    by_route = {route: [] for route in ROUTES}
    for kind, filename in LEDGER_NAMES.items():
        doc = _load(learn / filename, {})
        for row in _records(doc):
            row = dict(row)
            row.setdefault("kind", kind)
            all_rows.append(row)
            route = str(row.get("route") or "").strip().lower()
            if route in by_route and _is_reusable(row, d):
                by_route[route].append(_projection(row))

    payload = {
        "schema_version": 1,
        "as_of": d,
        "decision_cutoff": d,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "activation_date": ACTIVATION_DATE,
        "source": "能力进化库_自主拓展.json + 能力进化库_认知迭代.json",
        "source_manifest": _source_manifest(learn),
        "policy": "仅 validation=validated 且 capitalized=true 且有能力规则的记录可进入判断层；其余保持待验证，不得冒充能力",
        "routes": {
            route: {
                "eligible_count": len(by_route[route]),
                "status": "ready" if by_route[route] else "no_eligible_capabilities",
                "records": by_route[route],
            }
            for route in ROUTES
        },
        "eligible_total": sum(len(v) for v in by_route.values()),
        "historical_record_count": len(all_rows),
    }
    if write:
        _atomic(learn / PRELOAD_NAME.format(d=d), payload)
    return payload


def _preload(root: Path, d: str) -> tuple[Path, dict]:
    learn = _learn(root)
    path = learn / PRELOAD_NAME.format(d=d)
    doc = _load(path)
    if not isinstance(doc, dict):
        raise ValueError(f"缺少能力预加载或格式错误: {path}")
    if doc.get("as_of") != d or doc.get("decision_cutoff") != d:
        raise ValueError("能力预加载日期/决策截止日错配")
    if doc.get("schema_version") != 1:
        raise ValueError("能力预加载 schema_version 不支持")
    return path, doc


def _validate_receipt(root: Path, d: str) -> tuple[dict, dict]:
    preload_path, preload = _preload(root, d)
    learn = _learn(root)
    receipt_path = learn / RECEIPT_NAME.format(d=d)
    receipt = _load(receipt_path)
    if not isinstance(receipt, dict):
        raise ValueError(f"缺少能力使用回执或格式错误: {receipt_path}")
    if receipt.get("schema_version") != 1 or receipt.get("as_of") != d:
        raise ValueError("能力使用回执 schema/date 错配")
    expected_hash = _sha256(preload_path)
    if receipt.get("preload", {}).get("sha256") != expected_hash:
        raise ValueError("能力使用回执未绑定本次能力预加载快照")
    route_map = receipt.get("routes")
    if not isinstance(route_map, dict) or set(route_map) != set(ROUTES):
        raise ValueError(f"能力使用回执必须覆盖七域: {ROUTES}")

    eligible = {
        route: {str(x.get("id")): x for x in (preload.get("routes", {}).get(route, {}).get("records") or [])}
        for route in ROUTES
    }
    events = []
    for route in ROUTES:
        item = route_map[route]
        if not isinstance(item, dict):
            raise ValueError(f"{route}: 能力消费回执必须为对象")
        status = item.get("status")
        allowed = {"ready", "applied", "rejected_all", "no_eligible_capabilities", "not_applicable"}
        if status not in allowed:
            raise ValueError(f"{route}: 未知能力消费状态 {status}")
        considered = item.get("considered_ids") or []
        applied = item.get("applied") or []
        rejected = item.get("rejected") or []
        if not isinstance(considered, list) or len(considered) != len(set(considered)):
            raise ValueError(f"{route}: considered_ids 缺失或重复")
        if set(considered) != set(eligible[route]):
            raise ValueError(f"{route}: 必须逐条回应本路全部可复用能力")
        if not eligible[route] and status not in {"no_eligible_capabilities", "not_applicable"}:
            raise ValueError(f"{route}: 无可复用能力时必须明确 no_eligible_capabilities")
        if eligible[route] and status not in {"applied", "rejected_all"}:
            raise ValueError(f"{route}: 有可复用能力却未给出采用/拒绝状态")
        seen = set()
        for event in applied:
            if not isinstance(event, dict) or event.get("id") not in eligible[route]:
                raise ValueError(f"{route}: applied 引用了未知能力")
            if event["id"] in seen:
                raise ValueError(f"{route}: applied 能力重复")
            if not event.get("effect") or not event.get("source_locator"):
                raise ValueError(f"{route}: applied 必须写 effect 和 source_locator")
            seen.add(event["id"])
            events.append({"route": route, "id": event["id"], "event": event})
        for event in rejected:
            if not isinstance(event, dict) or event.get("id") not in eligible[route]:
                raise ValueError(f"{route}: rejected 引用了未知能力")
            if not event.get("reason"):
                raise ValueError(f"{route}: rejected 必须写明 reason")
    return receipt, {"preload_path": preload_path, "preload": preload, "events": events}


def validate(root: Path, d: str) -> dict:
    """只读校验当日七域能力消费回执，不修改账本。"""
    d = _date(d)
    root = Path(root).resolve()
    _receipt, checked = _validate_receipt(root, d)
    return {"status": "pass", "as_of": d, "applied_candidates": len(checked["events"]),
            "preload": str(Path("_学习") / PRELOAD_NAME.format(d=d)),
            "receipt": str(Path("_学习") / RECEIPT_NAME.format(d=d))}


def consume(root: Path, d: str, write: bool = True) -> dict:
    """校验回执并把真实 applied 事件写回两个能力账本。"""
    d = _date(d)
    root = Path(root).resolve()
    receipt, checked = _validate_receipt(root, d)
    learn = _learn(root)
    ledger_docs = {
        kind: _load(learn / filename, {}) for kind, filename in LEDGER_NAMES.items()
    }
    by_id = {}
    for kind, doc in ledger_docs.items():
        for row in _records(doc):
            if row.get("id"):
                by_id[str(row["id"])] = (kind, row)

    applied = []
    for item in checked["events"]:
        found = by_id.get(item["id"])
        if not found:
            raise ValueError(f"消费回执引用的能力不在双账本: {item['id']}")
        kind, row = found
        event = dict(item["event"])
        event.update({"as_of": d, "route": item["route"], "ledger_kind": kind})
        log = row.get("reuse_log")
        if not isinstance(log, list):
            log = []
        fingerprint = json.dumps(event, ensure_ascii=False, sort_keys=True)
        if not any(json.dumps(x, ensure_ascii=False, sort_keys=True) == fingerprint for x in log if isinstance(x, dict)):
            log.append(event)
            row["reuse_log"] = log
            row["reused_count"] = int(row.get("reused_count") or 0) + 1
            row["last_reused_at"] = d
            if kind == "认知迭代":
                routes = row.get("feedback_routes")
                if not isinstance(routes, list):
                    routes = []
                if item["route"] not in routes:
                    routes.append(item["route"])
                row["feedback_routes"] = routes
            applied.append({"id": item["id"], "route": item["route"], "kind": kind})

    audit = {
        "schema_version": 1,
        "as_of": d,
        "preload": {"path": str(Path("_学习") / PRELOAD_NAME.format(d=d)), "sha256": _sha256(checked["preload_path"])},
        "receipt": {"path": str(Path("_学习") / RECEIPT_NAME.format(d=d)), "sha256": _sha256(learn / RECEIPT_NAME.format(d=d))},
        "status": "pass",
        "applied_events": applied,
        "applied_count": len(applied),
        "policy": "仅回执中有 effect+source_locator 的 applied 事件计入 reused_count；拒绝/无能力不计数",
    }
    if write:
        for kind, filename in LEDGER_NAMES.items():
            _atomic(learn / filename, ledger_docs[kind])
        _atomic(learn / AUDIT_NAME.format(d=d), audit)
    return audit


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("prepare", "validate", "consume"))
    ap.add_argument("d")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = ap.parse_args(argv)
    try:
        d = _date(args.d)
        root = args.root.resolve()
        if args.command == "prepare":
            result = prepare(root, d, write=True)
        elif args.command == "validate":
            result = validate(root, d)
        else:
            result = consume(root, d, write=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "fail", "as_of": args.d, "errors": [str(exc)]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
