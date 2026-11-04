#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""能力回执汇总.py —— 把七域分路回执机械汇总为根级 能力使用回执_{d}.json。

背景：能力进化接线.py consume 门禁只认根级回执（七域全覆盖、绑定预加载 sha256），
而五路+cycle+master 各 agent 只写自己那份 能力使用回执_{route}_{d}.json。
历史做法是宿主在深夜手工补写根级回执（20261030 即如此），漏一次就整条复盘链 FAIL。
本脚本把"补写"变成可复现的机械汇总：只搬运分路回执原文，不改写 effect、不补造能力。

纪律：零编造。
- 分路回执缺失 / route 字段错 / considered_ids 与预加载 eligible 不一致 / applied 缺
  effect|source_locator / rejected 缺 reason —— 任一命中即退出码 1，不写任何文件。
- 根级文里的每条 applied/rejected 均为分路回执原文对象；note 原样保留。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROUTES = ("auction", "lhb", "theme", "logic", "limitup", "cycle", "master")
PRELOAD_NAME = "能力预加载_{d}.json"
RECEIPT_NAME = "能力使用回执_{d}.json"
ROUTE_RECEIPT_NAME = "能力使用回执_{route}_{d}.json"
ALLOWED_STATUS = {"ready", "applied", "rejected_all", "no_eligible_capabilities", "not_applicable"}


def _load(p: Path):
    with p.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _atomic_write(p: Path, doc: dict) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, allow_nan=False)
        fh.write("\n")
    os.replace(tmp, p)


def build(root: Path, d: str) -> dict:
    learn = root / "_学习"
    preload_path = learn / PRELOAD_NAME.format(d=d)
    if not preload_path.exists():
        raise ValueError(f"缺少能力预加载: {preload_path}")
    preload = _load(preload_path)
    if preload.get("as_of") != d or preload.get("decision_cutoff") != d:
        raise ValueError("能力预加载日期/决策截止日错配")
    if preload.get("schema_version") != 1:
        raise ValueError("能力预加载 schema_version 不支持")

    eligible = {
        route: {str(x.get("id")): x for x in (preload.get("routes", {}).get(route, {}).get("records") or [])}
        for route in ROUTES
    }

    routes_out: dict[str, dict] = {}
    applied_total = 0
    sources: list[str] = []
    for route in ROUTES:
        rp = learn / ROUTE_RECEIPT_NAME.format(route=route, d=d)
        if not rp.exists():
            raise ValueError(f"{route}: 缺少分路回执 {rp.name}——不代写、不猜能力")
        src = _load(rp)
        if not isinstance(src, dict):
            raise ValueError(f"{route}: 分路回执格式错误")
        if src.get("route") not in (None, route):
            raise ValueError(f"{route}: 分路回执 route 字段为 {src.get('route')}，错配")
        status = src.get("status")
        if status not in ALLOWED_STATUS:
            raise ValueError(f"{route}: 未知能力消费状态 {status}")
        considered = src.get("considered_ids") or []
        applied = src.get("applied") or []
        rejected = src.get("rejected") or []
        if not isinstance(considered, list) or len(considered) != len(set(considered)):
            raise ValueError(f"{route}: considered_ids 缺失或重复")
        if set(map(str, considered)) != set(eligible[route]):
            raise ValueError(
                f"{route}: considered_ids 与预加载 eligible 不一致 "
                f"(回执={sorted(map(str, considered))} 预加载={sorted(eligible[route])})"
            )
        if not eligible[route] and status not in {"no_eligible_capabilities", "not_applicable"}:
            raise ValueError(f"{route}: 无可复用能力却写 status={status}")
        if eligible[route] and status not in {"applied", "rejected_all"}:
            raise ValueError(f"{route}: 有可复用能力却写 status={status}")
        for ev in applied:
            if not isinstance(ev, dict) or str(ev.get("id")) not in eligible[route]:
                raise ValueError(f"{route}: applied 引用未知能力 {ev!r}")
            if not ev.get("effect") or not ev.get("source_locator"):
                raise ValueError(f"{route}: applied 必须写 effect 和 source_locator")
        for ev in rejected:
            if not isinstance(ev, dict) or str(ev.get("id")) not in eligible[route]:
                raise ValueError(f"{route}: rejected 引用未知能力 {ev!r}")
            if not ev.get("reason"):
                raise ValueError(f"{route}: rejected 必须写明 reason")

        item = {
            "status": status,
            "considered_ids": [str(x) for x in considered],
            "applied": applied,
            "rejected": rejected,
        }
        note = src.get("note") or src.get("说明")
        if note:
            item["note"] = note
        routes_out[route] = item
        applied_total += len(applied)
        sources.append(rp.name)

    return {
        "schema_version": 1,
        "as_of": d,
        "decision_cutoff": d,
        "preload": {
            "path": str(preload_path),
            "sha256": _sha256(preload_path),
        },
        "routes": routes_out,
        "applied_total": applied_total,
        "source": "能力回执汇总.py 机械汇总七域分路回执（原文搬运，零改写、零补造）；来源: " + ", ".join(sources),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("d")
    ap.add_argument("--root", default=r"D:\股票数据\市场数据")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    d = str(args.d).replace("-", "")
    root = Path(args.root).resolve()
    try:
        doc = build(root, d)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "fail", "as_of": d, "error": str(exc)}, ensure_ascii=False))
        return 1
    out = Path(args.out) if args.out else root / "_学习" / RECEIPT_NAME.format(d=d)
    if not args.dry_run:
        _atomic_write(out, doc)
    print(json.dumps({
        "status": "pass",
        "as_of": d,
        "written": None if args.dry_run else str(out),
        "applied_total": doc["applied_total"],
        "routes": {r: {"status": v["status"], "applied": len(v["applied"]), "rejected": len(v["rejected"])}
                   for r, v in doc["routes"].items()},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
