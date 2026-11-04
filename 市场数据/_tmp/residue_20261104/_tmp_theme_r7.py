import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d = L(B+"题材归位_20261030.json")
print("TOP", list(d.keys()))
for k in d:
    if k not in ("映射",):
        print(f"[{k}]", json.dumps(d[k], ensure_ascii=False)[:1500])
m = d["映射"]
print("映射 n=", len(m))
for code,v in m.items():
    print(code, json.dumps(v, ensure_ascii=False))
