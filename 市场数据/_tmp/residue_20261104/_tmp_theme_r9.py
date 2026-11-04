import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last

print("==== FACT")
print(json.dumps(L(B+"fact_20261030.json"), ensure_ascii=False, indent=1)[:3000])

print("==== 四维")
d=L(B+"_题材四维.json")
print("keys", list(d.keys())[:12] if isinstance(d,dict) else type(d))
if isinstance(d,dict):
    for k in d:
        v=d[k]
        print("--",k, type(v), (list(v.keys())[:10] if isinstance(v,dict) else len(v) if hasattr(v,'__len__') else ''))
