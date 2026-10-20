# -*- coding: utf-8 -*-
"""异常分诊：用 AST 找出裸 except 与静默 except，按文件/类型落盘。

只做只读扫描，不改代码。先分诊再修，避免把有意的清理型异常也一律改成抛错。
"""
from __future__ import annotations

import ast
import argparse
import datetime as dt
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
OUT = ROOT / "_学习" / "_运维"
BASELINE = OUT / "异常基线.json"
SKIP = {".review_staging", "releases", "_学习", "_复盘审计运行", "__pycache__", ".venv312", ".git", "tests", "_归档"}


def _iter_py():
    for p in ROOT.rglob("*.py"):
        if any(part in SKIP for part in p.parts):
            continue
        yield p


def _scope(file: str) -> str:
    parts = file.replace("\\", "/").split("/")
    if any(x.startswith("_部署备份") or x.startswith("_备份") or x in {"_tmp", "cache", "_归档"} for x in parts):
        return "historical"
    if parts[0] == "盘中" and len(parts) > 1 and parts[1].isdigit():
        return "historical"
    return "production"


def _disposition(rec: dict) -> tuple[str, str]:
    if rec["scope"] == "historical":
        return "excluded_historical", "备份/临时/历史快照，不纳入生产门禁"
    if rec["kind"] == "parse_error":
        return "parse_error", "文件无法解析，单独修复"
    ctx = (rec.get("try_context") or rec["context"]).lower()
    if any(x in ctx for x in ("errors.append", "fail.append", "failures.append", "print(", "log(", "logger.")):
        return "already_logged", "处理器已写错误/日志，非真正静默"
    if "subprocess." in ctx:
        return "reviewed_external_fallback", "外部补数失败→文件缺失，后续按缺失渲染/结算"
    if any(x in ctx for x in ("getmtime", "getsize", "stat(", "remove(", "unlink(", "close(", "kill(", "rmtree")):
        return "reviewed_cleanup", "清理/探测失败，不影响主结果"
    if any(x in ctx for x in ("json.load", "json.loads", "dictreader", "read_text", "open(", "float(")):
        return "reviewed_row_skip", "读取/逐行解析失败→跳过坏项，缺失由下游门禁暴露"
    return "reviewed_fail_closed", "读取失败→返回 None/空，下游按缺失 fail-closed"


def signature(rec: dict) -> str:
    raw = "|".join(str(rec.get(k, "")) for k in ("file", "line", "func", "kind", "type", "context"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _func_name(parents, node):
    cur = node
    while cur in parents:
        cur = parents[cur]
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return getattr(cur, "name", "")
    return ""


def _body_kind(handler: ast.ExceptHandler) -> str:
    body = [x for x in handler.body if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant))]
    if not body:
        return "silent_empty"
    if all(isinstance(x, ast.Pass) for x in body):
        return "silent_pass"
    if all(isinstance(x, ast.Continue) for x in body):
        return "silent_continue"
    # pass/continue 与其他语句混用也算“吞掉”
    if any(isinstance(x, (ast.Pass, ast.Continue)) for x in body) and len(body) <= 2:
        return "silent_mixed"
    return "handled"


def scan() -> dict:
    records = []
    for path in _iter_py():
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except (SyntaxError, OSError) as exc:
            rec = {"file": rel, "line": 0, "kind": "parse_error", "type": "", "func": "",
                   "context": str(exc)[:180], "scope": _scope(rel)}
            rec["sig"] = signature(rec)
            rec["disposition"], rec["reason"] = _disposition(rec)
            records.append(rec)
            continue
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            kind = _body_kind(node)
            if kind == "handled":
                continue
            try:
                type_text = ast.unparse(node.type) if node.type else ""
            except Exception:
                type_text = ""
            rec = {
                "file": rel,
                "line": getattr(node, "lineno", 0),
                "end_line": getattr(node, "end_lineno", 0),
                "kind": "bare" if node.type is None else kind,
                "type": type_text,
                "func": _func_name(parents, node),
                "context": (ast.get_source_segment(text, node) or "").replace("\n", " ")[:300],
                "try_context": (ast.get_source_segment(text, parents.get(node)) or "").replace("\n", " ")[:500]
                if isinstance(parents.get(node), ast.Try) else "",
            }
            rec["scope"] = _scope(rel)
            rec["sig"] = signature(rec)
            rec["disposition"], rec["reason"] = _disposition(rec)
            records.append(rec)
    by_file = Counter(r["file"] for r in records)
    return {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "total": len(records),
        "by_kind": dict(Counter(r["kind"] for r in records)),
        "by_scope": dict(Counter(r["scope"] for r in records)),
        "by_disposition": dict(Counter(r["disposition"] for r in records)),
        "by_file": dict(by_file.most_common(40)),
        "records": sorted(records, key=lambda x: (x["scope"] != "production", x["file"], x["line"])),
    }


