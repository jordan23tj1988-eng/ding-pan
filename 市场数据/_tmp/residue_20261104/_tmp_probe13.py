# -*- coding: utf-8 -*-
import json, sys, csv, collections
sys.stdout.reconfigure(encoding='utf-8')
base = "D:/股票数据/市场数据/_学习/"
root = "D:/股票数据/市场数据/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p, encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("LOADFAIL", p, last); return None
gw = L("题材归位_20261102.json"); mp = gw['映射']
rows={}
with open(root+"20261102/zt_pool.csv", encoding='utf-8-sig') as f:
    for r in csv.DictReader(f): rows[r['代码']]=r
by=collections.defaultdict(list)
for c,v in mp.items(): by[v['大方向']].append((c,v))
print("=== 主环节(第一段)离散度 ===")
for d,arr in sorted(by.items(), key=lambda x:-len(x[1])):
    pri=[ (v.get('环节') or '').split('/')[0] for c,v in arr]
    cnt=collections.Counter(pri)
    dup={k:n for k,n in cnt.items() if n>=2}
    print("%-14s n=%2d 主环节数=%2d 离散度=%.2f 重复环节=%s" % (d,len(arr),len(cnt),len(cnt)/len(arr), dup if dup else "无"))
print("\n=== 600801 ===")
print(json.dumps(rows.get('600801'), ensure_ascii=False))
print("\n=== 002827 / 001230 / 600261 核对 ===")
for c in ['002827','001230','600261','001219','002275','002086','002172','000995','600838']:
    print(c, json.dumps(rows.get(c), ensure_ascii=False))
