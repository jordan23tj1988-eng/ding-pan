# -*- coding: utf-8 -*-
import sys, os, re
from pathlib import Path
sys.path.insert(0, r"D:/股票数据/市场数据")
import review_pages as RP
m = RP.build_page_model(Path(r"D:/股票数据/市场数据"), "20261023", "limitup")
c = RP._contract()
h = RP._render(m, c)
out = r"D:/股票数据/市场数据/_学习/_tmp_page_limitup_20261023.html"
open(out, "w", encoding="utf-8").write(h)
print("rendered", len(h), "chars")
print("h2 count", len(re.findall(r"<h2", h)))
print("None:", h.count("None"), "null:", h.count("null"), "undefined:", h.count("undefined"))
for kw in ("市场温度", "荐票", "台账", "质量库", "深挖", "认知", "数据边界", "LEDGER"):
    print("  kw", kw, h.count(kw))
