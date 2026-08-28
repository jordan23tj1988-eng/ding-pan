# -*- coding: utf-8 -*-
import json, os
BASE = "D:/股票数据/市场数据"; X = BASE + "/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except FileNotFoundError: return None
        except Exception: continue
    return None
def P(t,o):
    print("\n"+"="*70); print("### "+t); print("="*70)
    print(json.dumps(o, ensure_ascii=False, indent=1))

P("6有_20260826", load(X+"/主流题材6有_20260826.json"))
P("生命周期_20260826", load(X+"/题材生命周期_20260826.json"))
