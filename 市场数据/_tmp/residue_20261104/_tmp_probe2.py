# -*- coding: utf-8 -*-
import json, collections, sys
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
print("日期", gw['日期'], "来源", gw['来源'], "口径", gw['口径'])
print("counts", gw['counts'], "档计数", gw['档计数'])
print("方向聚合", json.dumps(gw['方向聚合'], ensure_ascii=False)[:1200])
mp = gw['映射']
print("映射 len", len(mp), "sample keys", list(mp)[:3])
k0 = list(mp)[0]
print("sample", k0, json.dumps(mp[k0], ensure_ascii=False)[:800])
by = collections.defaultdict(list)
for code, v in mp.items():
    d = v.get('大方向') or v.get('方向')
    by[d].append((code, v))
print("--- by dir ---")
for d, arr in sorted(by.items(), key=lambda x:-len(x[1])):
    print(d, len(arr))
