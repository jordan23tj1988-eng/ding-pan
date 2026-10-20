"""P3 离线评估工具。旧档案只读；无隐式网络、配置或生产写入。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import os
import sys
from pathlib import Path
import re
import secrets
import signal
import subprocess
import tempfile
import time
import uuid

VERSION = 1
ROUTES = ("auction", "lhb", "theme", "logic", "limitup")
TZ = timezone(timedelta(hours=8))
UNITS = {"涨停数": "家", "炸板数": "家", "跌停数": "家", "炸板率": "ratio",
         "封板率": "ratio", "温度": "分", "温度档": None, "最高连板": "板",
         "题材线数": "条", "归位数量": "家", "归位A档数": "家", "归位B档数": "家",
         "归位C档数": "家", "回封数": "家", "二板加": "家", "成交额亿": "亿元", "封板总额亿": "亿元"}
OPS = {"gt": lambda a,b:a>b, "gte": lambda a,b:a>=b, "lt": lambda a,b:a<b,
       "lte": lambda a,b:a<=b, "eq": lambda a,b:a==b}


def _date(d):
    if not isinstance(d, str) or not re.fullmatch(r"[0-9]{8}", d):
        raise ValueError("date must be strict YYYYMMDD")
    return datetime.strptime(d, "%Y%m%d").date()


def _stamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return dt


def _now():
    return datetime.now(timezone.utc).isoformat()


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _load(path):
    def invalid(v):
        raise ValueError("non-finite JSON: " + v)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid, object_pairs_hook=pairs)


def _fail(d, errors):
    return {"schema_version": VERSION, "status": "fail", "errors": [str(e) for e in errors], "d": d}


def _save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(_bytes(obj))


def _cutoff(d):
    day = _date(d)
    return datetime(day.year, day.month, day.day, 23, 59, 59, 999999, tzinfo=TZ)


def _temporal(data, d, context="source"):
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("date", "日期", "d") and value is not None:
                day = _date(value)
                if day > _date(d):
                    raise ValueError(context + ": future date")
            if key in ("as_of", "asof", "observed_at", "build_time") and value is not None:
                # Legacy build_time has no zone; only check its date, never use as proof.
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    if key != "build_time":
                        raise ValueError(context + ": as_of requires timezone")
                    dt = dt.replace(tzinfo=TZ)
                if dt > _cutoff(d):
                    raise ValueError(context + ": future timestamp")
            _temporal(value, d, context)
    elif isinstance(data, list):
        for value in data:
            _temporal(value, d, context)


def _schema():
    ref = {"type": "object", "additionalProperties": False,
           "required": ["source_id", "field", "value", "unit"],
           "properties": {"source_id": {"type": "string"}, "field": {"type": "string"},
                          "value": {"type": ["string", "number", "boolean", "null"]},
                          "unit": {"type": ["string", "null"]}}}
    return {"type": "object", "additionalProperties": False,
            "required": ["schema_version", "d", "case_hash", "event"],
            "properties": {"schema_version": {"const": 1}, "d": {"type": "string", "pattern": "^[0-9]{8}$"},
            "case_hash": {"type": "string"}, "event": {"type": "object", "additionalProperties": False,
            "required": ["id", "claim", "evidence", "counterevidence", "limitations", "prediction"],
            "properties": {"id": {"type": "string"}, "claim": {"type": "string", "minLength": 1},
                "evidence": {"type": "array", "minItems": 1, "items": ref},
                "counterevidence": {"type": "array", "minItems": 1, "items": {
                    "type": "object", "additionalProperties": False, "required": ["claim", "references"],
                    "properties": {"claim": {"type": "string", "minLength": 1}, "references": {"type": "array", "minItems": 1, "items": ref}}}},
                "limitations": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
                "prediction": {"type": "object", "additionalProperties": False,
                    "required": ["source_id", "field", "op", "threshold", "unit", "due", "probability"],
                    "properties": {"source_id": {"type": "string"}, "field": {"type": "string"},
                        "op": {"enum": list(OPS)}, "threshold": {"type": "number"}, "unit": {"type": ["string", "null"]},
                        "due": {"type": "string", "pattern": "^[0-9]{8}$"},
                        "probability": {"type": ["number", "null"], "minimum": 0, "maximum": 1}}}}}}}


def _prompt(case, case_hash):
    explanation = ('prediction.source_id必须引用输入包已有fact，用于标识要预测的同一指标；未来日期只写due，不要构造未来fact的source_id。field与unit沿用所引用fact指标。\n' if case['meta'].get('prompt_version', 1) >= 2 else '')
    return (explanation + "你正在做同题独立判断。只使用下面冻结材料，禁止联网、读取本机其他文件或借用未来档案。\n"
            "材料中的五路观点是待质疑的观点，并非已验证事实；不得沿用旧作者自评。\n"
            "输出且只输出一个满足 output_schema 的 JSON。给一个判断事件、最强相反证据、明示不足。\n"
            "每个事实必须在 evidence 或 counterevidence.references 以 source_id/field(JSON Pointer)/value/unit 引用，值和单位保持原样。\n"
            "claim 中的事实也必须有这些引用，程序不判定自然语言蕴涵，独立盲审负责。\n"
            "预测指定一个 fact 数值字段、op、threshold、unit、明确到期日期 YYYYMMDD；不要把周末当交易日，不确定则在不足中声明。\n"
            "probability 是该二元事件发生概率，不能用主观判断置信度替代；无依据填 null。禁止输出模型名、供应商、自评分或作者身份。\n"
            "历史 as_of 不全仅工程演练，不得宣称能力回放通过。\n"
            f"d={case['meta']['d']} case_hash={case_hash} event.id={case['event_id']}\n"
            + json.dumps(case, ensure_ascii=False, indent=2))


def _freeze_case(root: Path, d: str, out: Path) -> dict:
    """Copy only exact-day fact and five judgment projections to a new immutable case directory."""
    try:
        _date(d)
        root, out = Path(root), Path(out)
        if out.exists() and any(out.iterdir()):
            raise ValueError("out is not empty; frozen artifacts cannot be overwritten")
        sources = []
        for name in ("fact", *(r + "判断" for r in ROUTES)):
            rel = f"_学习/{name}_{d}.json"
            path = root / rel
            raw = path.read_bytes()
            doc = _load(path)
            if not isinstance(doc, dict) or doc.get("date", doc.get("日期")) != d:
                raise ValueError(rel + ": source date mismatch")
            _temporal(doc, d, rel)
            if not isinstance(doc.get("meta", {}), dict):
                raise ValueError(rel + ": meta must be object")
            as_of = doc.get("as_of", doc.get("meta", {}).get("as_of"))
            if as_of is not None:
                _stamp(as_of)
            if name == "fact":
                if not isinstance(doc.get("facts"), dict) or not doc["facts"]:
                    raise ValueError("fact fields missing")
                data = {"facts": doc["facts"]}
            else:
                judgment = doc.get("判断")
                if not isinstance(judgment, dict):
                    raise ValueError(rel + ": judgment missing")
                data = {"判断": {k: judgment.get(k) for k in ("结论", "证据", "档位", "独立盲区声明")}}
            sid = name + ":" + d
            snapshot = f"sources/{name}.json"
            sources.append({"source_id": sid, "kind": "fact" if name == "fact" else "judgment",
                            "date": d, "as_of": as_of, "source_path": rel,
                            "original_sha256": _hash(raw), "snapshot": snapshot,
                            "snapshot_sha256": _hash(_bytes(data)), "data": data,
                            "units": {"/facts/"+k+"/value": UNITS.get(k) for k in data.get("facts", {})},
                            "unit_basis": "fact-v1 read-only adapter; no numeric conversion" if name == "fact" else None})
        missing = [s["source_id"] for s in sources if s["as_of"] is None]
        case = {"schema_version": VERSION, "meta": {"d": d, "prompt_version": 2, "as_of": _cutoff(d).isoformat(),
                "as_of_basis": "end_of_day_cutoff_not_capture_time", "frozen_at": _now(),
                "missing_as_of": missing, "replay_status": "engineering_only" if missing else "requires_independent_provenance_review"},
                "event_id": f"E-{d}-001", "sources": sources, "output_schema": _schema()}
        digest = _hash(_bytes(case))
        prompt = _prompt(case, digest).encode("utf-8")
        out.mkdir(parents=True, exist_ok=True)
        for s in sources:
            _save(out / s["snapshot"], s["data"])
        _save(out / "case.json", case)
        (out / "prompt.txt").write_bytes(prompt)
        _save(out / "hashes.json", {"schema_version": VERSION, "case_sha256": digest, "prompt_sha256": _hash(prompt)})
        return {"schema_version": VERSION, "status": "ok", "d": d, "case_path": str(out / "case.json"),
                "case_hash": digest, "replay_status": case["meta"]["replay_status"]}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _fail(d, [exc])


def verify_case(case_path: Path) -> dict:
    d = None
    try:
        case_path = Path(case_path)
        case = _load(case_path)
        d = case["meta"]["d"]
        _date(d)
        directory = case_path.parent.resolve()
        hashes = _load(directory / "hashes.json")
        if _hash(case_path.read_bytes()) != hashes["case_sha256"]:
            raise ValueError("case hash mismatch")
        if _hash((directory / "prompt.txt").read_bytes()) != hashes["prompt_sha256"]:
            raise ValueError("prompt hash mismatch")
        for source in case["sources"]:
            path = (directory / source["snapshot"]).resolve()
            if not path.is_relative_to(directory):
                raise ValueError("snapshot path escapes case")
            if _hash(path.read_bytes()) != source["snapshot_sha256"] or _hash(_bytes(source["data"])) != source["snapshot_sha256"]:
                raise ValueError("snapshot hash mismatch")
            if source["date"] != d:
                raise ValueError("source date mismatch")
            _temporal(source, d)
        return {"schema_version": VERSION, "status": "ok", "d": d, "case_hash": hashes["case_sha256"], "case": case}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _fail(d, [exc])


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _validate_schema(value, schema, path="output"):
    """Validate the frozen contract's small, explicit JSON Schema subset."""
    errors = []
    types = {"object": lambda v:isinstance(v, dict), "array": lambda v:isinstance(v, list),
             "string": lambda v:isinstance(v, str), "number": _number,
             "boolean": lambda v:type(v) is bool, "null": lambda v:v is None}
    wanted = schema.get("type")
    if wanted and not any(types[t](value) for t in ([wanted] if isinstance(wanted, str) else wanted)):
        return [path + ": invalid type"]
    if "const" in schema and (value != schema["const"] or type(value) is bool):
        errors.append(path + ": const mismatch")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(path + ": enum mismatch")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(path + "." + key + ": required")
        if schema.get("additionalProperties") is False and set(value) - set(props):
            errors.append(path + ": additional properties forbidden")
        for key in props.keys() & value.keys():
            errors.extend(_validate_schema(value[key], props[key], path + "." + key))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(path + ": insufficient items")
        for i, item in enumerate(value):
            errors.extend(_validate_schema(item, schema.get("items", {}), path + f"[{i}]"))
    if isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errors.append(path + ": empty text")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(path + ": invalid format")
    if _number(value):
        if value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            errors.append(path + ": out of bounds")
    return errors


