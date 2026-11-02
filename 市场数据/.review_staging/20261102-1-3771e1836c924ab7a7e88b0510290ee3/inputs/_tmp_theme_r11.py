import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d=L(B+"涨停对链条_20261030.json")
print("TOP", list(d.keys()))
for k in d:
    if k in ("链条","逐线","题材"): 
        print(k, type(d[k]))
        continue
    print(f"[{k}]", json.dumps(d[k], ensure_ascii=False)[:1200])
