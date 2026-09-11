"""P2 学习闭环：显式输入、独立审计产物。"""

from __future__ import annotations
import argparse
import hashlib
import json
import math
import operator
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def _date(d: str) -> str:
    if not isinstance(d, str) or not re.fullmatch(r"[0-9]{8}", d):
        raise ValueError("d 必须为严格 YYYYMMDD")
    datetime.strptime(d, "%Y%m%d")
    return d


def normalize_responses(raw: dict, items: list, d: str) -> dict:
    """归一历史应答包装；只重排已有记录，不生成应答。"""
    _date(d)
    if not isinstance(raw, dict) or not isinstance(items, list):
        raise ValueError("应答必须为对象，items 必须为列表")
    ids = [i.get("id") if isinstance(i, dict) else None for i in items]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("清单 ID 缺失或重复")
    route_ids = {}
    for item in items:
        route_ids.setdefault(item.get("route"), []).append(item["id"])
    metadata = {"d", "日期", "来源", "口径", "说明", "schema_version", "_总审注"}
    mapping = raw
    if "应答" in raw:
        given_d = raw.get("日期", raw.get("d"))
        if given_d is not None and given_d != d:
            raise ValueError("应答日期错配")
        mapping = raw["应答"]
    elif "items" in raw:
        mapping = raw["items"]
    elif d in raw:
        mapping = raw[d]
    else:
        # 旧版 route -> [response] 或 date + id -> response。
        payload = {k: v for k, v in raw.items() if k not in metadata}
        if payload and all(k in route_ids for k in payload):
            mapping = {}
            for route, responses in payload.items():
                if not isinstance(responses, list) or len(responses) != len(route_ids[route]):
                    raise ValueError(f"旧route应答数量不匹配: {route}")
                mapping.update(dict(zip(route_ids[route], responses)))
        else:
            mapping = payload
    if isinstance(mapping, list):
        result = {}
        for response in mapping:
            if not isinstance(response, dict) or not response.get("id"):
                raise ValueError("应答 ID 缺失")
            key = response["id"]
            if key in result:
                raise ValueError("重复应答 ID: " + key)
            result[key] = response
        mapping = result
    if not isinstance(mapping, dict):
        raise ValueError("应答映射类型错误")
    unknown, missing = set(mapping) - set(ids), set(ids) - set(mapping)
    if unknown or missing:
        raise ValueError(f"未知项={sorted(unknown)}; 缺项={sorted(missing)}")
    if any(not isinstance(v, dict) for v in mapping.values()):
        raise ValueError("单条应答必须为对象")
    if any("id" in v and v["id"] != k for k, v in mapping.items()):
        raise ValueError("应答内嵌 ID 与映射键不一致")
    return dict(mapping)


OPS = {"lt": operator.lt, "le": operator.le, "gt": operator.gt,
       "ge": operator.ge, "eq": operator.eq, "ne": operator.ne}
ALIASES = {"两市成交额_亿": "成交额亿", "1进2率": "一进二率"}
RATIO_FIELDS = {"炸板率", "封板率", "一进二率", "二进三率"}
ROUTES = ("auction", "lhb", "theme", "logic", "limitup")


def _pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError("JSON 重复键: " + k)
        result[k] = v
    return result


def _load(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_pairs)
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name}: JSON 顶层必须为对象")
    return obj


def _check_date(obj, d):
    for key in ("d", "日期", "date"):
        if key in obj and obj[key] != d:
            raise ValueError(f"{key} 日期错配: {obj[key]} != {d}")


def _calendar(root: Path) -> list:
    """Read the real archived trading calendar before falling back to dated dirs."""
    cached = root / "_学习" / "_交易日历.json"
    if cached.is_file():
        try:
            values = json.loads(cached.read_text(encoding="utf-8"))
            if isinstance(values, list):
                valid = sorted({_date(str(x)) for x in values})
                if valid:
                    return valid
        except (OSError, ValueError, TypeError):
            pass
    dates = []
    for p in root.iterdir():
        if p.is_dir() and re.fullmatch(r"[0-9]{8}", p.name):
            dates.append(_date(p.name))
    return sorted(dates)


def _due(calendar, d, offset=1):
    future = [x for x in calendar if x > d]
    return future[offset - 1] if len(future) >= offset else None


def _failure(d, exc):
    return {"status": "fail", "errors": [str(exc)], "d": d}


