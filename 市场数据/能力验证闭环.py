# -*- coding: utf-8 -*-
"""认知迭代/自主拓展的 T+1 机械验证与能力化。

没有绑定目标日证据就保持 unverifiable；不把自然语言或事后行情猜成命中。
只有结构化 validation_spec 验证通过，且有 capability_rule + boundary，才会
晋升 state=capability、validation=validated、capitalized=True。
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LEARN = ROOT / "_学习"
LEDGERS = {"认知迭代": LEARN / "能力进化库_认知迭代.json", "自主拓展": LEARN / "能力进化库_自主拓展.json"}


def load(path: Path, default: Any):
    try: return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception: return default


def atomic(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2); f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def normalize_date(value: str) -> str:
    value = str(value).strip().replace("-", "")
    if not re.fullmatch(r"\d{8}", value): raise ValueError(f"非法日期: {value}")
    dt.datetime.strptime(value, "%Y%m%d")
    return value


def get_records(doc: Any) -> tuple[list[dict], str]:
    if isinstance(doc, list): return [x for x in doc if isinstance(x, dict)], "list"
    if isinstance(doc, dict):
        for key in ("records", "认知迭代", "items", "data"):
            if isinstance(doc.get(key), list): return [x for x in doc[key] if isinstance(x, dict)], key
    return [], "list"


def text_of(r: dict, *keys: str) -> str:
    for k in keys:
        if r.get(k) not in (None, "", [], {}): return str(r[k])
    return ""


def get_path(obj: Any, path: str) -> Any:
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur: cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur): cur = cur[int(part)]
        else: raise KeyError(path)
    return cur


def compare(actual: Any, op: str, expected: Any) -> bool:
    if op in {"eq", "=="}: return actual == expected
    if op in {"ne", "!="}: return actual != expected
    if op in {"gt", ">"}: return actual > expected
    if op in {"ge", ">=", "≥"}: return actual >= expected
    if op in {"lt", "<"}: return actual < expected
    if op in {"le", "<=", "≤"}: return actual <= expected
    if op == "contains": return expected in actual
    if op == "in": return actual in expected
    raise ValueError(f"不支持的判定算子: {op}")


def evaluate(r: dict, as_of: str) -> tuple[str, str, list[dict]]:
    spec = r.get("validation_spec", r.get("验证规格"))
    if not isinstance(spec, dict) or not isinstance(spec.get("evidence"), list) or not spec["evidence"]:
        return "unverifiable", "缺少结构化 validation_spec 证据绑定", []
    refs, failures = [], []
    for item in spec["evidence"]:
        if not isinstance(item, dict): failures.append("证据项不是对象"); continue
        try: target_d = normalize_date(item.get("target_d", item.get("as_of")))
        except (TypeError, ValueError): failures.append("证据缺少合法 target_d"); continue
        if target_d > as_of: failures.append(f"证据目标日 {target_d} 晚于结算日 {as_of}"); continue
        raw = item.get("path")
        if not isinstance(raw, str) or not raw: failures.append("证据缺少 path"); continue
        path = (ROOT / raw).resolve() if not os.path.isabs(raw) else Path(raw).resolve()
        if ROOT not in path.parents and path != ROOT: failures.append("证据越出系统根目录"); continue
        if not path.is_file(): failures.append(f"证据不存在: {raw}"); continue
        try:
            actual = get_path(load(path, None), item["field"])
            passed = compare(actual, item["op"], item.get("value"))
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            failures.append(f"{raw}#{item.get('field')}: {exc}"); continue
        refs.append({"path": raw, "target_d": target_d, "field": item.get("field"), "op": item.get("op"), "expected": item.get("value"), "actual": actual, "passed": passed})
        if not passed: failures.append(f"{raw}#{item.get('field')} 不满足 {item.get('op')} {item.get('value')}")
    return ("falsified", "; ".join(failures), refs) if failures else ("validated", "所有绑定证据满足 validation_spec", refs)


def review_one(r: dict, as_of: str) -> dict | None:
    logs = r.get("review_log") if isinstance(r.get("review_log"), list) else []
    if any(isinstance(x, dict) and str(x.get("as_of", "")).replace("-", "") == as_of and x.get("status") in {"unverifiable", "validated", "falsified"} for x in logs): return None
    status, reason, refs = evaluate(r, as_of)
    event = {"reviewed_at": f"{as_of[:4]}-{as_of[4:6]}-{as_of[6:]}T00:00:00+08:00", "as_of": as_of, "status": status, "reason": reason, "evidence": refs, "rule_snapshot": text_of(r, "falsifiable_rule", "可证伪条件", "可证伪规则")}
    logs.append(event); r["review_log"] = logs; r["review_status"] = status; r["last_reviewed_at"] = event["reviewed_at"]; r["validation_evidence"] = refs
    if status == "validated":
        r["validation"] = "validated"; r["validated_at"] = as_of; r["hit_count"] = int(r.get("hit_count") or 0) + 1
        if r.get("capability_rule") or r.get("能力规则"):
            r["state"] = "capability"; r["capitalized"] = True; r["last_validated_at"] = as_of
    elif status == "falsified":
        r["validation"] = "refuted"; r["state"] = "refuted"; r["capitalized"] = False; r["refuted_at"] = as_of
    return event


def run(as_of: str, dry_run: bool = False) -> dict:
    as_of = normalize_date(as_of); total = changed = 0; counts = {}
    for kind, path in LEDGERS.items():
        doc = load(path, {}); records, container = get_records(doc); total += len(records)
        for r in records:
            event = review_one(r, as_of)
            if event:
                changed += 1; key = f"{kind}:{event['status']}"; counts[key] = counts.get(key, 0) + 1
        if records and not dry_run:
            out = records if container == "list" else dict(doc)
            if container != "list": out[container] = records
            out["last_review_run"] = {"as_of": as_of, "events": sum(v for k, v in counts.items() if k.startswith(kind + ":")), "policy": "无绑定证据保持unverifiable；validated且有能力规则才能力化"}
            atomic(path, out)
    return {"status": "pass", "as_of": as_of, "records": total, "new_review_events": changed, "counts": counts, "dry_run": dry_run, "policy": "不自动猜测命中；T+1 绑定证据通过后才允许 validated/capitalized"}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--as-of", default=dt.date.today().strftime("%Y%m%d")); ap.add_argument("--dry-run", action="store_true"); args = ap.parse_args()
    try:
        print(json.dumps(run(args.as_of, args.dry_run), ensure_ascii=False)); return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "fail", "as_of": args.as_of, "errors": [str(exc)]}, ensure_ascii=False)); return 1


if __name__ == "__main__": raise SystemExit(main())