def _pointer(data, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("reference requires JSON Pointer")
    for key in pointer[1:].split("/"):
        key = key.replace("~1", "/").replace("~0", "~")
        if isinstance(data, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", key):
                raise ValueError("invalid reference index")
            data = data[int(key)]
        else:
            data = data[key]
    return data


def _resolve(case, ref):
    source = next((s for s in case["sources"] if s["source_id"] == ref["source_id"]), None)
    if source is None:
        raise ValueError("reference source_id not found")
    try:
        value = _pointer(source["data"], ref["field"])
    except (ValueError, KeyError, IndexError, TypeError):
        raise ValueError("reference field not found") from None
    return source, value, source["units"].get(ref["field"])


def _structure(body, verified, identities=()):
    case = verified["case"]
    errors = _validate_schema(body, case["output_schema"])
    # Identity detection is only an anonymity guard, never a semantic score.
    text = json.dumps(body, ensure_ascii=False).casefold()
    if any(str(identity).casefold() in text for identity in identities if identity and len(str(identity)) > 2) or re.search(
            r"\b(?:gpt[- ]?[0-9]|claude|deepseek|gemini|openai|anthropic)\b", text):
        errors.append("identity leakage; independent blinded redaction required")
    if errors:
        return errors
    if body["d"] != verified["d"]:
        errors.append("d mismatch")
    if body["case_hash"] != verified["case_hash"]:
        errors.append("case_hash mismatch")
    event = body["event"]
    if event["id"] != case["event_id"]:
        errors.append("event.id mismatch")
    refs = list(event["evidence"])
    for opposite in event["counterevidence"]:
        refs.extend(opposite["references"])
    for i, ref in enumerate(refs):
        try:
            source, value, unit = _resolve(case, ref)
            if ref["value"] != value or (type(ref["value"]) is bool) != (type(value) is bool):
                errors.append(f"reference[{i}].value mismatch")
            if ref["unit"] != unit:
                errors.append(f"reference[{i}].unit mismatch")
        except ValueError as exc:
            errors.append(str(exc))
    pred = event["prediction"]
    try:
        source, value, unit = _resolve(case, pred)
        if source["kind"] != "fact" or pred["field"] not in source["units"]:
            errors.append("prediction must address a fact value field")
        elif value is not None and not _number(value):
            errors.append("prediction fact must be numeric or null")
        if pred["unit"] != unit:
            errors.append("prediction.unit mismatch")
        due = _date(pred["due"])
        if due <= _date(body["d"]) or due.weekday() >= 5:
            errors.append("prediction.due must be a future weekday; exchange calendar still requires review")
    except (ValueError, KeyError) as exc:
        errors.append("prediction.due/reference: " + str(exc))
    return errors


def _usage(doc):
    raw = doc.get("usage")
    if raw is not None and not isinstance(raw, dict):
        raise ValueError("usage must be object or null")
    raw = raw or {}
    result = {k: raw.get(k) for k in ("input_tokens", "output_tokens", "cost", "currency")}
    for k in ("input_tokens", "output_tokens", "cost"):
        value = result[k]
        if value is not None and (not _number(value) or value < 0 or (k != "cost" and type(value) is not int)):
            raise ValueError("invalid usage " + k)
    if result["currency"] is not None and not isinstance(result["currency"], str):
        raise ValueError("invalid currency")
    return result


def _duration(doc):
    start, end = doc.get("started"), doc.get("ended")
    if start is None or end is None:
        return None
    duration = (_stamp(end) - _stamp(start)).total_seconds()
    if duration < 0:
        raise ValueError("negative timestamp duration")
    return duration


def _alias(index):
    result = ""
    index += 1
    while index:
        index, rem = divmod(index-1, 26)
        result = chr(65+rem) + result
    return result


def _evaluate_outputs(case_path: Path, outputs: list[Path], out: Path) -> dict:
    """Offline structural checks; randomized blind packet and separate private mapping."""
    verified = verify_case(case_path)
    if verified["status"] == "fail":
        return verified
    d = verified["d"]
    try:
        if not outputs:
            raise ValueError("outputs must not be empty")
        out = Path(out)
        if out.exists() and any(out.iterdir()):
            raise ValueError("comparison out is not empty")
        paths = [Path(p) for p in outputs]
        if len({p.resolve() for p in paths}) != len(paths):
            raise ValueError("duplicate output paths")
        secrets.SystemRandom().shuffle(paths)
        candidates, private = [], []
        for index, path in enumerate(paths):
            alias = _alias(index)
            doc, body, errors = {}, None, []
            usage, duration = {k: None for k in ("input_tokens", "output_tokens", "cost", "currency")}, None
            try:
                doc = _load(path)
                if not isinstance(doc, dict):
                    raise ValueError("output envelope must be object")
                body = doc.get("output", doc)
                errors = _structure(body, verified, [doc.get("provider"), doc.get("model"), doc.get("run_id"), path.name, path.stem])
                if "output" in doc and doc.get("d") != d:
                    errors.append("envelope d mismatch")
                usage, duration = _usage(doc), _duration(doc)
            except (OSError, ValueError, KeyError, TypeError):
                if not isinstance(doc, dict):
                    doc = {}
                errors.append("invalid JSON/envelope/usage/timestamps")
            candidates.append({"alias": alias, "structure": {"status": "fail" if errors else "pass", "errors": errors},
                               "semantic_score": None, "output": None if errors else body})
            private.append({"alias": alias, "path": str(path.resolve()), "output_sha256": _hash(path.read_bytes()) if path.is_file() else None,
                            "provider": doc.get("provider"), "model": doc.get("model"), "run_id": doc.get("run_id"),
                            "kind": doc.get("kind", "external_unverified"), "usage": usage, "duration": duration,
                            "started": doc.get("started"), "ended": doc.get("ended"),
                            "metrics_provenance": "reported_by_external_file_not_independently_attested"})
        report = {"schema_version": VERSION, "d": d, "case_hash": verified["case_hash"],
                  "replay_status": verified["case"]["meta"]["replay_status"], "candidates": candidates,
                  "semantic_review_status": "pending_independent_blind_review", "improvement_conclusion": None,
                  "calibration": None, "calendar_status": "weekday_checked_exchange_calendar_not_verified",
                  "blind_review_instructions": "仅提供本文件及冻结 case；不要提供 private、输出原件、runner 日志。独立评审事实蕴涵、反证力度及遗漏；格式通过不是语义通过。"}
        _save(out / "private" / "mapping.json", {"schema_version": VERSION, "d": d, "candidates": private})
        _save(out / "blind_review.json", report)
        failed = [r["alias"] for r in candidates if r["structure"]["status"] == "fail"]
        if failed:
            result = _fail(d, ["structural check failed: " + a for a in failed])
            result["report_path"] = str(out / "blind_review.json")
            return result
        return {"schema_version": VERSION, "status": "ok", "d": d, "report_path": str(out / "blind_review.json"),
                "n_outputs": len(candidates), "semantic_score": None, "improvement_conclusion": None}
    except (OSError, ValueError, TypeError) as exc:
        return _fail(d, [exc])


def _by_id(records, name):
    indexed = {}
    for record in records:
        if not isinstance(record, dict) or record.get("schema_version") != VERSION or not isinstance(record.get("id"), str) or not record["id"]:
            raise ValueError(name + ": invalid schema/id")
        if record["id"] in indexed:
            raise ValueError(name + ": duplicate id")
        indexed[record["id"]] = record
    return indexed


def calibration_report(root: Path, d: str, registrations: list[dict], forecasts: list[dict],
                       labels: list[dict], *, min_samples: int = 30, min_bin_samples: int = 10,
                       bins: int = 5) -> dict:
    """Brier/reliability on predeclared binary fact events and hashed actual due-date facts.

    Caller-supplied timestamp provenance still needs independent archival attestation.
    A confidence field is never read as probability. No automatic promotion conclusion.
    """
    try:
        _date(d)
        root = Path(root).resolve()
        if any(type(v) is not int or v < 1 for v in (min_samples, min_bin_samples, bins)) or bins > 100:
            raise ValueError("sample thresholds/bins must be positive integers; bins <= 100")
        events, predictions, outcomes = (_by_id(registrations, "registrations"), _by_id(forecasts, "forecasts"), _by_id(labels, "labels"))
        if set(predictions) - set(events) or set(outcomes) - set(events):
            raise ValueError("forecast/label id has no preregistered event")
        excluded = {k: 0 for k in ("missing_forecast", "no_probability", "pending", "missing_label", "missing_value")}
        counts = {"registered": len(events), "forecasts": len(predictions), "probability_available": 0, "due": 0, "scored": 0}
        scores, modes, details, unique = [], set(), [], set()
        for eid, event in events.items():
            day, due = _date(event["d"]), _date(event["due"])
            registered = _stamp(event["registered_at"])
            if event["d"] > d or due <= day or due.weekday() >= 5 or registered > _cutoff(event["d"]):
                raise ValueError("event date/due/registered_at invalid or future")
            if registered.astimezone(TZ).date() != day:
                raise ValueError("registration date must equal event d")
            if event["source_id"] != "fact" or event["op"] not in OPS or not _number(event["threshold"]):
                raise ValueError("invalid predeclared fact predicate")
            if event.get("mode") not in ("prospective", "controlled_test"):
                raise ValueError("event mode must declare prospective or controlled_test")
            modes.add(event["mode"])
            signature = _hash(_bytes({k: event[k] for k in ("d", "due", "source_id", "field", "op", "threshold", "unit")}))
            if signature in unique:
                raise ValueError("duplicate event predicate would inflate sample denominator")
            unique.add(signature)
            forecast = predictions.get(eid)
            reason = None
            if event["due"] <= d:
                counts["due"] += 1
            if forecast is None:
                reason = "missing_forecast"
            else:
                submitted = _stamp(forecast["submitted_at"])
                if forecast["d"] != event["d"] or not registered <= submitted <= _cutoff(event["d"]):
                    raise ValueError("forecast not submitted after registration and before due")
                probability = forecast.get("probability")
                if probability is None:
                    reason = "no_probability"
                elif not _number(probability) or not 0 <= probability <= 1:
                    raise ValueError("probability must be numeric within [0,1]")
                else:
                    counts["probability_available"] += 1
            if reason is None and event["due"] > d:
                reason = "pending"  # Do not open a future label file.
            label = outcomes.get(eid)
            if reason is None and label is None:
                reason = "missing_label"
            if reason is None:
                if label["d"] != event["due"] or label["field"] != event["field"] or label["unit"] != event["unit"]:
                    raise ValueError("label date/field/unit does not match registered event")
                observed = _stamp(label["observed_at"])
                if observed > _cutoff(d) or observed.astimezone(TZ).date() < due:
                    raise ValueError("future or premature label observation")
                expected_path = Path("_学习") / f"fact_{event['due']}.json"
                path = (root / label["source_path"]).resolve()
                if not path.is_relative_to(root) or path != (root / expected_path).resolve():
                    raise ValueError("label source must be exact due-date fact within root")
                if not path.is_file():
                    reason = "missing_label"
                else:
                    if _hash(path.read_bytes()) != label["sha256"]:
                        raise ValueError("label hash mismatch")
                    doc = _load(path)
                    if doc.get("date") != event["due"]:
                        raise ValueError("label source date mismatch")
                    _temporal(doc, d)
                    units = {"/facts/"+key+"/value": UNITS.get(key) for key in doc.get("facts", {})}
                    if event["field"] not in units or event["unit"] != units[event["field"]]:
                        raise ValueError("label source unit/field mismatch")
                    try:
                        value = _pointer(doc, event["field"])
                    except (ValueError, KeyError, IndexError, TypeError):
                        value = None
                    fact_quality = _pointer(doc, event["field"].rsplit("/", 1)[0]).get("quality")
                    if fact_quality == "conflicted":
                        raise ValueError("conflicted label cannot be settled")
                    if value is None:
                        reason = "missing_value"
                    elif not _number(value):
                        raise ValueError("label value is not numeric")
                    else:
                        outcome = int(OPS[event["op"]](value, event["threshold"]))
                        scores.append((probability, outcome))
                        details.append({"id": eid, "status": "scored", "probability": probability, "outcome": outcome,
                                        "source_path": label["source_path"], "sha256": label["sha256"],
                                        "field": event["field"], "value": value, "unit": event["unit"]})
            if reason is not None:
                excluded[reason] += 1
                details.append({"id": eid, "status": reason, "outcome": None})
        n = len(scores)
        counts["scored"] = n
        bucketed = [[] for _ in range(bins)]
        for p, y in scores:
            bucketed[min(int(p * bins), bins - 1)].append((p, y))
        reliability = []
        for i, bucket in enumerate(bucketed):
            size = len(bucket)
            ready = size >= min_bin_samples
            reliability.append({"lower": i/bins, "upper": (i+1)/bins, "upper_inclusive": i == bins-1,
                                "n": size, "mean_probability": sum(p for p,y in bucket)/size if ready else None,
                                "observed_rate": sum(y for p,y in bucket)/size if ready else None,
                                "sample_gate": "sufficient" if ready else "insufficient"})
        return {"schema_version": VERSION, "status": "ok", "d": d, "denominators": counts, "exclusions": excluded,
                "brier": sum((p-y)**2 for p,y in scores)/n if n >= min_samples else None,
                "sample_gate": "sufficient" if n >= min_samples else "insufficient", "bins": reliability,
                "min_samples": min_samples, "min_bin_samples": min_bin_samples, "details": details,
                "score_scope": "prospective" if modes == {"prospective"} else "controlled_test" if modes == {"controlled_test"} else "mixed_or_empty",
                "provenance_status": "timestamps_and_hashes_checked_independent_attestation_pending",
                "improvement_conclusion": None}
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        return _fail(d, [exc])


def append_observation(root: Path, d: str, record: dict) -> dict:
    """Fail-fast exclusive append, idempotent on run_id/stage; conflicting reuse fails."""
    lock = None
    try:
        _date(d)
        required = {"schema_version", "d", "run_id", "stage", "started", "ended", "duration", "status",
                    "input_hash", "provider", "model", "tokens", "cost", "retries"}
        if not isinstance(record, dict) or not required <= record.keys() or record["schema_version"] != VERSION or record["d"] != d:
            raise ValueError("observation schema/date mismatch")
        if any(not isinstance(record[k], str) or not record[k] for k in ("run_id", "stage", "status")):
            raise ValueError("observation run_id/stage/status required")
        measured = _duration(record)
        if measured is None or not _number(record["duration"]) or not math.isclose(measured, record["duration"], abs_tol=0.000001):
            raise ValueError("duration must come from actual started/ended timestamps")
        if record["input_hash"] is not None and not re.fullmatch("[a-f0-9]{64}", record["input_hash"]):
            raise ValueError("invalid input_hash")
        if type(record["retries"]) is not int or record["retries"] < 0:
            raise ValueError("invalid retries")
        tokens = record["tokens"]
        if tokens is not None and not isinstance(tokens, dict):
            raise ValueError("invalid tokens")
        _usage({"usage": {**(tokens or {}), "cost": record["cost"]}})
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        lock_path = root / ".observability.lock"
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        lock = lock_path
        os.close(fd)
        path = root / "observability.jsonl"
        rows = []
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        for previous in rows:
            if previous["run_id"] == record["run_id"]:
                if previous["d"] != d or previous["input_hash"] != record["input_hash"]:
                    raise ValueError("run_id reused with different date/input_hash")
                if previous["stage"] == record["stage"]:
                    if previous != record:
                        raise ValueError("conflicting duplicate observation")
                    return {"schema_version": VERSION, "status": "ok", "d": d, "appended": False}
        with path.open("ab") as f:
            f.write((json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        return {"schema_version": VERSION, "status": "ok", "d": d, "appended": True}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return _fail(d, [exc])
    finally:
        if lock is not None:
            lock.unlink()


def _record(d, run_id, stage, started, ended, status, digest, provider=None, model=None, usage=None):
    usage = usage or {}
    tokens = {k: usage.get(k) for k in ("input_tokens", "output_tokens")}
    return {"schema_version": VERSION, "d": d, "run_id": run_id, "stage": stage,
            "started": started, "ended": ended, "duration": (_stamp(ended)-_stamp(started)).total_seconds(),
            "status": status, "input_hash": digest, "provider": provider, "model": model,
            "tokens": tokens if any(v is not None for v in tokens.values()) else None,
            "cost": usage.get("cost"), "currency": usage.get("currency"), "retries": 0}


def _can_observe(out):
    return not Path(out).exists() or (Path(out).is_dir() and not any(Path(out).iterdir()))


def freeze_case(root: Path, d: str, out: Path) -> dict:
    started = _now()
    fresh = _can_observe(out)
    result = _freeze_case(root, d, out)
    ended = _now()
    try:
        _date(d)
    except ValueError:
        return result
    if fresh:
        logged = append_observation(Path(out), d, _record(d, uuid.uuid4().hex, "freeze", started, ended,
                                                         result["status"], result.get("case_hash")))
        if logged["status"] == "fail":
            return logged
    return result


def evaluate_outputs(case_path: Path, outputs: list[Path], out: Path) -> dict:
    started = _now()
    fresh = _can_observe(out)
    result = _evaluate_outputs(case_path, outputs, out)
    ended = _now()
    d = result.get("d")
    if fresh and d is not None:
        digest = _load(Path(out) / "blind_review.json")["case_hash"] if "report_path" in result else None
        logged = append_observation(Path(out), d, _record(d, uuid.uuid4().hex, "compare", started,
                                                        ended, result["status"], digest))
        if logged["status"] == "fail":
            return logged
    return result



def _execute(command, request, root, timeout):
    # On Windows communicate(input=large_json) can block while writing stdin
    # before its timeout starts. File-backed stdin preserves the JSON protocol.
    options = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with tempfile.TemporaryFile(dir=root, prefix="review-eval-stdin-") as request_file:
        request_file.write(request)
        request_file.seek(0)
        process = subprocess.Popen(command, stdin=request_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   cwd=root, shell=False, **options)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                cleanup = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                         capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
                if cleanup.returncode != 0 and process.poll() is None:
                    process.kill()
                    raise ValueError("runner timeout; process-tree cleanup failed")
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                raise ValueError("runner timeout; child pipes remain open after tree cleanup") from None
            raise subprocess.TimeoutExpired(command, timeout) from None
        finally:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)


def run_model(root: Path, d: str, case_path: Path, out: Path, command: list[str] | None = None, *,
              allow_execution: bool = False, provider: str | None = None, model: str | None = None,
              timeout: float = 60, run_id: str | None = None, kind: str = "model_output") -> dict:
    """Explicit argv plugin: stdin request JSON -> stdout response JSON. Offline by default.

    response = {output: <frozen output schema>, usage: {input_tokens, output_tokens, cost, currency}}
    Missing usage stays null. No price estimation, automatic retries, or credential dependency.
    """
    verified = verify_case(case_path)
    if verified["status"] == "fail":
        return verified
    if d != verified["d"]:
        return _fail(d, ["case date mismatch"])
    lock = None
    try:
        root, out = Path(root).resolve(), Path(out).resolve()
        if not root.is_dir() or not out.is_relative_to(root):
            raise ValueError("runner out must be within explicit execution root")
        if not _number(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive")
        if kind not in ("model_output", "controlled_test_output"):
            raise ValueError("runner kind must distinguish model and controlled output")
        if command is not None and (not isinstance(command, list) or not command or any(not isinstance(v,str) or not v for v in command)):
            raise ValueError("command must be an explicit nonempty list of strings")
        if allow_execution and command is None:
            raise ValueError("explicit command required for execution")
        run_id = run_id or uuid.uuid4().hex
        request_hash = _hash(_bytes({"d":d,"case_hash":verified["case_hash"],"command":command,"provider":provider,"model":model,
                                     "execute":allow_execution,"timeout":timeout,"run_id":run_id,"kind":kind}))
        out.mkdir(parents=True, exist_ok=True)
        lock_path = out / ".runner.lock"
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        lock = lock_path
        os.close(fd)
        if (out / "result.json").exists():
            old = _load(out / "result.json")
            if old.get("request_hash") != request_hash:
                raise ValueError("runner directory belongs to a different request; use a new out")
            if old.get("output_sha256") is not None and _hash((out / "output.json").read_bytes()) != old["output_sha256"]:
                raise ValueError("cached output hash mismatch")
            return {**old, "cached": True}
        if any(p.name != ".runner.lock" for p in out.iterdir()):
            raise ValueError("runner out contains incomplete/other artifacts; use a new out")
        started = _now()
        usage = _usage({})
        status, errors, body = "offline", [], None
        if allow_execution:
            status = "ok"
            try:
                request = {"schema_version": VERSION, "d": d, "case_hash": verified["case_hash"],
                           "case": verified["case"], "prompt": (Path(case_path).parent / "prompt.txt").read_text(encoding="utf-8")}
                process = _execute(command, _bytes(request), root, timeout)
                private = out / "private"
                private.mkdir(exist_ok=True)
                (private / "stdout.txt").write_bytes(process.stdout)
                (private / "stderr.txt").write_bytes(process.stderr)
                if process.returncode != 0:
                    raise ValueError("runner exited with code " + str(process.returncode))
                response = _load(private / "stdout.txt")
                if not isinstance(response, dict):
                    raise ValueError("runner response must be JSON object")
                usage = _usage(response)
                body = response.get("output", response)
                errors = _structure(body, verified, [provider, model])
                if errors:
                    status = "fail"
            except subprocess.TimeoutExpired:
                status, errors = "timeout", ["runner timeout"]
            except (OSError, ValueError, KeyError, TypeError) as exc:
                status, errors = "fail", [str(exc)]
        ended = _now()
        if body is not None:
            envelope = {"schema_version": VERSION, "d": d, "run_id": run_id, "kind": kind,
                        "provider": provider, "model": model, "started": started, "ended": ended,
                        "usage": usage, "output": body}
            _save(out / "output.json", envelope)
        row = _record(d, run_id, "model", started, ended, status, verified["case_hash"], provider, model, usage)
        logged = append_observation(out, d, row)
        if logged["status"] == "fail":
            return logged
        result = _fail(d, errors) if status in ("fail", "timeout") else {"schema_version":VERSION,"status":status,"d":d}
        result.update(run_id=run_id, request_hash=request_hash, output_path=str(out/"output.json") if body is not None else None,
                      output_sha256=_hash((out/"output.json").read_bytes()) if body is not None else None, cached=False)
        _save(out / "result.json", result)
        return result
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return _fail(d, [exc])
    finally:
        if lock is not None:
            lock.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description="P3 offline frozen-case evaluation; no implicit model calls")
    sub = parser.add_subparsers(dest="action", required=True)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("d")
    freeze.add_argument("--root", type=Path, required=True)
    freeze.add_argument("--out", type=Path, required=True)
    compare = sub.add_parser("compare")
    compare.add_argument("--case", type=Path, required=True)
    compare.add_argument("--outputs", type=Path, nargs="+", required=True)
    compare.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--case", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("d")
    run.add_argument("--root", type=Path, required=True)
    run.add_argument("--case", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--execute", action="store_true")
    run.add_argument("--provider")
    run.add_argument("--model")
    run.add_argument("--run-id")
    run.add_argument("--timeout", type=float, default=60)
    run.add_argument("--kind", choices=["model_output","controlled_test_output"], default="model_output")
    run.add_argument("--command", nargs=argparse.REMAINDER)
    calibrate = sub.add_parser("calibrate")
    calibrate.add_argument("d")
    calibrate.add_argument("--root", type=Path, required=True)
    for flag in ("registrations", "forecasts", "labels", "out"):
        calibrate.add_argument("--"+flag, type=Path, required=True)
    calibrate.add_argument("--min-samples", type=int, default=30)
    calibrate.add_argument("--min-bin-samples", type=int, default=10)
    calibrate.add_argument("--bins", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        if args.action == "freeze":
            result = freeze_case(args.root, args.d, args.out)
        elif args.action == "compare":
            result = evaluate_outputs(args.case, args.outputs, args.out)
        elif args.action == "verify":
            result = verify_case(args.case)
            result.pop("case", None)
        elif args.action == "run":
            result = run_model(args.root, args.d, args.case, args.out, args.command, allow_execution=args.execute,
                               provider=args.provider, model=args.model, timeout=args.timeout, run_id=args.run_id, kind=args.kind)
        else:
            started = _now()
            result = calibration_report(args.root, args.d, _load(args.registrations), _load(args.forecasts), _load(args.labels),
                                        min_samples=args.min_samples, min_bin_samples=args.min_bin_samples, bins=args.bins)
            _save(args.out / "calibration.json", result)
            digest = _hash(args.registrations.read_bytes()+args.forecasts.read_bytes()+args.labels.read_bytes())
            logged = append_observation(args.out, args.d, _record(args.d, uuid.uuid4().hex, "calibrate", started, _now(), result["status"], digest))
            if logged["status"] == "fail":
                result = logged
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = _fail(getattr(args,"d",None), [exc])
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
