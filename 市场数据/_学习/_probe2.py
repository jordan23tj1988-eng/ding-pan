# -*- coding: utf-8 -*-
import json, os, sys, csv, glob
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:/股票数据/市场数据"
L = BASE + "/_学习"

# zt_pool.csv
for cand in [BASE+"/20261015/zt_pool.csv", BASE+"/zt_pool.csv"]:
    if os.path.exists(cand):
        print("=== zt_pool:", cand)
        with open(cand, 'r', encoding='utf-8-sig') as f:
            r = csv.DictReader(f)
            rows = list(r)
        print("cols:", r.fieldnames)
        for row in rows:
            print(" | ".join(str(row.get(c,'')) for c in r.fieldnames))
        break

print("=== 20261015 files in _学习 ===")
for p in sorted(glob.glob(L + "/*20261015*")):
    print(os.path.basename(p), os.path.getsize(p))
