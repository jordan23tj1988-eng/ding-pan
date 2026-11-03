# -*- coding: utf-8 -*-
import json, collections, io, sys
sys.stdout.reconfigure(encoding='utf-8')
base = "D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p, encoding=enc) as f:
                return json.load(f)
        except Exception as e:
            last=e
    print("LOADFAIL", p, last); return None

gw = L("题材归位_20261102.json")
print("=== 归位 type", type(gw), (list(gw.keys())[:12] if isinstance(gw,dict) else len(gw)))
def keys(o, d=0, maxd=2):
    if isinstance(o, dict):
        print("  "*d, list(o.keys())[:20])
        if d<maxd:
            for k in list(o.keys())[:3]:
                print("  "*d,"->",k); keys(o[k], d+1, maxd)
    elif isinstance(o, list):
        print("  "*d, "list len", len(o), o[0] if o and not isinstance(o[0],(dict,list)) else "")
        if o and isinstance(o[0],dict): keys(o[0], d+1, maxd)
keys(gw)
