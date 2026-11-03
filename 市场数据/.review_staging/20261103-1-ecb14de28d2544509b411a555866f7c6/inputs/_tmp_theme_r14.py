import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d=L(B+"总审_20261029.json")
print("TOP", list(d.keys()))
for k,v in d.items():
    s=json.dumps(v, ensure_ascii=False)
    if "指派" in k or "指派" in s[:200]:
        print(f"===== [{k}]")
        print(json.dumps(v, ensure_ascii=False, indent=1)[:4000])
