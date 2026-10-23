# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
t = json.load(open(os.path.join(L,"_市场温度表.json"), encoding="utf-8"))
for d in ("20261022","20261023"):
    v = t.get(d) if isinstance(t, dict) else None
    if isinstance(v, dict):
        keep = {k: v[k] for k in list(v)[:12]}
        print("温度", d, json.dumps(keep, ensure_ascii=False)[:400])
x = json.load(open(os.path.join(L,"_情绪先行指标.json"), encoding="utf-8"))
for d in ("20261022","20261023"):
    v = x.get(d)
    print("\n先行", d, json.dumps(v, ensure_ascii=False)[:900] if v else None)
q = json.load(open(os.path.join(L,"涨停质量荐票_20261023.json"), encoding="utf-8"))
print("\n荐票 keys:", list(q.keys()))
print("top5:", json.dumps(q.get("top5"), ensure_ascii=False)[:900])
print("活跃因子:", json.dumps(q.get("活跃因子"), ensure_ascii=False)[:400])
print("规则:", json.dumps(q.get("规则"), ensure_ascii=False)[:400] if "规则" in q else "")
k = json.load(open(os.path.join(L,"_涨停质量库.json"), encoding="utf-8"))
print("\n质量库 keys:", list(k.keys())[:12])
print("基准:", json.dumps(k.get("基准"), ensure_ascii=False)[:400])
print("因子:", json.dumps(k.get("因子"), ensure_ascii=False)[:600])
