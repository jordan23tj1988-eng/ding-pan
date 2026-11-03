# -*- coding: utf-8 -*-
import json,sys,csv,collections
sys.stdout.reconfigure(encoding='utf-8')
base="D:/股票数据/市场数据/_学习/"; root="D:/股票数据/市场数据/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p,encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("FAIL",p,last); return None
ths=L("THS涨停池_20261102.json")
print("THS keys/type", type(ths), (list(ths.keys())[:8] if isinstance(ths,dict) else len(ths)))
lst = ths.get('list') or ths.get('data') or ths.get('池') or None
if lst is None and isinstance(ths,dict):
    for k,v in ths.items():
        if isinstance(v,list) and v and isinstance(v[0],dict): lst=v; print("用键",k); break
print("THS 条数", len(lst) if lst else None)
if lst: print(json.dumps(lst[0],ensure_ascii=False)[:400])
codes={str(x.get('code') or x.get('代码')) for x in (lst or [])}
zt={r['代码'] for r in csv.DictReader(open(root+'20261102/zt_pool.csv',encoding='utf-8-sig'))}
gw=L("题材归位_20261102.json"); mp=gw['映射']
ai=[c for c,v in mp.items() if v['大方向']=='AI应用/传媒']
print("AI传媒45 在THS命中:", sum(1 for c in ai if c in codes), "/45 ; zt_pool", len(zt), "THS", len(codes))
print("THS有而zt_pool无:", sorted(codes-zt)[:15])
