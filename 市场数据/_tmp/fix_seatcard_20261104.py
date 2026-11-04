# -*- coding: utf-8 -*-
"""把当日 Top5 荐票卡（<!--SEATCARD--> + 表格）从「三 龙虎榜台账」details 内移到 seats 段。

11-03 agent 把当日荐票卡写进了台账 <details> 里，渲染器 artifact('SEATCARD','seats') 替换后
卡片落在台账段，seats 段缺卡 → 栏目内容错位（段数正常，不报错，比 raise 更难发现）。
"""
import json
import shutil
from pathlib import Path

p = Path(r"D:\股票数据\市场数据\_学习\judgment_20261103.json")
bak = p.with_suffix(".json.bak_seatcard_20261104")
if not bak.exists():
    shutil.copy2(p, bak)
    print("备份", bak.name)

with open(p, encoding="utf-8") as f:
    d = json.load(f)
h = d["bodies"]["lhb"]

k = h.find("当日席位路Top5荐票")
assert k > 0, "找不到当日席位路Top5荐票"
pstart = h.rfind("<p ", 0, k)
assert pstart > 0 and k - pstart < 300, (pstart, k)

card = h.find('<div class="card"', k)
assert card > 0, "找不到推荐卡 div"

i = card
depth = 0
while True:
    nxt_open = h.find("<div", i)
    nxt_close = h.find("</div>", i)
    if nxt_close < 0:
        raise SystemExit("未找到 </div>")
    if nxt_open != -1 and nxt_open < nxt_close:
        depth += 1
        i = nxt_open + 4
    else:
        depth -= 1
        i = nxt_close + 6
        if depth == 0:
            break

chunk = h[pstart:i]
print("抽取块长度", len(chunk))
print("块尾", repr(chunk[-60:]))
assert "SEATCARD" in chunk and "景旺电子" in chunk

h2 = h[:pstart] + h[i:]
first_end = h2.find("</section>")
assert first_end > 0
h3 = h2[:first_end] + chunk + h2[first_end:]

d["bodies"]["lhb"] = h3
with open(p, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False)
print("原长", len(h), "-> 新长", len(h3), "差值", len(h3) - len(h))
print("段数", h3.count("<section>"))
