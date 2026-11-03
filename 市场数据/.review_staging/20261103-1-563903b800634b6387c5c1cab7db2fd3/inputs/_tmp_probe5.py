# -*- coding: utf-8 -*-
import json, sys
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
def sk(o, path="", d=0, maxd=3):
    if isinstance(o, dict):
        print(path, "{", list(o.keys())[:25])
        if d<maxd:
            for k in list(o.keys())[:6]:
                sk(o[k], path+"."+str(k), d+1, maxd)
    elif isinstance(o, list):
        print(path, "[len", len(o), "]", (json.dumps(o[0], ensure_ascii=False)[:300] if o else ""))
    else:
        print(path, "=", repr(o)[:200])

for f in ["主流题材6有_20261102.json","题材生命周期_20261102.json","_情绪先行指标.json"]:
    print("\n=========", f)
    o = L(f)
    sk(o, f, 0, 1)
