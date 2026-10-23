# -*- coding: utf-8 -*-
import json, os, sys
from pathlib import Path
L = r"D:/股票数据/市场数据/_学习"
p = os.path.join(L, "limitup判断_20261023.json")
d = json.load(open(p, encoding="utf-8"))
blind = d["判断"].pop("独立盲区声明", None)
if blind: d["独立盲区声明"] = blind
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("top keys:", list(d.keys()), "bytes", os.path.getsize(p))
print("判断 keys:", list(d["判断"].keys()))

sys.path.insert(0, r"D:/股票数据/市场数据")
import review_pages as RP
m = RP.build_page_model(Path(r"D:/股票数据/市场数据"), "20261023", "limitup")
from collections import Counter
print("claims", len(m["claims"]), Counter(c["role"] for c in m["claims"]))
print("sections", Counter(c["section"] for c in m["claims"]))
print("hero", (m.get("hero") or {}).get("text","")[:50])
cands = [n for n in dir(RP) if "render" in n.lower() or "page" in n.lower()]
print("render fn candidates:", cands)
