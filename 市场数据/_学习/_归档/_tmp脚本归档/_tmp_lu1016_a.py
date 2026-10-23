# -*- coding: utf-8 -*-
import json, os, csv, re, io
B = r"D:\股票数据\市场数据\_学习"
M = r"D:\股票数据\市场数据"

def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None

q = load_any(os.path.join(B, "涨停质量荐票_20261016.json"))
print("=== 质量荐票 keys ===", list(q.keys()) if isinstance(q,dict) else type(q))
def peek(o, n=3):
    if isinstance(o, list):
        print(" list len", len(o), "first:", json.dumps(o[0], ensure_ascii=False)[:1500] if o else None)
    elif isinstance(o, dict):
        for k,v in list(o.items())[:12]:
            s = json.dumps(v, ensure_ascii=False) if not isinstance(v,str) else v
            print("  ", k, "=", s[:300])
peek(q)
