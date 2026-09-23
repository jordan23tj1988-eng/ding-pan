# -*- coding: utf-8 -*-
"""能力进化模块.py —— 五路 + 概览共用的两块标准能力模块唯一生产者(2026-09-22)

背景(用户指令: "认知迭代 · 能力进化 / 自主拓展 · 能力进化 这两个能力是每一路,
五路加概览都有的能力, 你现在有的路有, 有的路还没有改过来, 要求你修复")
    旧实现 `生成盯盘台._sync_overview_evolution` 从现站某一路 HTML 里"原样搬运"
    已冻结的模块字节, 结果三处失真:
      ①只有主题页被同步 → 竞价/产业逻辑/涨停页长期缺这两块, 龙虎榜页与旧模块并存重复;
      ②搬来的数字是模板冻结值(自主拓展承接 12 / 认知迭代 235), 与当日能力库脱节;
      ③源不可用时的回退链(现站 cycle/lhb/index)本身也是冻结拷贝, 越搬越旧。
    本模块改为从当日权威能力库直出两块模块, 作为**唯一真源**:
      统计: `_学习/能力进化快照_{d}.json`(只取 ≤d 最近一日, 零后视镜)
      明细: `_学习/能力进化库_自主拓展.json` / `_学习/能力进化库_认知迭代.json`
      产物: `_学习/能力进化模块_{d}.html`(含两块 section + 唯一 CSS, 供门禁与审计复核)
    展示文案/结构/类名与已验收模板逐字一致(不新增自造组件), 只把数字换成当日真值。

纪律: 零编造(缺数据=0 与空提示, 不补造); 零后视镜(快照不得晚于复盘日);
      幂等(同输入同字节); 只依赖 _学习 下的能力库, 不读页面(禁止跨页回灌)。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_ROOT = Path(r"D:/股票数据/市场数据")

# 8 个统计位: (快照字段, 页面文案) —— 顺序与已验收模板逐字一致
STAT_LABELS = (
    ("inherited", "历史承接"),
    ("experiences", "经验/教训/信号"),
    ("capabilities", "已沉淀能力"),
    ("hits", "后续命中"),
    ("validated", "验证成功"),
    ("refuted", "已证伪"),
    ("tracking", "追踪中"),
    ("shelved", "已搁置"),
)
HINT = "发现 → 追踪 → 验证 → 经验 → 能力 → 后续命中"
# 唯一 CSS(与现站 cycle/theme/lhb 已验收模块字节一致; 禁自造类名)
CSS = (
    ".evolution{border-top:1px solid var(--line);padding-top:18px;margin-top:18px}"
    ".evo-stats{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 14px}"
    ".evo-stat{min-width:92px;padding:10px 12px;border:1px solid var(--line);border-radius:9px;"
    "background:rgba(255,255,255,.025)}.evo-stat b{display:block;font-size:20px;color:var(--accent)}"
    ".evo-stat small{color:var(--mut)}.evo-list{display:grid;gap:0;margin-top:10px}"
    ".evo-row{display:grid;grid-template-columns:72px minmax(0,1fr) 250px;gap:12px;padding:11px 0;"
    "border-bottom:1px solid var(--line);line-height:1.55}.evo-row b{color:var(--accent)}"
    ".evo-row span{font-weight:700}.evo-row small{color:var(--mut)}"
    ".evo-empty{padding:14px 0;color:var(--mut);font-size:12px}"
    ".evo-row{grid-template-columns:1fr}.evo-row small{grid-column:1}"
)
EMPTY_TEXT = {
    "自主拓展": "当前没有明确的能力化、后续命中或验证证据；不把未验证记录伪装成结果。",
    "认知迭代": "当前历史资料没有明确的能力化、后续命中或验证证据，暂不计数。",
}
MAX_ROWS = 12
NUMERALS = "一二三四五六七八九十"


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _read_snapshot(root: Path, d: str):
    """只取 <=d 的最近一日快照; 没有就如实返回 None(零后视镜 + 零编造)。"""
    learn = Path(root) / "_学习"
    rows = []
    for path in sorted(learn.glob("能力进化快照_*.json")):
        m = re.fullmatch(r"能力进化快照_(\d{8})\.json", path.name)
        if m and m.group(1) <= d:
            rows.append((m.group(1), path))
    if not rows:
        return None, None
    as_of, path = rows[-1]
    return as_of, _load(path)


def _ledger_records(root: Path, kind: str):
    path = Path(root) / "_学习" / ("能力进化库_%s.json" % kind)
    if not path.is_file():
        return []
    data = _load(path)
    records = data.get("records") if isinstance(data, dict) else data
    return [r for r in (records or []) if isinstance(r, dict)]


def _has_result(record):
    """只算明确验证/证伪/能力化结果；审计日志本身不等于结果。"""
    return bool(
        record.get("capitalized") is True
        or record.get("state") in ("capability", "validated", "refuted")
        or record.get("hit_count") is not None
        or record.get("validation") in ("validated", "refuted")
    )


def _row_html(record):
    validation = record.get("validation") or "待验证"
    hit = record.get("hit_count")
    capital = "是" if record.get("capitalized") is True else "—"
    return (
        '<div class="evo-row"><b>%s</b><span>%s</span><small>验证：%s · 命中：%s · 资金化：%s</small></div>'
        % (_esc(record.get("route", "—")), _esc(record.get("title") or record.get("body") or "—"),
           _esc(validation), _esc("—" if hit is None else hit), capital)
    )


def _panel_html(title, stats, records):
    pills = "".join(
        '<span class="evo-stat"><b>%s</b><small>%s</small></span>' % (stats.get(key, 0), label)
        for key, label in STAT_LABELS
    )
    ordered = sorted(records, key=lambda r: str(r.get("date") or r.get("discovered_at") or ""),
                     reverse=True)
    rows = [_row_html(r) for r in ordered if _has_result(r)]
    shown = rows[:MAX_ROWS]
    if len(rows) > len(shown):
        shown.append('<div class="evo-empty">另有 %d 条有结果记录未在本页展开（全量见 _学习/能力进化库）。</div>'
                     % (len(rows) - len(shown)))
    body = "".join(shown) or '<div class="evo-empty">%s</div>' % EMPTY_TEXT[title]
    return (
        '<section class="evolution"><h2>%s · 能力进化<span class="hint">%s</span></h2>'
        '<div class="evo-stats">%s</div>'
        '<details open><summary>已沉淀与验证明细 <span class="chip">%d条有结果记录</span></summary>'
        '<div class="evo-list">%s</div></details></section>'
        % (title, HINT, pills, len(rows), body)
    )


def build(root, d):
    """产出当日两块标准能力模块(未编号) + CSS + 溯源信息。"""
    root = Path(root)
    if not re.fullmatch(r"\d{8}", str(d)):
        raise ValueError("date must be YYYYMMDD: %r" % (d,))
    as_of, snapshot = _read_snapshot(root, d)
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    stats = {}
    for key, title in (("自主拓展", "自主拓展"), ("认知迭代", "认知迭代")):
        block = snapshot.get(key)
        stats[key] = block if isinstance(block, dict) else {}
    ext_records = _ledger_records(root, "自主拓展")
    cog_records = _ledger_records(root, "认知迭代")
    sections = [
        _panel_html("自主拓展", stats["自主拓展"], ext_records),
        _panel_html("认知迭代", stats["认知迭代"], cog_records),
    ]
    return {
        "d": d,
        "as_of": as_of,
        "source": {
            "snapshot": ("_学习/能力进化快照_%s.json" % as_of) if as_of else None,
            "自主拓展": "_学习/能力进化库_自主拓展.json",
            "认知迭代": "_学习/能力进化库_认知迭代.json",
        },
        "stats": stats,
        "css": CSS,
        "sections": sections,
        "html": "\n".join(sections),
    }


def renumber(section_html, n):
    """把标题序号写成第 n 段(按目标页自身段数顺延, 防重复编号)。"""
    numeral = NUMERALS[n - 1] if 1 <= n <= len(NUMERALS) else str(n)
    fixed = re.sub(r"<h2>(?:[一二三四五六七八九十]+\s*)?(自主拓展|认知迭代)",
                   lambda m: "<h2>%s %s" % (numeral, m.group(1)), section_html, count=1)
    if ("<h2>%s " % numeral) not in fixed:
        raise RuntimeError("能力模块编号失败: n=%d" % n)
    return fixed


def renumbered(root, d, start):
    """构建并把两块模块编号为 start / start+1。"""
    payload = build(root, d)
    payload["sections"] = [renumber(sec, start + i) for i, sec in enumerate(payload["sections"])]
    payload["html"] = "\n".join(payload["sections"])
    payload["start"] = start
    return payload


def artifact_text(payload):
    """当日产物: 两块模块(带编号) + 唯一 CSS, 供门禁/审计直接复读。"""
    return (
        "<!-- 能力进化模块 (五路+概览共用唯一真源) d=%s as_of=%s -->\n"
        "<style id=\"overview-evolution-sync\">%s</style>\n%s\n"
        % (payload["d"], payload.get("as_of") or "—", payload["css"], payload["html"])
    )


def write_artifact(root, payload):
    path = Path(root) / "_学习" / ("能力进化模块_%s.html" % payload["d"])
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(artifact_text(payload), encoding="utf-8", newline="\n")
    tmp.replace(path)
    return path


def summary(payload):
    out = {"d": payload["d"], "as_of": payload.get("as_of"), "start": payload.get("start"),
           "source": payload["source"], "stats": payload["stats"],
           "sections": len(payload["sections"]), "bytes": len(payload["html"])}
    return out


STYLE_ID = "overview-evolution-sync"
SYNC_START = "<!--OVERVIEW_EVOLUTION_SYNC_START-->"
SYNC_END = "<!--OVERVIEW_EVOLUTION_SYNC_END-->"
# 五路 + 概览 (canonical 顺序; 门禁/哨兵/生成器都用这一份)
ROUTES = ("index", "cycle", "auction", "lhb", "theme", "logic", "limitup")
# 各页"业务段"数(不含两块标准能力模块); 与页面实际段数不符 = 编号漂移, 必须报错
BUSINESS_SECTIONS = {"index": 4, "cycle": 5, "auction": 4, "lhb": 4,
                     "theme": 3, "logic": 5, "limitup": 4}
# 展示层历史模块标题(自主深挖/我的认知迭代); 内容在判断层与能力库, 展示层只留两块标准模块
LEGACY_RE = re.compile(r"自主深挖|我的认知迭代|认知迭代")
FOOT_ANCHOR = '<div class="foot">'


def legacy_headings(html):
    """展示层历史模块标题(已排除两块标准能力模块)。"""
    body = re.sub(r'<section class="evolution">.*?</section>', "", html, flags=re.S)
    out = []
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", body, re.S):
        text = re.sub(r"<[^>]+>", "", m.group(1))
        if LEGACY_RE.search(text):
            out.append(text.strip())
    return out


def _h2_numerals(html):
    return [NUMERALS.index(x) + 1 for x in re.findall(r"<h2[^>]*>\s*([一二三四五六七八九十])\s", html)]


def verify_page(html, route, root=None, d=None):
    """校验一页的两块标准能力模块是否符合契约; 返回问题列表(空=通过)。

    单一契约实现: 生成链自检、发布门禁(review_publish)、现站哨兵(复盘一致性哨兵)共用。
    route/root/d 给全时追加"与该路唯一真源逐字节一致"的比对。
    """
    problems = []
    if route not in BUSINESS_SECTIONS:
        return ["unknown route: %s" % route]
    expected = BUSINESS_SECTIONS[route]
    count = html.count('<section class="evolution">')
    if count != 2:
        problems.append("能力模块数量!=2 (%d)" % count)
    if html.count(SYNC_START) != 1 or html.count(SYNC_END) != 1:
        problems.append("同步锚点不唯一 (start=%d end=%d)" % (html.count(SYNC_START), html.count(SYNC_END)))
    if len(re.findall(r'<style\b[^>]*\bid=["\']%s["\']' % STYLE_ID, html, flags=re.I)) != 1:
        problems.append("能力模块样式不唯一/缺失 (id=%s)" % STYLE_ID)
    if "evolution-style-sync" in html:
        problems.append("残留旧样式 id=evolution-style-sync")
    left = legacy_headings(html)
    if left:
        problems.append("残留旧模块标题: %s" % " / ".join(left))
    blocks = re.findall(r'<section class="evolution">.*?</section>', html, re.S)
    if len(blocks) == 2:
        if blocks[0].find("自主拓展") < 0 or blocks[1].find("认知迭代") < 0:
            problems.append("两块模块顺序错(应先自主拓展后认知迭代)")
        if FOOT_ANCHOR in html and html.index(blocks[0]) > html.rindex(FOOT_ANCHOR):
            problems.append("能力模块位置在页脚之后")
        want = [NUMERALS[expected], NUMERALS[expected + 1]]
        got = []
        for sec in blocks:
            m = re.search(r"<h2>\s*([一二三四五六七八九十])?\s*(自主拓展|认知迭代)", sec)
            got.append((m.group(1) or "") if m else "")
        if got != want:
            problems.append("模块编号不符 (got=%s want=%s)" % (got, want))
    nums = _h2_numerals(html)
    if nums:
        business = [n for n in nums if n <= expected]
        if not business or max(business) != expected:
            problems.append("页面业务段数与契约不符 (max=%s expect=%d)" % (max(business) if business else None, expected))
    else:
        problems.append("页面无编号段落")
    if root is not None and d is not None and len(blocks) == 2:
        want_sections = canonical_sections(root, d, route)
        if blocks != want_sections:
            problems.append("能力模块字节与当日唯一真源不一致")
    return problems


def canonical_sections(root, d, route):
    """该路当日的两块标准模块(按该路段数编号)——门禁比对基准。"""
    if route not in BUSINESS_SECTIONS:
        raise ValueError("unknown route: %s" % route)
    payload = build(root, d)
    start = BUSINESS_SECTIONS[route] + 1
    return [renumber(sec, start + i) for i, sec in enumerate(payload["sections"])]


def main(argv=None):
    ap = argparse.ArgumentParser(description="五路+概览标准能力模块唯一生产者")
    ap.add_argument("d", help="复盘日 YYYYMMDD")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--start", type=int, default=1, help="起始段序号(默认1, 不编号)")
    ap.add_argument("--no-artifact", action="store_true", help="只打印不落盘")
    args = ap.parse_args(argv)
    payload = renumbered(args.root, args.d, args.start)
    if not args.no_artifact:
        path = write_artifact(args.root, payload)
        print(str(path), file=sys.stderr)
    print(json.dumps(summary(payload), ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
