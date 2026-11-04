# -*- coding: utf-8 -*-
"""把 LHBLEDGER 锚点对从被剥掉的旧认知段，搬回到 三 龙虎榜台账 段内（对齐 10/30 黄金壳位置）。
只动注释锚点，不改任何业务文字。"""
import json, re, shutil, sys, pathlib

BASE = pathlib.Path(r"D:\股票数据\市场数据")
L = BASE / "_学习"
JUDG = L / "judgment_20261102.json"
H2 = "<h2>三 龙虎榜台账 · 席位量化扫描</h2>"


def fix(html):
    # 1) 清掉所有既有 LHBLEDGER 锚点（可能散落在被剥掉的旧段里）
    html = re.sub(r"<!--LHBLEDGER-->\s*<!--/LHBLEDGER-->", "", html)
    html = html.replace("<!--LHBLEDGER-->", "").replace("<!--/LHBLEDGER-->", "")
    if "LHBLEDGER" in html:
        raise SystemExit("残留锚点，人工检查")
    # 2) 在台账段内重建锚点对
    i = html.find(H2)
    if i < 0:
        raise SystemExit("台账 h2 未找到")
    body_start = i + len(H2)
    end = html.find("</section>", body_start)
    if end < 0:
        raise SystemExit("台账 section 结束未找到")
    return html[:body_start] + "\n<!--LHBLEDGER-->".replace("\n", "\n\n", 1) + html[body_start:end] + "\n<!--/LHBLEDGER-->\n" + html[end:]


def verify(name, html):
    ok_start = html.count("<!--LHBLEDGER-->") == 1
    ok_end = html.count("<!--/LHBLEDGER-->") == 1
    i = html.find("<!--LHBLEDGER-->")
    inside = html.find(H2) < i < html.find("</section>", html.find(H2))
    print(name, "start=%d end=%d 在台账段内=%s" % (html.count("<!--LHBLEDGER-->"), html.count("<!--/LHBLEDGER-->"), inside))
    return ok_start and ok_end and inside


judg = json.loads(JUDG.read_text(encoding="utf-8"))
bp = L / "lhb_body_20261102.html"
body = bp.read_text(encoding="utf-8")
nb = fix(body)
nj = fix(judg["bodies"]["lhb"])
if not (verify("body", nb) and verify("judgment", nj)):
    sys.exit("校验失败，未写")
shutil.copy(bp, str(bp) + ".bak_ledgeranchor_20261102")
bp.write_text(nb, encoding="utf-8", newline="\n")
judg["bodies"]["lhb"] = nj
with JUDG.open("w", encoding="utf-8", newline="\n") as fh:
    json.dump(judg, fh, ensure_ascii=False, indent=1)
print("已写回")
