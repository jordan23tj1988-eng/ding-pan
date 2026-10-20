# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def rd(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

B = 'D:/股票数据/市场数据/_学习/'

print("===== 风险日历_20261016 =====")
print(json.dumps(rd(B+'风险日历_20261016.json'), ensure_ascii=False, indent=1)[:3000])

print("\n===== 风险事件_20261016 (keys + metrics) =====")
re16 = rd(B+'风险事件_20261016.json')
print("TOP KEYS:", list(re16.keys()))
for k,v in re16.items():
    if k != '事件' and not isinstance(v,(list,dict)):
        print(k, "=", v)
    elif isinstance(v, dict):
        print(k, "-> dict keys:", list(v.keys())[:20])
        print("   ", json.dumps(v, ensure_ascii=False)[:2500])
print("事件 count:", len(re16.get('事件',[])))
print("事件 sample[0..2]:")
for e in re16.get('事件',[])[:3]:
    print("  ", json.dumps(e, ensure_ascii=False))

print("\n===== 能力预加载_20261016 =====")
cap = rd(B+'能力预加载_20261016.json')
print(json.dumps(cap, ensure_ascii=False, indent=1)[:4000])
