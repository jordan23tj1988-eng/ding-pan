# -*- coding: utf-8 -*-
"""撤销 #250 ①（index body 改动）。

原因（实测更正）：index 页面渲染走 GOLDEN_INDEX 黄金骨架（`module_golden_index.build`），
`review_pages.render_page` 对 golden 段直接 `body += golden_bodies[s['id']]`，**根本不读
judgment 的 bodies.index**。页面上两个「二 拐点预警」经查是：①`<aside class="rail">` 内
IDXLEAD 卡片自带的可见标题 ②`<section id="turning" hidden aria-hidden="true">` 结构门禁用
的隐藏段头 —— 后者不可见，页面无视觉重复。之前的 grep 把隐藏段也数进来了，属误判。

保留：auction/logic 的「五 深挖」→「五 自主深挖」（真修，body 层合规）。
"""
import json
import shutil
from pathlib import Path

L = Path(r"D:\股票数据\市场数据\_学习")
p = L / "judgment_20261103.json"
bak = L / "judgment_20261103.json.bak_next_20261104"
cur = json.load(open(p, encoding="utf-8"))
old = json.load(open(bak, encoding="utf-8"))
cur["bodies"]["index"] = old["bodies"]["index"]
shutil.copy2(p, L / "judgment_20261103.json.bak_before_index_rollback")
with open(p, "w", encoding="utf-8") as f:
    json.dump(cur, f, ensure_ascii=False)
print("index body 已回滚:", len(cur["bodies"]["index"]), "字符")
print("auction 措辞保持:", "五 自主深挖" in cur["bodies"]["auction"])
print("logic   措辞保持:", "五 自主深挖" in cur["bodies"]["logic"])
