# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def rd(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)
B = 'D:/股票数据/市场数据/_学习/'

print("===== 总审_20261015 指派清单 =====")
zs = rd(B+'总审_20261015.json')
print("TOP KEYS:", list(zs.keys()))
idx = zs.get('指派清单')
print("指派清单 type:", type(idx))
print(json.dumps(idx, ensure_ascii=False, indent=1)[:6000])
