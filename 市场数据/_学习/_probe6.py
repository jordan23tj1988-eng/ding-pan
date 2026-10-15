# -*- coding: utf-8 -*-
import json, os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')
B = r"D:/股票数据/市场数据"
M = B + "/_学习/_模拟盘/master"
print("=== master dir ===")
for f in sorted(os.listdir(M)):
    p = os.path.join(M, f)
    print(f, os.path.getsize(p))
# 账本 tail
for name in ["账本.jsonl","账本.csv"]:
    p = os.path.join(M,name)
    if os.path.exists(p):
        print("--- ", name)
        lines = open(p, encoding='utf-8').read().strip().split("\n")
        print("lines:", len(lines))
        for l in lines[-8:]:
            print(l[:600])
# bars for holdings
for code in ["600693","605577"]:
    p = B + "/_学习/_bars_cache/%s.csv" % code
    if os.path.exists(p):
        lines = open(p, encoding='utf-8').read().strip().split("\n")
        print("--- bars", code, "head:", lines[0])
        for l in lines[-4:]:
            print(l)
# dt_pool / strong_pool 20261015
for fn in ["dt_pool.csv","strong_pool.csv","zb_pool.csv"]:
    p = B + "/20261015/" + fn
    if os.path.exists(p):
        rows = list(csv.DictReader(open(p, encoding='utf-8-sig')))
        print("---", fn, "rows", len(rows), "cols", list(rows[0].keys())[:14] if rows else None)
        for r in rows:
            if r.get('代码') in ("600693","605577"):
                print(r)
