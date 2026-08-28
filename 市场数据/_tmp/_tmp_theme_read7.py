# -*- coding: utf-8 -*-
import json
BASE = "D:/股票数据/市场数据"; X = BASE + "/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except FileNotFoundError: return None
        except Exception: continue
    return None
print("======== 规格 10_题材命门agent.md ========")
for enc in ("utf-8-sig","utf-8","gbk"):
    try:
        print(open(BASE+"/_agent规格/10_题材命门agent.md", encoding=enc).read()); break
    except Exception: continue
print("\n======== _认知库_theme.json ========")
print(json.dumps(load(X+"/_认知库_theme.json"), ensure_ascii=False, indent=1)[:9000])
