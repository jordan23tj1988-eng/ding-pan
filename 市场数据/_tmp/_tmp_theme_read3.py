# -*- coding: utf-8 -*-
import json, os, csv
BASE = "D:/股票数据/市场数据"; X = BASE + "/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except FileNotFoundError: return None
        except Exception: continue
    return None

print("#### 题材归位_20260826 结构")
gw = load(X+"/题材归位_20260826.json")
print("type", type(gw), "keys" , list(gw.keys())[:20] if isinstance(gw,dict) else len(gw))
print(json.dumps(gw, ensure_ascii=False, indent=1)[:6000])
