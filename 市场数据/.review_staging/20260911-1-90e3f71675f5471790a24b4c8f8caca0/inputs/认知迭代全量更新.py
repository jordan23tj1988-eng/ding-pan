# -*- coding: utf-8 -*-
"""认知迭代全量更新入口。

这是每日链路历史名称 ``认知迭代全量更新.py`` 的兼容入口。它不自行解释
HTML 或行情，而是复用 ``review_learning.collect_cognition`` 的严格收集器，
再把独立 run 中的记录投影为渲染器兼容的认知库快照。

用法：
    python -B 认知迭代全量更新.py YYYYMMDD
    python -B 认知迭代全量更新.py YYYYMMDD --root D:/股票数据/市场数据 \
        --out D:/股票数据/review_run_YYYYMMDD_cognition

约束：日期必须显式传入；只消费 d<=目标日的记录；审计 run 写到输入 root
之外；快照使用目标日而非系统当前日期；不覆盖 judgment、荐票或页面发出版。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

ROUTES = ("auction", "cycle", "lhb", "limitup", "logic", "theme", "master")
DATE_RE = re.compile(r"^\d{8}$")


def _date(value: str) -> str:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        raise ValueError("日期必须为严格 YYYYMMDD")
    datetime.strptime(value, "%Y%m%d")
    return value


def _date_key(value) -> str | None:
    text = str(value or "").replace("-", "")
    return text if DATE_RE.fullmatch(text) else None


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} 顶层必须为对象")
    return data


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent,
                           prefix=path.name + ".", suffix=".tmp", delete=False) as fh:
        temp = Path(fh.name)
        json.dump(data, fh, ensure_ascii=False, indent=1, allow_nan=False)
        fh.write("\n")
    os.replace(temp, path)


def _record_to_legacy(record: dict) -> dict:
    """只做字段投影，不从 claim 推导新的事实或档位。"""
    claim = record.get("claim")
    basis = record.get("basis")
    raw_date = _date_key(record.get("d"))
    dashed = (f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}" if raw_date else record.get("d"))
    return {
        "日期": dashed,
        "标题": claim if isinstance(claim, str) else "",
        "正文": claim if isinstance(claim, str) else None,
        "支撑": basis,
        "档位": None,
        "类型": "结构化认知" if record.get("origin") == "structured" else "历史认知",
        "来源": record.get("source"),
        "可证伪条件": record.get("falsifier"),
        "状态": record.get("status"),
    }


def _legacy_key(item: dict) -> tuple:
    return (str(item.get("日期") or "").replace("-", ""),
            str(item.get("标题") or ""), str(item.get("正文") or ""))


def _prior_items(root: Path, route: str, target: str) -> list[dict]:
    """取目标日前最近的日期化快照作为历史基线，保证"全量"不丢历史条目。"""
    candidates = []
    for path in (root / "_学习" / "子agent增强").glob(f"认知库_{route}_????????.json"):
        match = re.search(r"_(\d{8})\.json$", path.name)
        if not match or match.group(1) >= target:
            continue
        try:
            items = _load_json(path).get("条目")
        except (OSError, ValueError, TypeError):
            continue
        if isinstance(items, list) and items:
            candidates.append((match.group(1), items))
    if not candidates:
        return []
    return [x for x in candidates[-1][1] if isinstance(x, dict)
            and (_date_key(x.get("日期")) or "99999999") <= target]


def _write_snapshots(root: Path, target: str, records: list[dict]) -> dict[str, int]:
    grouped: dict[str, list[dict]] = {route: _prior_items(root, route, target) for route in ROUTES}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("认知 run 含非对象记录")
        route = record.get("route")
        record_date = _date_key(record.get("d"))
        if route not in grouped:
            raise ValueError(f"认知 run 含未知路: {route}")
        if record_date is None or record_date > target:
            raise ValueError(f"认知记录日期越过目标日: {record.get('d')}")
        grouped[route].append(_record_to_legacy(record))

    enhanced = root / "_学习" / "子agent增强"
    counts = {}
    updated = f"{target[:4]}-{target[4:6]}-{target[6:]}"
    for route, raw_items in grouped.items():
        deduped: dict[tuple, dict] = {}
        for item in raw_items:
            if isinstance(item, dict):
                deduped[_legacy_key(item)] = item
        items = sorted(deduped.values(),
                       key=lambda row: (str(row.get("日期") or ""), str(row.get("标题") or "")),
                       reverse=True)
        payload = {
            "route": route,
            "version": 2,
            "updated": updated,
            "as_of": target,
            "源": "review_learning.collect_cognition 独立run + 目标日前最近日期化快照；仅含日期不晚于as_of的记录",
            "条数": len(items),
            "条目": items,
        }
        _atomic_json(root / "_学习" / f"_认知库_{route}.json", payload)
        dated = dict(payload)
        dated["源"] = "认知迭代全量更新.py 输出的日期化增强快照"
        _atomic_json(enhanced / f"认知库_{route}_{target}.json", dated)
        counts[route] = len(items)
    return counts


def run(target: str, root: Path, out: Path) -> dict:
    target = _date(target)
    root = root.resolve()
    out = out.resolve()
    if not root.is_dir():
        raise ValueError(f"输入 root 不存在: {root}")
    if out.is_relative_to(root):
        raise ValueError("--out 必须位于输入 root 之外，避免把审计产物混入生产输入")

    # 延迟导入，确保该入口与项目现有 P2 收集器保持单一真源。
    sys.path.insert(0, str(root))
    from review_learning import collect_cognition

    collected = collect_cognition(root, target, out)
    if collected.get("status") != "pass":
        return {
            "status": "fail",
            "d": target,
            "errors": collected.get("errors", ["collect_cognition failed"]),
            "audit_artifact": collected.get("artifact"),
            "snapshots_written": [],
        }

    artifact = Path(collected["artifact"])
    audit = _load_json(artifact)
    records = audit.get("records")
    if not isinstance(records, list):
        raise ValueError("认知收集器产物缺少 records 列表")
    counts = _write_snapshots(root, target, records)
    return {
        "status": "pass",
        "d": target,
        "as_of": target,
        "audit_artifact": str(artifact),
        "routes": counts,
        "total_records": sum(counts.values()),
        "snapshots_written": [
            str(root / "_学习" / f"_认知库_{route}.json") for route in ROUTES
        ],
        "enhanced_written": [
            str(root / "_学习" / "子agent增强" / f"认知库_{route}_{target}.json")
            for route in ROUTES
        ],
        "historical_publication_modified": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("d", help="目标日期，严格 YYYYMMDD")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        target = _date(args.d)
        root = args.root.resolve()
        out = (args.out or root.parent / f"review_run_{target}_cognition").resolve()
        result = run(target, root, out)
        # 在认知库更新后同步能力进化账本：承接历史、去重、保留验证/命中证据
        import subprocess, sys
        evo = root / "自我进化闭环.py"
        if evo.exists() and result.get("status") == "pass":
            p = subprocess.run([sys.executable, str(evo), target], cwd=str(root), capture_output=True, text=True, encoding="utf-8")
            result["evolution_ledger"] = {"status": "pass" if p.returncode == 0 else "fail", "output": p.stdout[-2000:]}
    except (OSError, ValueError, TypeError, KeyError, ImportError) as exc:
        result = {"status": "fail", "d": args.d, "errors": [str(exc)], "snapshots_written": []}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
