# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
base = "D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p, encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("LOADFAIL", p, last); return None
st = L("_模拟盘/theme/状态.json")
print("=== 状态.json ===")
print(json.dumps(st, ensure_ascii=False)[:4000])
cap = L("能力预加载_20261102.json")
print("\n=== 能力预加载 theme ===")
print(json.dumps(cap.get('routes',{}).get('theme') if isinstance(cap,dict) else None, ensure_ascii=False)[:2000])
print("\n=== 能力预加载 top keys ===", list(cap.keys()) if isinstance(cap,dict) else type(cap))
