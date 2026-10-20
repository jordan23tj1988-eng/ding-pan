# -*- coding: utf-8 -*-
"""死脚本候选清单：静态扫描根目录 .py 是否被主链/文档/任务引用。

只产清单，不删除。动态 import、外部手工调用可能产生假阳性，需人工二次确认。
"""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
CRON = Path(r"C:\Users\66353\AppData\Local\hermes\profiles\a\cron\jobs.json")
SKIP_DIRS = {".review_staging", "releases", "_学习", "_复盘审计运行", "__pycache__", ".venv312", ".git", "_诊断", "_归档"}
TEXT_EXT = {".py", ".bat", ".cmd", ".ps1", ".vbs"}
# 文档/历史记录会把所有脚本都提到，纳入会制造“都活着”的假阴性。
SKIP_NAMES = {"_变更总账.md", "_链路地图.md", "MODULE_MAP.md", "AGENTS.md"}


def _haystack_files():
    import os
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and not x.startswith("_tmp")]
        for name in filenames:
            if name in SKIP_NAMES:
                continue
            p = Path(dirpath) / name
            if p.suffix.lower() not in TEXT_EXT:
                continue
            try:
                if p.stat().st_size > 2 * 1024 * 1024:
                    continue
            except OSError:
                continue
            yield p
    if CRON.is_file():
        yield CRON


def _doc_files():
    import os
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and not x.startswith("_tmp")]
        for name in filenames:
            if not name.endswith(".md") or name == "_变更总账.md":
                continue
            p = Path(dirpath) / name
            try:
                if p.stat().st_size > 1024 * 1024:
                    continue
            except OSError:
                continue
            yield p


def build() -> dict:
    scripts = sorted(ROOT.glob("*.py"))
    texts = {}
    for p in _haystack_files():
        try:
            texts[p.resolve()] = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    docs = {}
    for p in _doc_files():
        try:
            docs[p.resolve()] = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    entries = []
    for s in scripts:
        stem = s.stem
        pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(stem) + r"(?![A-Za-z0-9_])")
        refs = []
        for p, text in texts.items():
            if p == s.resolve():
                continue
            if pat.search(text):
                refs.append(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p))
        doc_refs = []
        for p, text in docs.items():
            if pat.search(text):
                doc_refs.append(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p))
        entries.append({
            "script": s.name,
            "lines": len(s.read_text(encoding="utf-8", errors="ignore").splitlines()),
            "mtime": dt.datetime.fromtimestamp(s.stat().st_mtime).isoformat(timespec="seconds"),
            "refs": len(refs),
            "ref_files": refs[:8],
            "doc_refs": len(doc_refs),
            "doc_files": doc_refs[:5],
        })
    dead = [x for x in entries if x["refs"] == 0]
    strong = [x for x in dead if x["doc_refs"] == 0]
    manual = [x for x in dead if x["doc_refs"] > 0]
    return {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "root_scripts": len(entries),
        "referenced": len(entries) - len(dead),
        "unreferenced": len(dead),
        "strong_candidates": len(strong),
        "manual_or_doc": len(manual),
        "strong": sorted(strong, key=lambda x: (-x["lines"], x["script"])),
        "manual": sorted(manual, key=lambda x: (-x["lines"], x["script"])),
        "all": entries,
        "caveat": "仅静态匹配；动态 import、外部手工调用、cron 中拼接名称可能漏检，删除前须人工确认。",
    }


def render_md(d: dict) -> str:
    lines = ["# 疑似死脚本 / 未接线脚本清单", "", f"生成：{d['generated_at']}", "",
             f"根目录脚本 **{d['root_scripts']}** 个；有代码引用 **{d['referenced']}**；零代码引用 **{d['unreferenced']}** "
             f"（强候选 **{d['strong_candidates']}**，文档提及但未接线 **{d['manual_or_doc']}**）。", "",
             "> 只产清单，不删除。静态扫描会漏掉动态 import / 外部手工调用 / 名称拼接，删前必须人工确认。", "",
             "## A. 强候选（代码与文档都零引用）", "", "| 脚本 | 行数 | 最后修改 |", "|---|---:|---|"]
    for x in d["strong"]:
        lines.append(f"| `{x['script']}` | {x['lines']} | {x['mtime']} |")
    lines += ["", "## B. 文档提及但未接线（更像手工工具，不应直接删）", "",
              "| 脚本 | 行数 | 提及文档 |", "|---|---:|---|"]
    for x in d["manual"]:
        lines.append(f"| `{x['script']}` | {x['lines']} | {', '.join(x['doc_files'][:2])} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    out = ROOT / "_学习" / "_运维"
    out.mkdir(parents=True, exist_ok=True)
    d = build()
    (out / "死脚本_最新.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "死脚本_最新.md").write_text(render_md(d), encoding="utf-8")
    print(json.dumps({"root": d["root_scripts"], "unreferenced": d["unreferenced"],
                      "strong": d["strong_candidates"], "manual": d["manual_or_doc"],
                      "top": [x["script"] for x in d["strong"][:15]]}, ensure_ascii=False, indent=1))
    sys.exit(0)
