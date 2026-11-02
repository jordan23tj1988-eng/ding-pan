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
mp = gw['映射']
by = collections.defaultdict(list)
for code, v in mp.items():
    by[v['大方向']].append(v)
for d, arr in sorted(by.items(), key=lambda x:-len(x[1])):
    print("\n###", d, len(arr))
    arr.sort(key=lambda v:(-int(str(v.get('连板口径','1板')).replace('连板','').replace('板','') or 1), v.get('首封','')))
    for v in arr:
        print(" ", v['代码'], v['名称'], v.get('连板口径'), "首封",v.get('首封'), "开板",v.get('开板次数'), "|", v.get('环节'), "|", v.get('催化')[:70], "| 行业", v.get('所属行业'))
