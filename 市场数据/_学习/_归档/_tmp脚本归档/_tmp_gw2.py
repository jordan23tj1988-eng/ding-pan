# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
g = json.load(open(os.path.join(L,"题材归位_20261023.json"), encoding="utf-8"))
print("档计数:", json.dumps(g.get("档计数"), ensure_ascii=False))
print("\n方向聚合:", json.dumps(g.get("方向聚合"), ensure_ascii=False)[:1200])
print("\nA:", json.dumps(g.get("A"), ensure_ascii=False)[:500])
print("\nB:", json.dumps(g.get("B"), ensure_ascii=False)[:800])
print("\nC:", json.dumps(g.get("C"), ensure_ascii=False)[:500])
m = g.get("映射")
print("\n映射 type", type(m), len(m) if hasattr(m,'__len__') else '')
items = m.items() if isinstance(m, dict) else enumerate(m)
for i,(k,v) in enumerate(items):
    if i < 4: print(" ", k, json.dumps(v, ensure_ascii=False)[:300])
for code in ("002724","603278","003021","301502","000678","688836"):
    v = m.get(code) if isinstance(m, dict) else None
    print(" *", code, json.dumps(v, ensure_ascii=False)[:300])
