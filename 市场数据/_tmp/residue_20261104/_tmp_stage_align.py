# -*- coding: utf-8 -*-
"""把 logic / lhb 的 body 段归位到页面契约语义（黄金版段标题口径）。
原则：正文一字不删，只改 h2 标签词/层级，并补两段“机器读数/原文搬运”段填空段。
"""
import json, re, shutil, sys, pathlib

BASE = pathlib.Path(r"D:\股票数据\市场数据")
L = BASE / "_学习"
JUDG = L / "judgment_20261102.json"

# ---------- logic ----------
LOGIC_ADD_HARDNESS = """<section>
<h2>四 逻辑硬度 · 消息溯源<span class="hint">机器段：原文搬运自 _学习/logic判断_20261102.json#判断.结论（agent 原文，未经改写，不新增判断）</span></h2>
<p>硬度分级（原文摘录）：125 只涨停按三同口径（净利同比&gt;0 且 归母净利&gt;0 且 营收同比&gt;0）分为 真增长 47 只＝37.6% / 减亏假阳 14 只＝11.2%（同比转正但归母仍亏） / 净利同比≤0 共 64 只＝51.2%；带订单·扩产·涨价级产业证据的只有 3 只（688596 正帆科技「新签订单」、688376 美埃科技「海外扩产」、605288 凯迪股份「送样」且亏损）。本段为原文搬运，判断归属 logic 路 20261102，宿主未改写。</p>
</section>

"""

LOGIC_ADD_FORWARD = """<section>
<h2>五 前置预期雷达 · 风险日历踩窗<span class="hint">机器段：源 _学习/风险日历_20261102.json（status=pass）· 只呈现已接入维度，不把缺事件解释成无风险</span></h2>
<p>风险日历读数：事件 575 条；已接入维度 限售解禁 / 分红除权 / 股东减持 / 高管减持；未接入维度 财报披露日历 / 股东大会 / 业绩预告 —— 缺事件≠无风险，不得据此声称无此类风险。事件源状态 pass，覆盖交易日 20261102。</p>
</section>

"""

LOGIC_MAP = [
    ("二 产业逻辑·业绩腿命门", "二 中报季报 · 业绩腿三同口径"),
    ("三 产业逻辑判断", "三 链条纵深与环节卡位"),
    ("四 荐票与深挖", "六 荐票与深挖"),
    ("五 认知迭代", "七 认知迭代"),
]

# ---------- lhb ----------
LHB_ADD_TIERS = """<section>
<h2>四 全市场席位分档库<span class="hint">机器段：源 _学习/_席位分档.json（更新 20261102，窗口 20260401~20261030）+ SEATLIB 组件直出表</span></h2>
<p>分档库读数：有效笔 19956、在库席位 472；档分布 S16 / A45 / B144 / C90 / P177；全体执1 基准胜率 48.6%、均涨 0.63%（收缩 K=10，n&lt;25 标小样本）。口径：一笔＝席位净买&gt;0 且买额≥1000万；执1＝T+1 开买→T+1 收；零后视镜；每晚重算、掉档自动净化。本段为机器读数，非 LLM 判断。</p>
</section>

"""


def replace_label(html, old, new):
    pat = re.compile(r"<h2>(\s*)" + re.escape(old))
    n = len(pat.findall(html))
    if n != 1:
        raise SystemExit("label 命中数异常 %s -> %s : %d" % (old, new, n))
    return pat.sub(lambda m: "<h2>" + m.group(1) + new, html, count=1)


def insert_before_h2(html, anchor_label, block):
    i = html.find("<h2>" + anchor_label)
    if i < 0:
        raise SystemExit("锚点未找到: " + anchor_label)
    s = html.rfind("<section", 0, i)
    if s < 0:
        raise SystemExit("锚点无 section: " + anchor_label)
    return html[:s] + block + html[s:]


def to_h3(html, label):
    old = "<h2>" + label + "</h2>"
    if html.count(old) != 1:
        raise SystemExit("h3 转换命中异常: " + label + " count=%d" % html.count(old))
    return html.replace(old, "<h3>" + label + "</h3>")


def fix_logic(html):
    for old, new in LOGIC_MAP:
        html = replace_label(html, old, new)
    html = insert_before_h2(html, "六 荐票与深挖", LOGIC_ADD_HARDNESS + LOGIC_ADD_FORWARD)
    return html


def fix_lhb(html):
    html = to_h3(html, "二 席位荐票 · 今日 0 只（空仓）")
    html = replace_label(html, "三 资金温度与席位结构", "二 资金温度与席位结构")
    html = replace_label(html, "四 龙虎榜台账 · 席位量化扫描", "三 龙虎榜台账 · 席位量化扫描")
    html = insert_before_h2(html, "五 自主深挖", LHB_ADD_TIERS)
    return html


def report(name, html, expect):
    hs = [re.sub(r"<[^>]+>", "", m).strip() for m in re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)]
    labels = [re.match(r"[一二三四五六七八九]", h).group(0) if re.match(r"[一二三四五六七八九]", h) else "?" for h in hs]
    print(name, "h2=%d" % len(hs), labels)
    for h in hs:
        print("    ", h[:34])
    print("    section 配平:", html.count("<section") == html.count("</section>"))
    return len(hs) == expect


judg = json.loads(JUDG.read_text(encoding="utf-8"))
bak = JUDG.with_suffix(".json.bak_stagealign_20261102")
if not bak.exists():
    shutil.copy(JUDG, bak)

ok = True
for route, fn, expect in (("logic", fix_logic, 7), ("lhb", fix_lhb, 6)):
    body_path = L / ("%s_body_20261102.html" % route)
    body = body_path.read_text(encoding="utf-8")
    new = fn(body)
    ok &= report(route + " body文件", new, expect)
    jb = judg["bodies"][route]
    jnew = fn(jb)
    ok &= report(route + " judgment", jnew, expect)
    if not ok:
        raise SystemExit("校验失败，未写文件")
    shutil.copy(body_path, str(body_path) + ".bak_stagealign_20261102")
    body_path.write_text(new, encoding="utf-8", newline="\n")
    judg["bodies"][route] = jnew

with JUDG.open("w", encoding="utf-8", newline="\n") as fh:
    json.dump(judg, fh, ensure_ascii=False, indent=1)
print("写回完成")
