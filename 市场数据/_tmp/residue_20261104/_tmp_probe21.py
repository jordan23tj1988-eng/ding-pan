# -*- coding: utf-8 -*-
import json,sys,csv
sys.stdout.reconfigure(encoding='utf-8')
base="D:/股票数据/市场数据/_学习/"; root="D:/股票数据/市场数据/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p,encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("FAIL",p,last); return None
lst=L("THS涨停池_20261102.json")
print("THS 条数", len(lst)); print(json.dumps(lst[0],ensure_ascii=False)[:500])
codes={str(x.get('code') or x.get('代码') or x.get('股票代码')) for x in lst}
zt={r['代码'] for r in csv.DictReader(open(root+'20261102/zt_pool.csv',encoding='utf-8-sig'))}
gw=L("题材归位_20261102.json"); mp=gw['映射']
ai=[c for c,v in mp.items() if v['大方向']=='AI应用/传媒']
print("AI传媒45 在THS命中:", sum(1 for c in ai if c in codes), "/45 ; zt_pool", len(zt), "THS", len(codes))
print("THS有而zt_pool无(前20):", sorted(codes-zt)[:20])
print("zt_pool有而THS无:", sorted(zt-codes)[:10])
