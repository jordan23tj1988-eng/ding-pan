# -*- coding: utf-8 -*-
"""复盘链健康门禁：只读核验，不补写缺失历史结果。

用法：python 复盘链健康检查.py 20260922 [--strict]
输出：_学习/复盘链健康_YYYYMMDD.json
"""
from __future__ import annotations
import argparse, datetime as dt, glob, json, os, re, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LEARN = ROOT / "_学习"
ARCHIVE = ROOT / "复盘" / "盯盘台" / "archive"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def code_of(x: Any) -> str | None:
    if not isinstance(x, dict):
        return None
    for k in ("代码", "code", "证券代码", "股票代码", "标的代码"):
        v = x.get(k)
        if v is not None and str(v).strip():
            return str(v).strip().zfill(6)
    return None


def as_rows(obj: Any, keys: tuple[str, ...]) -> list[dict]:
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        for k in keys:
            if isinstance(obj.get(k), list):
                return [x for x in obj[k] if isinstance(x, dict)]
    return []


def source_rows(path: Path, route: str) -> tuple[list[dict], str]:
    d = load_json(path)
    if not isinstance(d, dict):
        return [], "invalid"
    if route == "lhb":
        # 正式席位荐票是 top5，不把全量研究候选冒充为已发荐票。
        return as_rows(d.get("top5"), ("top5", "荐票", "明细")), "top5"
    if route == "limitup":
        return as_rows(d.get("top5"), ("top5", "荐票", "明细")), "top5"
    if route == "theme":
        return as_rows(d.get("荐票"), ("荐票", "明细", "top5")), "荐票"
    if route == "logic":
        return as_rows(d.get("荐票", {}).get("标的") if isinstance(d.get("荐票"), dict) else d.get("荐票"), ("荐票", "明细")), "荐票.标的"
    if route == "auction":
        return as_rows(d.get("荐票") or d.get("池") or d.get("明细"), ("荐票", "池", "明细")), "荐票/池"
    return [], "unknown"


def settle_rows(path: Path) -> list[dict]:
    d = load_json(path)
    if not isinstance(d, dict):
        return []
    # 各路历史口径不同；只读取明确的逐票/Top5结果，不把汇总数字当逐票结算。
    for k in ("明细", "Top5", "top5", "荐票", "结算明细"):
        if isinstance(d.get(k), list):
            return [x for x in d[k] if isinstance(x, dict)]
    return []


def route_paths(route: str, issue: str, settle: str) -> tuple[list[Path], list[Path]]:
    source_patterns = {
        "auction": [f"竞价池发出_{issue}.json", f"竞价荐票_{issue}.json"],
        "lhb": [f"席位荐票_{issue}.json", f"龙虎榜荐票_{issue}.json"],
        "theme": [f"题材荐票_{issue}.json"],
        "logic": [f"逻辑判断_{issue}.json", f"logic判断_{issue}.json"],
        "limitup": [f"涨停质量荐票_{issue}.json", f"涨停荐票_{issue}.json"],
    }
    settle_patterns = {
        "auction": [f"竞价荐票结算_{settle}.json", f"竞价池结算_{settle}.json"],
        "lhb": [f"席位荐票结算_{settle}.json", f"龙虎榜荐票结算_{settle}.json"],
        "theme": [f"题材荐票结算_{settle}.json"],
        "logic": [f"逻辑荐票结算_{settle}.json"],
        "limitup": [f"质量荐票结算_{settle}.json", f"涨停荐票结算_{settle}.json"],
    }
    return ([LEARN / x for x in source_patterns[route]], [LEARN / x for x in settle_patterns[route]])


def first_existing(paths: list[Path]) -> Path | None:
    return next((p for p in paths if p.exists()), None)


def previous_trade_day(day: str) -> str | None:
    # 优先使用系统已有交易日历；没有时只回退到最近存在日数据目录，绝不猜周末之外的节假日。
    for name in ("_交易日历.json", "交易日历.json"):
        p = LEARN / name
        d = load_json(p)
        vals = d if isinstance(d, list) else (d.get("交易日", []) if isinstance(d, dict) else [])
        vals = [str(x).replace("-", "")[:8] for x in vals]
        prior = sorted(x for x in vals if re.fullmatch(r"\d{8}", x) and x < day)
        if prior:
            return prior[-1]
    dirs = []
    for p in ROOT.glob("20????????"):
        if p.is_dir() and p.name < day:
            dirs.append(p.name)
    if dirs:
        return sorted(dirs)[-1]
    return None


def atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def check(issue: str) -> dict:
    settlement_day = previous_trade_day(issue)
    continuity = {
        "target": issue,
        "artifacts": {
            "总审": (LEARN / f"总审_{issue}.json").exists(),
            "推演": (LEARN / f"推演_{issue}.json").exists(),
            "盯盘台归档": (ARCHIVE / f"{issue}.html").exists(),
        },
        "release_dirs": len(glob.glob(str(ROOT / "releases" / f"{issue}-*"))),
    }
    continuity["pass"] = all(continuity["artifacts"].values())
    routes = {}
    total_issued = total_settled = 0
    missing_source = []
    failures = []
    for route in ("auction", "lhb", "theme", "logic", "limitup"):
        if settlement_day is None:
            routes[route] = {"status": "unknown", "reason": "找不到上一交易日，未猜测结算日"}
            continue
        sp, tp = route_paths(route, settlement_day, settlement_day)
        source = first_existing(sp)
        settle = first_existing(tp)
        if source is None:
            missing_source.append(route)
            routes[route] = {"status": "missing_source", "issue_day": settlement_day, "source_candidates": [str(x) for x in sp], "settlement": str(settle) if settle else None}
            continue
        issued, source_basis = source_rows(source, route)
        issued_codes = [code_of(x) for x in issued if code_of(x)]
        if settle is None:
            settled_rows = []
        else:
            settled_rows = settle_rows(settle)
        settled_codes = [code_of(x) for x in settled_rows if code_of(x)]
        unique_issued = set(issued_codes)
        unique_settled = set(settled_codes)
        matched = len(unique_issued & unique_settled)
        dup_settle = len(settled_codes) - len(unique_settled)
        ratio = (matched / len(unique_issued)) if unique_issued else None
        total_issued += len(unique_issued)
        total_settled += matched
        status = "pass" if ratio is not None and ratio >= 0.90 and dup_settle == 0 else ("empty_issued" if not unique_issued else "fail")
        if status == "fail":
            failures.append(route)
        routes[route] = {
            "status": status, "issue_day": settlement_day,
            "source": str(source), "source_basis": source.name,
            "issued_count": len(unique_issued), "settlement": str(settle) if settle else None,
            "settled_rows": len(settled_codes), "matched_count": matched,
            "coverage": ratio, "duplicate_settlement_rows": dup_settle,
            "missing_codes": sorted(unique_issued - unique_settled),
        }
    overall = (total_settled / total_issued) if total_issued else None
    hard_fail = (not continuity["pass"]) or bool(failures)
    result = {
        "schema_version": 1, "checked_at": dt.datetime.now().astimezone().isoformat(),
        "target_date": issue, "settlement_date": settlement_day,
        "status": "fail" if hard_fail else ("warn" if missing_source else "pass"),
        "gate": {"continuity_pass": continuity["pass"], "coverage_gate": "pass" if overall is None or overall >= 0.90 else "fail", "threshold": 0.90},
        "continuity": continuity, "coverage": {"issued_count": total_issued, "matched_count": total_settled, "ratio": overall, "routes": routes, "missing_source_routes": missing_source, "failed_routes": failures},
        "policy": "缺源=缺口告警；缺少结算不可视为无荐票；不补写历史收益；只对明确发出版逐票计覆盖率",
    }
    atomic_write(LEARN / f"复盘链健康_{issue}.json", result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?", default=dt.date.today().strftime("%Y%m%d"))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    result = check(args.date.replace("-", ""))
    print(json.dumps({"status": result["status"], "target_date": result["target_date"], "settlement_date": result["settlement_date"], "coverage": result["coverage"]["ratio"], "issued": result["coverage"]["issued_count"], "matched": result["coverage"]["matched_count"], "continuity": result["continuity"]["pass"], "failed_routes": result["coverage"]["failed_routes"], "missing_source_routes": result["coverage"]["missing_source_routes"]}, ensure_ascii=False))
    return 1 if args.strict and result["status"] == "fail" else 0

if __name__ == "__main__":
    raise SystemExit(main())
