import json, os
base = r"D:\股票数据\市场数据"
p = os.path.join(base, "_学习", "_情绪先行指标.json")
d = json.load(open(p, encoding="utf-8"))
print("TYPE", type(d).__name__, "LEN", len(d))
ks = sorted(d.keys()) if isinstance(d, dict) else []
print("KEYS", ks[-6:])
last = ks[-1] if ks else None
v = d.get(last)
print("LAST", last, "type", type(v).__name__)
print(json.dumps(v, ensure_ascii=False)[:1200])
