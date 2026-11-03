# -*- coding: utf-8 -*-
"""lhb body 段结构归并：7 段 -> 黄金版 4 业务段 + 2 标准能力段位置。
只改 h2/h3 标题层级与编号，正文一字不删。"""
import json, re, shutil, sys, pathlib

BASE = pathlib.Path(r"D:\股票数据\市场数据")
BODY = BASE / "_学习" / "lhb_body_20261102.html"
JUDG = BASE / "_学习" / "judgment_20261102.json"

MAP = [
    ("h2", "一 席位综合判断"),
    ("h3", "训练库 · 净买占比因子（能力在用）"),
    ("h2", "二 席位荐票 · 今日 0 只（空仓）"),
    ("h2", "三 资金温度与席位结构"),
    ("h2", "四 龙虎榜台账 · 席位量化扫描"),
    ("h2", "五 自主深挖 · 承接 MA-20261030-01 三项"),
    ("h2", "六 我的认知迭代"),
]


def fix(html):
    counter = [0]

    def rep(m):
        k = counter[0]
        counter[0] += 1
        if k >= len(MAP):
            return m.group(0)
        tag, title = MAP[k]
        inner = m.group(1)
        span = re.search(r'<span class="mut">.*?</span>', inner, re.S)
        new_inner = title + (" " + span.group(0) if span else "")
        if tag == "h3":
            attrs = m.group(0)[3: m.group(0).find(">")]  # h2 的属性原样带过去
            return "<h3" + attrs + ">" + new_inner + "</h3>"
        return "<h2" + m.group(0)[3: m.group(0).find(">")] + ">" + new_inner + "</h2>"

    out = re.sub(r"<h2[^>]*>(.*?)</h2>", rep, html, flags=re.S)
    return out


def verify(name, html):
    h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)
    titles = [re.sub(r"<[^>]+>", "", h).strip() for h in h2]
    ok = len(h2) == 6 and titles[0][:1] == "一" and titles[-1].startswith("六")
    print(name, "h2数=", len(h2), "|", [t[:14] for t in titles])
    print("   h3训练库:", "训练库" in "".join(re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.S)))
    print("   section配平:", html.count("<section") == html.count("</section>"))
    return ok


body = BODY.read_text(encoding="utf-8")
judg = json.loads(JUDG.read_text(encoding="utf-8"))
old_lhb = judg["bodies"]["lhb"]

new_body = fix(body)
new_lhb = fix(old_lhb)

ok1 = verify("body文件", new_body)
ok2 = verify("judgment.bodies.lhb", new_lhb)
if not (ok1 and ok2):
    print("校验失败，不动文件")
    sys.exit(1)

shutil.copy(BODY, str(BODY) + ".bak_merge7to4_20261102")
shutil.copy(JUDG, str(JUDG) + ".bak_merge7to4_20261102")
BODY.write_text(new_body, encoding="utf-8", newline="\n")
judg["bodies"]["lhb"] = new_lhb
with JUDG.open("w", encoding="utf-8", newline="\n") as fh:
    json.dump(judg, fh, ensure_ascii=False, indent=1)
print("已写回（正文长度 body %d -> %d, judgment %d -> %d）" % (len(body), len(new_body), len(old_lhb), len(new_lhb)))
