# -*- coding: utf-8 -*-
import json, os
from pathlib import Path
L = r"D:/股票数据/市场数据/_学习"
p = os.path.join(L, "limitup判断_20261023.json")
d = json.load(open(p, encoding="utf-8"))
one = d.pop("一句话", "")
if one:
    nd = {}
    for k, v in d.items():
        nd[k] = v
        if k == "路":
            nd["一句话"] = one  # 仍在判断内? 不: 顶层不允许
    # 顶层白名单: 日期/路/来源/判断/荐票/认知迭代/深挖/独立盲区声明/验证注记/schema_version
    nd.pop("一句话", None)
    d = nd
d["判断"] = dict([("一句话", one)] + list(d["判断"].items())) if one else d["判断"]
d["schema_version"] = 1
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("top keys:", list(d.keys()))
print("判断 keys:", list(d["判断"].keys())[:6])
print("bytes", os.path.getsize(p))

# 渲染试跑
import sys
sys.path.insert(0, r"D:/股票数据/市场数据")
from review_pages import build_page_model
try:
    m = build_page_model(Path(r"D:/股票数据/市场数据"), "20261023", "limitup")
    print("RENDER OK route=", m.get("route"), "sections=", [s["id"] for s in m["sections"]])
    print("claims=", len(m["claims"]), "hero=", (m.get("hero") or {}).get("text","")[:60])
    print("sources=", m.get("sources"))
    print("limitations=", len(m.get("limitations") or []))
except Exception as e:
    import traceback; traceback.print_exc()
