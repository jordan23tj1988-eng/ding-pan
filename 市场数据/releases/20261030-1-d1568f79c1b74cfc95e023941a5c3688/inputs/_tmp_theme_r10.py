import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d=L(B+"_题材四维.json")
for day in ("20261028","20261029","20261030"):
    print("="*12, day)
    for k,v in d[day].items():
        print(" ", k, json.dumps(v, ensure_ascii=False))