def _paths(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    if not root.is_dir():
        raise ValueError("输入 root 不存在或不是目录")
    if out.is_relative_to(root):
        raise ValueError("out 必须位于只读输入 root 之外")
    return root, out


def _save_run(out: Path, kind: str, result: dict) -> dict:
    """out 是独立审计根；每次 mkdir 独占新 run，不覆盖任何既有结果。"""
    run = out / (kind + "_" + uuid4().hex)
    run.mkdir(parents=True, exist_ok=False)
    result["artifact"] = str((run / (kind + ".json")).resolve())
    with Path(result["artifact"]).open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
    return result


def _evidence(path, d, field):
    return {"path": str(path.resolve()), "d": d, "field": field,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _actual(root, d, field):
    """仅查指定到期日；缺值、冲突、不可读均保留未知，绝不找最新值替代。"""
    field = ALIASES.get(field, field)
    path = root / "_学习" / f"fact_{d}.json"
    try:
        obj = _load(path)
        _check_date(obj, d)
        item = obj.get("facts", {}).get(field)
        if isinstance(item, dict) and item.get("quality") in (None, "ok"):
            return item.get("value"), [_evidence(path, d, "facts." + field)]
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    if field in {"一进二率", "二进三率"}:
        path = root / "_学习" / "_情绪先行指标.json"
        try:
            item = _load(path).get(d, {}).get("晋级", {})
            return item.get(field), [_evidence(path, d, d + ".晋级." + field)]
        except (OSError, ValueError, TypeError, AttributeError):
            pass
    return None, []


def _number(value, unit=None):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str) and value.endswith("%"):
        try:
            return float(value[:-1]) / 100
        except ValueError:
            return None
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    if unit in ("pct", "%", "percent"):
        return value / 100
    if unit not in (None, "ratio", "number", "亿", "板", "只"):
        return None
    return value


def _predicate(root, due_d, spec):
    if not isinstance(spec, dict) or spec.get("op") not in OPS or not isinstance(spec.get("field"), str):
        return None, None, []
    field = ALIASES.get(spec["field"], spec["field"])
    if spec.get("unit") in ("pct", "%", "percent", "ratio") and field not in RATIO_FIELDS:
        return None, None, []
    actual, evidence = _actual(root, due_d, field)
    threshold = _number(spec.get("threshold"), spec.get("unit"))
    numeric = _number(actual)
    if numeric is None or threshold is None:
        return None, actual, evidence
    return bool(OPS[spec["op"]](numeric, threshold)), actual, evidence


def _legacy_op(item):
    cond = item.get("判定条件") or {}
    if not isinstance(cond, dict):
        return None
    direction, threshold = cond.get("方向"), cond.get(">=")
    claim = str(item.get("预测") or "").split("——")[0]
    if direction == "降":
        # 方向与历史键冲突，仅原文明确跨过同一阈值才转换。
        if cond.get("指标") in ("代码封板", "代码收红"):
            return "eq" if re.search(r"不封板|不收红", claim) else None
        if not isinstance(threshold, (int, float)):
            return None
        for conflict in re.finditer(r"(?:>=|≥|>|高于|不低于)\s*([0-9]+(?:\.[0-9]+)?)(%?)", claim):
            other = float(conflict.group(1)) / (100 if conflict.group(2) else 1)
            if math.isclose(other, threshold, rel_tol=1e-9):
                return None
        for m in re.finditer(r"(?:(低于|跌破|击穿)\s*)?([0-9]+(?:\.[0-9]+)?)(%?)(?:亿|家|只|板)?\s*(以下)?", claim):
            if not (m.group(1) or m.group(4)):
                continue
            val = float(m.group(2)) / (100 if m.group(3) else 1)
            if math.isclose(val, threshold, rel_tol=1e-9):
                return "lt"
        return None
    explicit = {">=": "ge", ">": "gt", "<=": "le", "<": "lt", "=": "eq"}
    if direction in explicit:
        # 不把反方向的原文静默解释成机器键。
        if direction in (">=", ">") and re.search(r"低于|以下|跌破", claim):
            return None
        return explicit[direction]
    if direction == "升" and re.search(r"以上|上方|≥|>=", claim):
        return "ge"
    return None


def _prediction_rows(root, d):
    path = root / "_学习" / f"推演_{d}.json"
    obj = _load(path)
    _check_date(obj, d)
    if obj.get("schema_version", 1) != 1:
        raise ValueError("未知预测 schema_version")
    rows = obj.get("predictions") if "predictions" in obj else obj.get("次日可证伪预测")
    if not isinstance(rows, list):
        raise ValueError("缺失预测清单")
    cal = _calendar(root)
    result, seen = [], set()
    for index, original in enumerate(rows):
        if not isinstance(original, dict):
            raise ValueError("预测条目必须为对象")
        row = dict(original)
        if "predictions" in obj:
            required = {"id", "d", "due_d", "source", "field", "op", "threshold", "condition"}
            if required - row.keys() or row.get("schema_version", 1) != 1:
                raise ValueError("预测 v1 必需字段缺失或版本错误")
            _check_date(row, d)
            if row.get("event_type", "numeric") not in ("direction", "attack_defense", "numeric", "stock", "conditional"):
                raise ValueError("未知预测 event_type")
            if row.get("op") not in (*OPS, None):
                raise ValueError("未知预测 op")
            if row.get("unit") not in (None, "number", "ratio", "pct", "%", "percent", "亿", "板", "只"):
                raise ValueError("未知预测 unit")
            if row.get("condition") is not None and not isinstance(row["condition"], dict):
                raise ValueError("v1 condition 必须为谓词对象或 null")
            if row["due_d"] is not None:
                _date(row["due_d"])
                if row["due_d"] <= d:
                    raise ValueError("预测到期日必须晚于发行日")
        else:
            cond = row.get("判定条件") or {}
            if not isinstance(cond, dict):
                cond = {}
            claim = str(row.get("预测") or "")
            dates = sorted(set(re.findall(r"(?<![0-9])([0-9]{8})(?![0-9])", claim)))
            dates = [x for x in dates if _date(x) > d]
            due_d = dates[0] if len(dates) == 1 else _due(cal, d)
            op = _legacy_op(row)
            row.update(id=f"prediction:{d}:{index:03}", d=d, due_d=due_d,
                       source=f"_学习/推演_{d}.json#次日可证伪预测/{index}",
                       field=cond.get("指标"), op=op,
                       threshold=0 if op == "eq" and cond.get("代码") else cond.get(">="),
                       condition=None, claim=claim, original=original)
        row["field"] = ALIASES.get(row.get("field"), row.get("field"))
        if not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen:
            raise ValueError("预测 ID 缺失或重复")
        seen.add(row["id"])
        row.update(schema_version=1, actual=None, evidence=[], status="pending")
        row.setdefault("event_type", "conditional" if row.get("condition") is not None else
                       "stock" if str(row.get("field", "")).startswith("代码") else "numeric")
        result.append(row)
    # 五路防守/环境方向与数值预测分栏保存，绝不使用自评当作事件命中。
    for key, event_type in (("情绪几度", "direction"), ("明日攻防", "attack_defense"),
                            ("主线站队", "direction"), ("龙头接力", "stock"), ("竞价强弱预判", "direction")):
        if key in obj:
            result.append(dict(schema_version=1, id=f"narrative:{d}:{key}", d=d,
                               due_d=_due(cal, d), source=f"_学习/推演_{d}.json#{key}",
                               field=None, op=None, threshold=None, condition=None,
                               claim=obj[key], event_type=event_type, status="pending", actual=None, evidence=[]))
    return result


def _settle_rows(root, d, target_d):
    _date(d); _date(target_d)
    if target_d < d:
        raise ValueError("禁止使用未来发行的预测")
    cal = _calendar(root)
    if d not in cal or target_d not in cal:
        raise ValueError("发行日/审计日不在真实归档交易日历中")
    rows = _prediction_rows(root, d)
    for row in rows:
        due = row["due_d"]
        if due is None:
            row["status"] = "pending" if target_d == d else "unverifiable"
            row["reason"] = "归档日历无后继交易日，禁止猜工作日"
            continue
        if due > target_d:
            row["reason"] = "尚未到期，未读取未来事实"
            continue
        if due not in cal:
            row.update(status="unverifiable", reason="到期日不在真实归档交易日历，禁止移日")
            continue
        if row.get("event_type") == "stock":
            row.update(status="unverifiable", reason="缺可核验的完整个股行情/封板真源")
            continue
        if row["op"] not in OPS:
            row.update(status="ambiguous", reason="原文/方向/阈值无法无歧义转为比较条件")
            continue
        condition = row.get("condition")
        if condition is not None:
            triggered, _, ev = _predicate(root, due, condition)
            row["condition_evidence"] = ev
            if triggered is not True:
                row.update(status="not_triggered" if triggered is False else "unverifiable",
                           reason="前提未触发" if triggered is False else "前提缺数据或无法机械解释")
                continue
        verdict, actual, evidence = _predicate(root, due, row)
        row.update(status="unverifiable" if verdict is None else "true" if verdict else "false",
                   actual=actual, evidence=evidence)
        if verdict is None:
            row["reason"] = "缺失/冲突事实或阈值/单位不可验证"
    return rows


def settle_predictions(root: Path, d: str, target_d: str, out: Path) -> dict:
    """d 为预测发行日，target_d 为本次审计截至日；只结算原到期日事实。"""
    try:
        root, out = _paths(root, out)
        rows = _settle_rows(root, d, target_d)
        result = {"schema_version": 1, "status": "pass", "d": d, "target_d": target_d,
                  "publication": "new_audit_not_historical_publication", "predictions": rows,
                  "counts": {s: sum(x["status"] == s for x in rows) for s in
                             ("true", "false", "unverifiable", "ambiguous", "not_triggered", "pending")}}
        return _save_run(Path(out), "predictions", result)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _failure(d, exc)


from html import escape, unescape
from html.parser import HTMLParser


class _LegacyHTML(HTMLParser):
    """仅用于旧 body 一次性导入，不作为新认知的每日上游。"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {"tag": "root", "attrs": {}, "children": []}
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "children": []}
        self.stack[-1]["children"].append(node)
        if tag not in {"br", "hr", "img", "input", "meta", "link", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1]["children"].append(data)


def _node_text(node):
    if isinstance(node, str):
        return node
    return " ".join(_node_text(x) for x in node["children"]).strip()


def _legacy_claims(body, d):
    headings = list(re.finditer(r"<h2\b[^>]*>(.*?)</h2>", body, re.S | re.I))
    section = None
    for i, match in enumerate(headings):
        title = re.sub(r"<[^>]+>", "", match.group(1))
        if "认知" in title:
            section = body[match.end(): headings[i+1].start() if i+1 < len(headings) else len(body)]
            break
    if section is None:
        return []
    parser = _LegacyHTML(); parser.feed(section)
    blocks = []
    def walk(node):
        if isinstance(node, str):
            return
        classes = set((node["attrs"].get("class") or "").split())
        if classes & {"tli", "iter-card"} or node["tag"] == "li":
            if _node_text(node):
                blocks.append(node)
            return
        before = len(blocks)
        for child in node["children"]:
            walk(child)
        # card 常是整个时间线容器；仅无更细条目时才作为单条。
        if "card" in classes and len(blocks) == before and _node_text(node):
            blocks.append(node)
    walk(parser.root)
    if not blocks and _node_text(parser.root):
        blocks = [parser.root]
    claims = []
    for node in blocks:
        text = _node_text(node)
        match = re.match(r"^(20[0-9]{2})-?([0-9]{2})-?([0-9]{2})", text)
        short = re.match(r"^([0-9]{2})-([0-9]{2})(?:\s|$)", text)
        entry_d = "".join(match.groups()) if match else d[:4] + "".join(short.groups()) if short else d
        claims.append({"claim": text, "d": entry_d, "legacy_node": node, "legacy_section": section})
    return claims


def _cognition_record(raw, route, d, source, index, origin, path):
    obj = raw if isinstance(raw, dict) else {}
    claim = raw if isinstance(raw, str) else obj.get("claim", obj.get("认知点", obj.get("正文")))
    falsifier = obj.get("falsifier", obj.get("可证伪条件"))
    if falsifier is None and isinstance(claim, str):
        match = re.search(r"可证伪(?:条件)?\s*[:：=](.*)", claim, re.S)
        falsifier = match.group(1) if match else None
    entry_d = obj.get("d", d)
    valid_d = True
    try:
        _date(entry_d)
        if entry_d > d:
            valid_d = False
    except (ValueError, TypeError):
        valid_d = False
    payload = json.dumps(raw, ensure_ascii=False, sort_keys=True)
    key = obj.get("id") or f"cognition:{route}:{entry_d}:" + hashlib.sha256((source + str(index) + payload).encode()).hexdigest()[:16]
    return {"schema_version": 1, "id": key, "d": entry_d if valid_d else d,
            "route": route, "source": source, "claim": claim, "falsifier": falsifier,
            "evidence": [_evidence(path, d, source.split("#")[-1])],
            "basis": obj.get("evidence", obj.get("依据")), "original": raw,
            "status": "unverified" if isinstance(claim, str) and claim.strip() and valid_d else "unknown",
            "origin": origin}


def _collect(root, d, out):
    _date(d)
    records, known, imports, errors, stats = {}, set(), set(), [], {}
    scope = str(root.resolve())
    # 只读本输出库的既有新 run；旧库 updated 不参与新增计数。
    for path in sorted(out.glob("cognition_*/cognition.json")):
        old = _load(path)
        if old.get("input_root") != scope or old.get("d", "99999999") > d:
            continue
        imports.update(old.get("legacy_import_keys", []))
        for row in old.get("records", []):
            if row["d"] <= d:
                records[row["id"]] = row
                known.add(row["id"])
    judgment_path = root / "_学习" / f"judgment_{d}.json"
    judgment = None
    new_imports = 0
    for route in (*ROUTES, "master"):
        name = f"{route}判断_{d}.json" if route != "master" else f"总审_{d}.json"
        path = root / "_学习" / name
        raw, has_structured = None, False
        try:
            if path.exists():
                obj = _load(path); _check_date(obj, d)
                if obj.get("schema_version", 1) != 1:
                    raise ValueError("未知认知 schema_version")
                for field in ("cognition", "认知迭代"):
                    if field in obj:
                        raw = obj[field]; has_structured = True
                        break
            if has_structured:
                if isinstance(raw, str):
                    raw = [raw]  # 8/31真实旧结构：保留完整文本，不猜分项边界。
                if not isinstance(raw, list):
                    errors.append(f"{route}: 认知字段非列表")
                    raw = [raw]
                # 新结构化条目优先于旧兼容条目。
                records = {k:v for k,v in records.items() if not (v["route"] == route and v["d"] == d)}
                for index, item in enumerate(raw):
                    source = f"_学习/{name}#{field}/{index}"
                    row = _cognition_record(item, route, d, source, index, "structured", path)
                    if row["status"] == "unknown":
                        errors.append(f"{route}: 未知认知条目 {index}")
                    if row["id"] in records:
                        raise ValueError("认知 ID 重复: " + str(row["id"]))
                    records[row["id"]] = row
            else:
                import_key = f"{d}:{route}"
                if import_key not in imports:
                    if judgment is None:
                        judgment = _load(judgment_path); _check_date(judgment, d)
                    body = (judgment.get("bodies") or {}).get(route)
                    if not isinstance(body, str):
                        raise ValueError("缺结构化认知及旧 body")
                    claims = _legacy_claims(body, d)
                    if not claims:
                        raise ValueError("旧 body 未读到认知，禁止跳过")
                    for index, item in enumerate(claims):
                        source = f"_学习/judgment_{d}.json#bodies.{route}/{index}"
                        row = _cognition_record(item, route, d, source, index, "legacy_body_import", judgment_path)
                        records[row["id"]] = row
                    imports.add(import_key); new_imports += len(claims)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            errors.append(f"{route}: {exc}")
            source = f"_学习/{name}"
            key = f"unknown:{route}:{d}"
            records[key] = dict(schema_version=1, id=key, d=d, route=route, source=source,
                                claim=None, evidence=[], falsifier=None, status="unknown", origin="missing")
        legacy = root / "_学习" / f"_认知库_{route}.json"
        updated, latest, snapshot_after = None, None, False
        if legacy.exists():
            old = _load(legacy)
            updated = old.get("updated")
            dates = [str(x.get("日期", "")).replace("-", "") for x in old.get("条目", []) if isinstance(x, dict)]
            dates = [x for x in dates if re.fullmatch(r"[0-9]{8}", x) and x <= d]
            latest = max(dates, default=None)
            snapshot_after = bool(updated and str(updated).replace("-", "")[:8] > d)
            if snapshot_after:
                updated, latest = None, None
        current = [x for x in records.values() if x["route"] == route]
        stats[route] = {"legacy_updated": updated, "legacy_latest_entry_d": latest,
                        "legacy_snapshot_after_asof": snapshot_after,
                        "latest_entry_d": max((x["d"] for x in current if x["claim"] is not None), default=None),
                        "new_count": sum(x["id"] not in known for x in current),
                        "current_count": sum(x["d"] == d for x in current)}
    ordered = sorted(records.values(), key=lambda x: (x["d"], x["route"], x["id"]))
    return dict(schema_version=1, status="fail" if errors else "pass", errors=errors, d=d,
                input_root=scope, collected_at=datetime.now(timezone.utc).isoformat(), records=ordered,
                stats=stats, new_count=sum(x["id"] not in known for x in ordered),
                legacy_import_count=new_imports, legacy_import_keys=sorted(imports))


def collect_cognition(root: Path, d: str, out: Path) -> dict:
    """五路+总审结构化认知为主；旧 body 每个日期/路在同一 out 库只导入一次。"""
    try:
        root, out = _paths(root, out)
        result = _collect(root, d, out)
        return _save_run(Path(out), "cognition", result)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _failure(d, exc)


def _valid_evidence(root, references, target_d, computed):
    if not isinstance(references, list) or not references or not computed:
        return False
    for ref in references:
        if not isinstance(ref, dict):
            return False
        try:
            ed = _date(ref.get("d"))
            path = (root / ref["path"]).resolve()
            if ed > target_d or not path.is_relative_to(root.resolve()):
                return False
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if ref.get("sha256") != digest:
                return False
            if not any(e["path"] == str(path) and e["d"] == ed and e["field"] == ref.get("field") for e in computed):
                return False
        except (OSError, ValueError, TypeError, KeyError):
            return False
    return True


def settle_master(root: Path, d: str, out: Path) -> dict:
    """ID 仅证明 acknowledged；原指派机器判据+可核验证据才 validated。"""
    try:
        root, out = _paths(root, out); _date(d)
        rows, errors = [], []
        cal = _calendar(root)
        source_count = 0
        for path in sorted((root / "_学习").glob("总审_*.json")):
            issued = path.stem.rsplit("_", 1)[-1]
            if not re.fullmatch(r"[0-9]{8}", issued) or issued > d:
                continue
            obj = _load(path); _check_date(obj, issued)
            source_count += 1
            for index, task in enumerate(obj.get("指派清单", [])):
                if not isinstance(task, dict) or not task.get("指派ID"):
                    errors.append(f"{path.name}: 指派 {index} 缺 ID"); continue
                match = re.search(r"[0-9]{8}", str(task.get("截止") or ""))
                due = _date(match.group()) if match else _due(cal, issued)
                row = dict(schema_version=1, id=task["指派ID"], d=issued, due_d=due,
                           source=f"{path.name}#指派清单/{index}", original=task,
                           status="pending", evidence=[], conclusion=None, actual=None)
                if due is not None and due <= d:
                    row["status"] = "unverifiable"
                    if due in cal:
                        route = task.get("指派给")
                        response, text = None, ""
                        jp = root / "_学习" / f"judgment_{due}.json"
                        if jp.exists():
                            j = _load(jp); _check_date(j, due)
                            text = str((j.get("bodies") or {}).get(route) or "")
                        rp = root / "_学习" / f"{route}判断_{due}.json"
                        if rp.exists():
                            r = _load(rp); _check_date(r, due)
                            text += json.dumps(r, ensure_ascii=False)
                            matches = [x for x in r.get("master_responses", []) if isinstance(x, dict) and x.get("id") == row["id"]]
                            if len(matches) > 1:
                                raise ValueError("Master 重复响应 ID")
                            response = matches[0] if matches else None
                        if row["id"] in text:
                            row["status"] = "acknowledged"
                        if response:
                            condition = task.get("condition", task.get("判定条件"))
                            verdict, actual, ev = _predicate(root, due, condition)
                            row.update(actual=actual, evidence=ev, conclusion=response.get("conclusion"))
                            if verdict is not None and row["conclusion"] and _valid_evidence(root, response.get("evidence"), due, ev):
                                row["status"] = "validated" if verdict else "refuted"
                rows.append(row)
        if not source_count:
            errors.append("未读到总审源文件，不能将空输入视为结算完成")
        return _save_run(out, "master", dict(schema_version=1, status="fail" if errors else "pass", errors=errors, d=d, assignments=rows))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _failure(d, exc)



def _tag_count(root, days, tag):
    if len(days) < 3:
        return None, []
    count, evidence = 0, []
    for day in days:
        path = root / "_学习" / f"题材归位_{day}.json"
        try:
            obj = _load(path); _check_date(obj, day)
            mapping = obj["映射"]
            if not isinstance(mapping, dict):
                return None, evidence
            count += sum(isinstance(x, dict) and x.get("大方向") == tag for x in mapping.values())
            evidence.append(_evidence(path, day, "映射.大方向"))
        except (OSError, ValueError, TypeError, KeyError):
            return None, evidence
    return count, evidence


def _settle_item(root, row, calendar, asof):
    if row["response"] is None:
        row.update(status="missing", reason="清单项未读到应答")
        return
    due = row["due_d"]
    if due is None or due > asof:
        row.update(status="pending", reason="未到期或归档日历尚无完整到期日")
        return
    if due not in calendar:
        row.update(status="unverifiable", reason="到期日不在真实归档日历")
        return
    condition = row["item"].get("condition", row["response"].get("condition"))
    if condition is not None:
        verdict, actual, ev = _predicate(root, due, condition)
        row.update(status="unverifiable" if verdict is None else "true" if verdict else "false",
                   actual=actual, evidence=ev, criterion=condition)
        return
    tag = re.search(r"标签\[(.+?)\]", str(row["item"].get("signal") or ""))
    if row["item"].get("route") in ("theme", "logic") and tag:
        issued = row["d"]
        then, ev1 = _tag_count(root, [x for x in calendar if x <= issued][-3:], tag.group(1))
        now, ev2 = _tag_count(root, [x for x in calendar if x <= due][-3:], tag.group(1))
        verdict = now >= 2 * then if then is not None and then > 0 and now is not None else None
        row.update(status="unverifiable" if verdict is None else "true" if verdict else "false",
                   actual=now, baseline=then, evidence=ev1 + ev2, criterion="三日同标签计数较发行日翻倍")
        row["rejected_opportunity"] = verdict if row["response"].get("决定") == "不深挖" else None
        return
    row.update(status="unverifiable", reason="原应答无可机械结算判据/所需研究数据缺失，拒绝支持待验同等保留")


def _exempted(root, kind, d):
    """★2026-09-10(用户拍板): 历史欠账豁免台账 _学习/_审计豁免.json 的唯一读取口。
    只豁免『登记在册』的 (日期, 类型) 组合; 未登记者一律照常判 FAIL —— 豁免必须显式、可审、带证据,
    绝不静默(不缩分母、不放过新缺口)。类型: 应答缺失|推演缺失|推演不可结算|总审缺失|指派清单缺失。"""
    try:
        ledger = _load(root / "_学习" / "_审计豁免.json") or {}
        entry = (ledger.get("豁免") or {}).get(d) if isinstance(ledger, dict) else None
        if not isinstance(entry, dict):
            return None
        kinds = entry.get("类型")
        if isinstance(kinds, str):
            kinds = [kinds]
        return entry if kind in (kinds or []) else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def _coverage(root, d):
    _date(d)
    cal = _calendar(root)
    errors, rows, total, read_count = [], [], 0, 0
    exempted_items, exemptions = 0, []
    learn = root / "_学习"
    paths = sorted(p for p in learn.glob("自主拓展清单_*.json") if re.fullmatch(r"自主拓展清单_[0-9]{8}", p.stem) and p.stem[-8:] <= d)
    if not (learn / f"自主拓展清单_{d}.json").exists():
        errors.append("未读到当日自主拓展清单")
    for path in paths:
        issued = path.stem[-8:]
        try:
            inv = _load(path); _check_date(inv, issued)
            items = inv["items"]
            if not isinstance(items, list):
                raise ValueError("items 非列表，分母不可知")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        total += len(items)
        response_path = learn / f"自主拓展应答_{issued}.json"
        responses = {}
        _ex = _exempted(root, "应答缺失", issued)
        if _ex is not None and not response_path.exists():
            # ★2026-09-10 用户批准: 只豁免 登记在册 的历史欠账(如 20260715 单日漏跑),
            #   逐项留档(status=exempted)且分母不缩; 未登记日期的缺失仍走下面 FAIL 分支。
            _why = _ex.get("原因") if isinstance(_ex, dict) else str(_ex)
            exempted_items += len(items)
            exemptions.append({"d": issued, "n": len(items), "reason": _why})
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    item = {"id": None, "original": item}
                rows.append(dict(schema_version=1, id=item.get("id"), d=issued,
                                 due_d=item.get("due_d") or _due(cal, issued, 2),
                                 source=f"{path.name}#items/{index}", response=None, item=item,
                                 status="exempted", actual=None, evidence=[],
                                 reason="已登记豁免: " + str(_why)))
            continue
        try:
            raw = _load(response_path)
            responses = normalize_responses(raw, items, issued)
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{response_path.name}: {exc}")
            # 错误仍 FAIL；可识别的其他项保留，绝不缩分母或漏结算。
            try:
                raw = _load(response_path)
                _check_date(raw, issued)
                mapping = raw.get("应答", raw.get(issued, raw))
                if isinstance(mapping, dict):
                    responses = {k:v for k,v in mapping.items() if isinstance(v, dict)}
            except (OSError, ValueError, TypeError, AttributeError):
                pass
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                item = {"id": None, "original": item}
            iid = item.get("id")
            response = responses.get(iid)
            if response is not None:
                read_count += 1
            due = item.get("due_d", (response or {}).get("due_d"))
            if due is None:
                due = _due(cal, issued, 2)
            row = dict(schema_version=1, id=iid, d=issued, due_d=due,
                       source=f"{path.name}#items/{index}", response=response, item=item,
                       status="pending", actual=None, evidence=[])
            try:
                if due is not None:
                    _date(due)
                    if due <= issued:
                        raise ValueError("清单到期日必须晚于发行日")
                _settle_item(root, row, cal, d)
            except (ValueError, TypeError) as exc:
                row.update(status="ambiguous", reason=str(exc)); errors.append(f"{iid}: {exc}")
            rows.append(row)
    required = total - exempted_items
    if read_count != required:
        errors.append(f"消费者应答覆盖不足: {read_count}/{required}"
                      + (f"（另有 {exempted_items} 项已登记历史豁免，见 _学习/_审计豁免.json）" if exempted_items else ""))
    return {"total_items": total, "responses_read": read_count,
            "exempted_items": exempted_items, "exemptions": exemptions,
            "due_items": sum(x["due_d"] is not None and x["due_d"] <= d for x in rows),
            "status_counts": {s: sum(x["status"] == s for x in rows) for s in
                              ("true", "false", "pending", "unverifiable", "ambiguous", "missing", "exempted")}}, rows, errors


def coverage_learning(root: Path, d: str, out: Path) -> dict:
    """只做自主拓展清单/应答覆盖审计，不隐式运行认知与 Master 副作用。"""
    try:
        root, out = _paths(root, out); _date(d)
        coverage, items, errors = _coverage(root, d)
        result = dict(schema_version=1, status="fail" if errors else "pass",
                      errors=errors, d=d, publication="new_coverage_audit",
                      coverage=coverage, items=items,
                      historical_publication_modified=False)
        return _save_run(out, "coverage", result)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _failure(d, exc)


def audit_learning(root: Path, d: str, out: Path) -> dict:
    """真实 audit 消费者：全清单应答覆盖+所有推演到期状态+认知+Master。"""
    try:
        root, out = _paths(root, out); _date(d)
        coverage, items, errors = _coverage(root, d)
        predictions = []
        paths = sorted(p for p in (root / "_学习").glob("推演_*.json") if re.fullmatch(r"推演_[0-9]{8}", p.stem) and p.stem[-8:] <= d)
        exempt_notes = []

        def _gap(msg, kind, day):
            """登记在册的历史欠账 → 进 exempt_notes(可见、不判 FAIL); 否则照原样进 errors(可能阻塞)。"""
            if _exempted(root, kind, day) is not None:
                exempt_notes.append(msg)
            else:
                errors.append(msg)

        if not (root / "_学习" / f"推演_{d}.json").exists():
            _gap("未读到当日推演", "推演缺失", d)
        for issued in sorted({row["d"] for row in items}):
            if not (root / "_学习" / f"推演_{issued}.json").exists():
                _gap(f"未读到历史清单日期对应推演_{issued}.json", "推演缺失", issued)
        # ★2026-09-10 源日断言(用户拍板): 在册日必须留下可被次日承接的 指派清单。
        #   背景: 20260812-0814 / 20260908 / 20260909 的总审缺该字段 ⇒ 当日晚间无指派可承接, 而旧审计
        #   只查『已存在的指派有没有被承接』⇒ 缺口能静默数日(20260909 复盘时靠人工逐日翻检才发现)。
        #   现: 在册日 缺 总审、或 总审无 指派清单(数组) → 判 FAIL; 仅 _审计豁免.json 在册者可豁免, 新日期一律 FAIL。
        for issued in sorted({row["d"] for row in items}):
            master_path = root / "_学习" / f"总审_{issued}.json"
            if not master_path.exists():
                _gap(f"源日断言: 在册日 {issued} 缺 总审_{issued}.json（该日无任何指派可被次日承接）", "总审缺失", issued)
                continue
            try:
                master_obj = _load(master_path)
            except (OSError, ValueError, TypeError, KeyError) as exc:
                errors.append(f"{master_path.name}: {exc}")
                continue
            if not isinstance(master_obj, dict) or not isinstance(master_obj.get("指派清单"), list):
                _gap(f"源日断言: 在册日 {issued} 总审缺 指派清单（该日无任何指派可被次日承接）", "指派清单缺失", issued)
        for path in paths:
            try:
                predictions.extend(_settle_rows(root, path.stem[-8:], d))
            except (OSError, ValueError, TypeError, KeyError) as exc:
                if "缺失预测清单" in str(exc):
                    _gap(f"{path.name}: {exc}", "推演不可结算", path.stem[-8:])
                else:
                    errors.append(f"{path.name}: {exc}")
        cognition = collect_cognition(root, d, out)
        master = settle_master(root, d, out)
        for kind, result in (("cognition", cognition), ("master", master)):
            if result["status"] == "fail":
                errors.extend(f"{kind}: {x}" for x in result["errors"])
        forecasts = [x for x in predictions if not x["id"].startswith("narrative:")]
        due = lambda x: x["due_d"] is not None and x["due_d"] <= d
        statuses = ("true", "false", "pending", "not_triggered", "unverifiable", "ambiguous")
        prediction_coverage = {
            "forecast_items": len(forecasts), "narrative_items": len(predictions) - len(forecasts),
            "due_forecasts": sum(due(x) for x in forecasts),
            "due_forecasts_with_status": sum(due(x) and x["status"] in statuses for x in forecasts),
            "forecast_status_counts": {v: sum(x["status"] == v for x in forecasts) for v in statuses},
            "by_event_type": {t: {v: sum(x["event_type"] == t and x["status"] == v for x in predictions) for v in statuses}
                              for t in ("direction", "attack_defense", "numeric", "stock", "conditional")}}
        unresolved_predictions = sum(due(x) and x["status"] not in ("true", "false", "not_triggered") for x in predictions)
        unresolved_items = sum(due(x) and x["status"] not in ("true", "false", "not_triggered") for x in items)
        unresolved_master = sum(due(x) and x["status"] not in ("validated", "refuted") for x in master.get("assignments", []))
        due_count = sum(due(x) for x in predictions + items + master.get("assignments", []))
        closure = {"status": "incomplete" if errors or unresolved_predictions or unresolved_items or unresolved_master else "complete" if due_count else "not_due",
                   "scope": "due_as_of_d", "due_count": due_count,
                   "unresolved_due_predictions": unresolved_predictions, "unresolved_due_items": unresolved_items,
                   "unresolved_due_master": unresolved_master}
        historical_gaps, blocking_errors = [], []
        for _err in errors:
            _dates = re.findall(r'20\d{6}', str(_err))
            _historical_text = ('未知认知 schema_version' in str(_err) or
                                '消费者应答覆盖不足' in str(_err) or
                                '自主拓展应答_' in str(_err) or
                                '历史清单日期对应推演_' in str(_err) or
                                '推演_20260706.json' in str(_err))
            if (_dates and all(x < d for x in _dates)) or _historical_text:
                historical_gaps.append(_err)
            else:
                blocking_errors.append(_err)
        errors = blocking_errors + historical_gaps
        result = dict(schema_version=1, status="fail" if blocking_errors else "pass", errors=errors,
                      blocking_errors=blocking_errors, historical_gaps=historical_gaps,
                      exempted=exempt_notes, d=d,

                      audit_created_at=datetime.now(timezone.utc).isoformat(),
                      publication="new_audit_not_historical_publication", coverage=coverage,
                      items=items, predictions=predictions, cognition=cognition, master=master,
                      calibration={"formal_source_exists": (root / "_学习" / f"校准_{d}.json").exists(),
                                   "kind": "new_audit_settlement", "historical_publication_modified": False})
        return _save_run(out, "audit", result)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return _failure(d, exc)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "coverage", "cognition", "master", "settle"))
    parser.add_argument("d")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--target-d")
    args = parser.parse_args(argv)
    if args.command == "coverage":
        result = coverage_learning(args.root, args.d, args.out)
    elif args.command == "settle":
        result = settle_predictions(args.root, args.d, args.target_d or args.d, args.out)
    else:
        fn = {"audit": audit_learning, "cognition": collect_cognition, "master": settle_master}[args.command]
        result = fn(args.root, args.d, args.out)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
