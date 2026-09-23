# -*- coding: utf-8 -*-
"""restore_lhb_page.py — 龙虎榜页黄金版恢复与能力模块保留。

与 restore_cycle_page.py 同构：
- 黄金只读版提供页面壳、CSS、导航、页脚；
- module_render_lhb.py 提供目标日动态头部及前四段；
- 当前站点/概览页的两个 evolution section 原样保留；
- PAPERTRADE 从目标日模拟盘引擎产物重接，缺失时保留成对空锚点；
- 供 _deploy_site 每次发布自动调用，避免一次性手工修复。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import os
from pathlib import Path

BASE = Path(r"D:/股票数据/市场数据")
GOLDEN = Path(r"D:/黄金对照版717/lhb.html")
SITE = BASE / "复盘/盯盘台/lhb.html"
INDEX = BASE / "复盘/盯盘台/index.html"
TMP_DIR = BASE / "_tmp"
# 发布候选站点后处理(2026-09-12)：同一套恢复逻辑可跑在候选 site 上，使
# “被门禁检查的页面”与“被部署的页面”同源；不带环境变量时仍是现站默认行为。
TARGET = Path(os.environ["LHB_PAGE_TARGET"]) if os.environ.get("LHB_PAGE_TARGET") else SITE
SOURCE = Path(os.environ["LHB_PAGE_SOURCE"]) if os.environ.get("LHB_PAGE_SOURCE") else TARGET
# 候选站点上概览页尚未重建时，能力模块/CSS 回退源(默认现站龙虎榜页)。
ABILITY_FALLBACK = Path(os.environ["LHB_ABILITY_FALLBACK"]) if os.environ.get("LHB_ABILITY_FALLBACK") else (
    SITE if TARGET != SITE else None
)


def _evolution_sections(html: str) -> list[str]:
    return re.findall(r'<section class="evolution"[^>]*>.*?</section>', html, re.S)


# 黄金版龙虎榜工程不含“数据边界”模块(2026-09-12 用户拍板，防复发)。
# 头部从发布页继承、动态段来自渲染器，两处都可能把它带回来，故一律剥离并在末尾断言。
DATA_BOUNDARY_CARD_RE = re.compile(r'<div class="card"><b>数据边界</b><ul>.*?</ul></div>', re.S)
DATA_BOUNDARY_INNER_RE = re.compile(r'<div class="inner-limit"><b>数据边界</b><ul>.*?</ul></div>', re.S)


def _strip_data_boundary(html: str) -> str:
    html = DATA_BOUNDARY_CARD_RE.sub("", html)
    return DATA_BOUNDARY_INNER_RE.sub("", html)


# 头部截取终点：席位段壳 / 数据边界卡 / 段一 h2，取最先出现者，避免把“数据边界”带进黄金页。
HEAD_STOP_MARKS = ('<section id="seats"', '<div class="card"><b>数据边界</b>', "<h2>一")


def _head_bounds(src: str) -> tuple[int, int]:
    start = src.find('<div class="wrap">')
    if start < 0:
        return -1, -1
    stops = [p for p in (src.find(mark, start) for mark in HEAD_STOP_MARKS) if p > start]
    return start, (min(stops) if stops else -1)


def _renumber_evolution(sections: list[str]) -> list[str]:
    if len(sections) != 2:
        raise RuntimeError(f"能力进化模块数量异常: {len(sections)}")
    out = []
    for n, sec in zip(("五", "六"), sections):
        sec = re.sub(r"<h2>(?:[一二三四五六七八九十]\s+)?自主拓展", f"<h2>{n} 自主拓展", sec, count=1)
        sec = re.sub(r"<h2>(?:[一二三四五六七八九十]\s+)?认知迭代", f"<h2>{n} 认知迭代", sec, count=1)
        out.append(sec)
    return out


def _evolution_style(source: str) -> str:
    """优先复制同步器已产出的精确 CSS，回退到概览样式提取。"""
    m = re.search(r'<style id="overview-evolution-sync">.*?</style>', source, re.S)
    if m:
        return m.group(0)
    css = ""
    # 仅在 style 内容内提取，避免旧空 style 的 HTML 标签被跨标签正则吞入。
    for style_body in re.findall(r'<style\b[^>]*>(.*?)</style\s*>', source, re.S | re.I):
        css += "".join(re.findall(
            r'[^{}]*\.(?:evolution|evo-stats|evo-stat|evo-list|evo-row|evo-empty)[^{}]*\{[^{}]*\}',
            style_body,
        ))
    if not css:
        raise RuntimeError("未找到能力进化 CSS")
    return '<style id="overview-evolution-sync">' + css + "</style>"


def _papertrade(d: str) -> str:
    paper = BASE / "_学习/_模拟盘/lhb" / f"看板_{d}.html"
    if paper.exists():
        return "<!--PAPERTRADE-->\n" + paper.read_text(encoding="utf-8") + "\n<!--/PAPERTRADE-->\n"
    return "<!--PAPERTRADE-->\n<!--/PAPERTRADE-->\n"


def _render_dynamic(d: str) -> str:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out = TMP_DIR / f"lhb_dynamic_{d}.html"
    renderer = BASE / "module_render_lhb.py"
    cp = subprocess.run(
        [sys.executable, str(renderer), d, "--out", str(out)],
        cwd=str(BASE), capture_output=True, text=True, encoding="utf-8",
    )
    if cp.returncode != 0 or not out.exists():
        raise RuntimeError("龙虎榜动态渲染失败:\n" + cp.stdout[-2000:] + cp.stderr[-2000:])
    dynamic = out.read_text(encoding="utf-8")
    if "<h2>一" not in dynamic or "<h2>五" not in dynamic:
        raise RuntimeError("动态龙虎榜 body 缺少前四段边界")
    return dynamic


def build_page(d: str, current_html: str | None = None) -> str:
    if not GOLDEN.exists(): raise RuntimeError(f"黄金版不存在: {GOLDEN}")
    if not SOURCE.exists(): raise RuntimeError(f"当前页不存在: {SOURCE}")
    golden = GOLDEN.read_text(encoding="utf-8")
    current = current_html if current_html is not None else SOURCE.read_text(encoding="utf-8")
    evo = _evolution_sections(current)
    index_src = SOURCE.parent / "index.html" if SOURCE != SITE else INDEX
    if len(evo) < 2 and index_src.exists(): evo = _evolution_sections(index_src.read_text(encoding="utf-8"))
    if len(evo) < 2 and ABILITY_FALLBACK is not None:
        if not ABILITY_FALLBACK.is_file():
            raise RuntimeError(f"能力模块回退源缺失: {ABILITY_FALLBACK}")
        evo = _evolution_sections(ABILITY_FALLBACK.read_text(encoding="utf-8"))
    evo = _renumber_evolution(evo[:2])

    dynamic = _render_dynamic(d)
    first_five = dynamic.find("<h2>五")
    dynamic_front = dynamic[:first_five].rstrip()
    # judgment body 的 section 壳可能漂移/缺闭合；黄金龙虎榜工程为 h2 直连，
    # 只保留动态组件内容，剥离 section 标签，避免把新壳带入黄金页。
    dynamic_front = re.sub(r"</?section(?:\s[^>]*)?>", "", dynamic_front)
    dynamic_front = _strip_data_boundary(dynamic_front)
    h1 = dynamic_front.find("<h2>一")
    if h1 < 0: raise RuntimeError("动态 body 缺少段一")

    wrap = golden.find('<div class="wrap">')
    if wrap < 0: raise RuntimeError("黄金版 wrap 缺失")
    wrap_end = golden.find(">", wrap) + 1
    foot = golden.rfind('<div class="foot">')
    if foot < 0: raise RuntimeError("黄金版 foot 缺失")
    # 发布页头部含当日 ticker/hero/kpi/PAPERTRADE；优先保留它。
    # 手工首跑则从本次恢复前备份回读，后续发布由 release 页直接提供。
    head_source = current
    head_start, head_end = _head_bounds(head_source)
    if head_end < 0:
        for candidate in sorted(
            SOURCE.parent.glob("lhb.html.before_*.bak"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            probe = candidate.read_text(encoding="utf-8")
            ps, pe = _head_bounds(probe)
            if ps >= 0 and pe > ps:
                head_source, head_start, head_end = probe, ps, pe
                break
    if head_end > head_start:
        head = head_source[head_source.find(">", head_start) + 1:head_end]
    else:
        head = dynamic_front[:h1]
        if "<!--PAPERTRADE-->" not in head:
            head += _papertrade(d)
    head = _strip_data_boundary(head)
    body = head.rstrip() + "\n" + dynamic_front[h1:].lstrip()
    if body.count("<!--PAPERTRADE-->") == 0:
        mark = body.find("<h2>一")
        body = body[:mark] + _papertrade(d) + body[mark:]
    # 黄金版壳 + 当日发布头部 + 动态前四段 + 原样能力模块 + 黄金版页脚。
    page = golden[:wrap_end] + body + "\n" + "\n".join(evo) + "\n" + golden[foot:]

    style_source = current
    if '<style id="overview-evolution-sync">' not in style_source and index_src.exists():
        style_source = index_src.read_text(encoding="utf-8")
    if '<style id="overview-evolution-sync">' not in style_source and ABILITY_FALLBACK is not None:
        style_source = ABILITY_FALLBACK.read_text(encoding="utf-8")
    style = _evolution_style(style_source)
    page = re.sub(r'\n*<!--EVOLUTION_STYLE_SYNC_START-->.*?<!--EVOLUTION_STYLE_SYNC_END-->\n*', "\n", page, flags=re.S)
    page = re.sub(r'<style id="overview-evolution-sync">.*?</style>', "", page, flags=re.S)
    head_pos = page.find("</head>")
    if head_pos < 0: raise RuntimeError("输出 head 缺失")
    page = page[:head_pos] + "\n<!--EVOLUTION_STYLE_SYNC_START-->\n" + style + "\n<!--EVOLUTION_STYLE_SYNC_END-->\n" + page[head_pos:]

    if page.count("<h2>") < 6: raise RuntimeError("输出 h2 不足六段")
    if len(_evolution_sections(page)) != 2: raise RuntimeError("输出能力进化模块不是两组")
    if page.find("<h2>五") < page.find("<h2>四"): raise RuntimeError("龙虎榜段序错位")
    if page.find('<section class="evolution"') <= page.find("<h2>四"): raise RuntimeError("能力进化模块未位于前四段之后")
    if page.count("<div") != page.count("</div>"):
        raise RuntimeError(f"div 不配平: open={page.count('<div')} close={page.count('</div>')}")
    for token in ("FUNDTEMP", "LHBLEDGER"):
        if token not in page: raise RuntimeError("动态必备锚点缺失: " + token)
    if page.count("<!--FUNDTEMP-->") != 1 or page.count("<!--/FUNDTEMP-->") != 1:
        raise RuntimeError("FUNDTEMP 锚点不成对")
    if page.count("<!--LHBLEDGER-->") != 1 or page.count("<!--/LHBLEDGER-->") != 1:
        raise RuntimeError("LHBLEDGER 锚点不成对")
    if "数据边界" in page:
        raise RuntimeError("输出仍含“数据边界”模块：黄金版龙虎榜工程不允许，已阻断发布")
    return page


def main() -> int:
    d = sys.argv[1] if len(sys.argv) > 1 else "20260910"
    if not SOURCE.is_file():
        raise RuntimeError("龙虎榜恢复源页面缺失: " + str(SOURCE))
    current = SOURCE.read_text(encoding="utf-8")
    out = build_page(d, current)
    backup = TARGET.with_name(TARGET.name + f".before_lhb_restore_{d}.bak")
    shutil.copy2(TARGET, backup)
    tmp = TARGET.with_name(TARGET.name + ".lhb_restore_tmp")
    tmp.write_text(out, encoding="utf-8", newline="\n")
    tmp.replace(TARGET)
    print(f"restored {TARGET} bytes={TARGET.stat().st_size}")
    print(f"backup {backup}")
    print(f"h2={len(re.findall(r'<h2>', out))} evolution={len(_evolution_sections(out))}")
    print(f"papertrade={out.count('<!--PAPERTRADE-->')}/{out.count('<!--/PAPERTRADE-->')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
