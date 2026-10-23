import json, os, csv, io
B = r"D:/股票数据/市场数据"
L = os.path.join(B, "_学习")

def load(p):
    for enc in ("utf-8-sig","utf-8","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f:
                return json.load(f)
        except Exception as e:
            continue
    return None

# summary
p = os.path.join(B, "20261023", "summary.json")
print("=== summary ===")
print(json.dumps(load(p), ensure_ascii=False, indent=1)[:2000])

# zt_pool header + count
p = os.path.join(B, "20261023", "zt_pool.csv")
rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
print("\n=== zt_pool ===", len(rows), "cols:", list(rows[0].keys()))
for r in rows[:3]:
    print({k: r[k] for k in list(r.keys())[:12]})

# temperature
t = load(os.path.join(L, "_市场温度表.json"))
print("\n=== 温度表 type ===", type(t))
if isinstance(t, dict):
    print("keys", list(t.keys())[:10])
    for k in list(t.keys()):
        if "20261023" in str(k) or "20261022" in str(k):
            print(k, json.dumps(t[k], ensure_ascii=False)[:800])
elif isinstance(t, list):
    print(len(t))
    for x in t:
        if str(x.get("日期","")) in ("20261023","20261022"):
            print(json.dumps(x, ensure_ascii=False))
