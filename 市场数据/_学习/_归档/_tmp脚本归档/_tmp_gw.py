# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
g = json.load(open(os.path.join(L,"题材归位_20261023.json"), encoding="utf-8"))
print("keys:", list(g.keys()))
print("counts:", json.dumps(g.get("counts"), ensure_ascii=False))
for k in ("A","B","C"):
    v = g.get(k)
    if isinstance(v, list):
        print(k, "len", len(v), "sample:", json.dumps(v[0], ensure_ascii=False)[:400])
    elif isinstance(v, dict):
        print(k, "dict keys", list(v.keys())[:10], json.dumps(v, ensure_ascii=False)[:600])
print("口径:", str(g.get("口径"))[:300])
print("source_status:", g.get("source_status"), "missing:", g.get("missing_fields"))
