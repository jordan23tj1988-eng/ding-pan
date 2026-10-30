import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d = L(B+"题材生命周期_20261030.json")
print("TOP KEYS", list(d.keys()) if isinstance(d,dict) else type(d))
print(json.dumps(d, ensure_ascii=False)[:6000])