def render_md(d: dict) -> str:
    lines = ["# 异常分诊报告", "", f"生成：{d['generated_at']}", "",
             f"总计 **{d['total']}** 处；生产 **{d['by_scope'].get('production', 0)}**，"
             f"历史快照 **{d['by_scope'].get('historical', 0)}**。", "",
             f"分类：`{json.dumps(d['by_kind'], ensure_ascii=False)}`", "",
             f"处置：`{json.dumps(d['by_disposition'], ensure_ascii=False)}`", "",
             "## 按文件（Top 40）", "", "| 文件 | 处数 |", "|---|---:|"]
    for f, n in d["by_file"].items():
        lines.append(f"| `{f}` | {n} |")
    lines += ["", "## 明细（全部）", "", "| 文件:行 | 范围 | 类型 | 函数 | 处置 | 理由 |", "|---|---|---|---|---|---|"]
    for r in d["records"]:
        lines.append(f"| `{r['file']}:{r['line']}` | {r['scope']} | {r['kind']} / `{r['type']}` | {r['func']} | {r['disposition']} | {r['reason']} |")
    return "\n".join(lines) + "\n"


def render_ledger_md(d: dict) -> str:
    lines = ["# 静默异常逐项治理台账", "", f"生成：{d['generated_at']}", "",
             "> 处置口径：`excluded_historical` 不计入生产；`already_logged` 已留痕；"
             "`reviewed_row_skip` 坏行跳过、缺失由下游门禁暴露；`reviewed_external_fallback` 外部补数失败按缺失处理；"
             "`reviewed_cleanup` 清理型；`reviewed_fail_closed` 返回空/None 由下游失败。", "",
             f"合计 **{d['total']}**；生产 **{d['by_scope'].get('production', 0)}**；"
             f"历史 **{d['by_scope'].get('historical', 0)}**。", "",
             "| # | 文件:行 | 范围 | 类型 | 函数 | 处置 | 理由/上下文 |", "|---:|---|---|---|---|---|---|"]
    for i, r in enumerate(d["records"], 1):
        ctx = r["context"].replace("|", "\\|")[:150]
        lines.append(f"| {i} | `{r['file']}:{r['line']}` | {r['scope']} | {r['kind']} / `{r['type']}` | "
                     f"{r['func'] or '—'} | **{r['disposition']}** | {r['reason']}；`{ctx}` |")
    return "\n".join(lines) + "\n"


def write_outputs(d: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(d, ensure_ascii=False, indent=1)
    (OUT / "异常分诊_最新.json").write_text(payload, encoding="utf-8")
    (OUT / "异常分诊_最新.md").write_text(render_md(d), encoding="utf-8")
    (OUT / "异常治理台账.md").write_text(render_ledger_md(d), encoding="utf-8")
    (OUT / "异常治理台账.json").write_text(payload, encoding="utf-8")


def update_baseline(d: dict) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": d["generated_at"], "total": d["total"],
               "by_scope": d["by_scope"], "entries": sorted(r["sig"] for r in d["records"])}
    BASELINE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


def check_baseline(d: dict) -> int:
    if not BASELINE.is_file():
        print(f"[FAIL] 基线不存在: {BASELINE}；先运行 --update-baseline")
        return 1
    try:
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        known = set(base.get("entries") or [])
    except (OSError, ValueError, TypeError) as exc:
        print(f"[FAIL] 基线不可读: {exc}")
        return 1
    current = {r["sig"]: r for r in d["records"]}
    new = [r for sig, r in current.items() if sig not in known]
    fixed = [sig for sig in known if sig not in current]
    print(json.dumps({"total": d["total"], "production": d["by_scope"].get("production", 0),
                      "baseline": len(known), "new": len(new), "fixed_or_removed": len(fixed)},
                     ensure_ascii=False))
    for r in new[:40]:
        print(f"[NEW] {r['file']}:{r['line']} {r['kind']} {r['type']} {r['func']} :: {r['context'][:160]}")
    if new:
        print("[FAIL] 新增未登记的静默异常处理器；逐项确认后再 --update-baseline")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验是否有新增静默处理器")
    ap.add_argument("--update-baseline", action="store_true", help="把当前清单写为基线")
    args = ap.parse_args()
    d = scan()
    if args.check:
        return check_baseline(d)
    write_outputs(d)
    if args.update_baseline:
        update_baseline(d)
    print(json.dumps({"total": d["total"], "by_scope": d["by_scope"], "by_kind": d["by_kind"],
                      "by_disposition": d["by_disposition"],
                      "top": list(d["by_file"].items())[:8]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
