import json, os
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try:
            return json.load(open(p,encoding=enc))
        except Exception as e:
            last=e
    raise last

p = B+"子agent增强/战绩画像_theme_20261030.json"
d=L(p)
print("KEYS", list(d.keys()))
for k,v in d.items():
    if k=="按日":
        print("按日 n=", len(v))
        for r in v[-8:]:
            print("  ", json.dumps(r,ensure_ascii=False))
        continue
    print(f"--- {k}:", json.dumps(v, ensure_ascii=False)[:2500])
