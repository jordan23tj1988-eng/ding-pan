# -*- coding: utf-8 -*-
import json, os
L = r"D:/股票数据/市场数据/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None

for nm, fn in [("题材归位","题材归位_20261023.json"), ("开盘验证维","开盘验证维_20261023.json")]:
    d = load(os.path.join(L, fn))
    print("\n=== %s ===" % nm, type(d))
    print(json.dumps(d, ensure_ascii=False, indent=1)[:2500])

print("\n=== 认知库_limitup ===")
d = load(os.path.join(L, "_认知库_limitup.json"))
print(json.dumps(d, ensure_ascii=False, indent=1)[:3000])

print("\n=== 战绩画像_limitup ===")
d = load(os.path.join(L, "子agent增强", "战绩画像_limitup_20261023.json"))
print(json.dumps(d, ensure_ascii=False, indent=1)[:3000])

print("\n=== 反思jsonl 末2行 ===")
lines = open(os.path.join(L,"_涨停质量反思.jsonl"), encoding="utf-8").read().strip().split("\n")
for ln in lines[-2:]:
    print(json.dumps(json.loads(ln), ensure_ascii=False, indent=1)[:2500])
