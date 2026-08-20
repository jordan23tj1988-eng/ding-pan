# -*- coding: utf-8 -*-
"""1445场·明细: cards全字段(sell/abort/fill/timeline)+连板票+判断流水+spec目录"""
import json, io, os, glob, datetime

BASE = r"D:\股票数据\市场数据"
def rd(p):
    return io.open(p, encoding="utf-8").read()

w = json.loads(rd(os.path.join(BASE, "盘中", "20260818", "warboard.json")))
print("=== cards 全字段 ===")
for c in w.get("cards") or []:
    print(json.dumps(c, ensure_ascii=False))
    print("---")

print("\n=== 连板票 ===")
for x in w.get("连板票") or []:
    print(json.dumps(x, ensure_ascii=False))

print("\n=== 判断流水(今日) ===")
jp = os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "判断流水.jsonl")
if os.path.exists(jp):
    for line in rd(jp).splitlines()[-15:]:
        d = json.loads(line)
        if d.get("ts","").startswith("08-19"):
            print(json.dumps(d, ensure_ascii=False))

print("\n=== 今日临盘决断 全文 ===")
tdir = os.path.join(BASE, "盘中", "20260819")
for f in sorted(glob.glob(os.path.join(tdir, "临盘决断_*.json"))):
    print("\n-----", os.path.basename(f), "-----")
    print(rd(f))

print("\n=== _agent规格 目录 ===")
sp = os.path.join(BASE, "_agent规格")
try:
    for root, dnames, fnames in os.walk(sp):
        for fn in fnames:
            print(os.path.join(root, fn))
except Exception as e:
    print("ERR", e)

print("\n=== _协作 目录 ===")
sp2 = os.path.join(BASE, "_协作")
try:
    for root, dnames, fnames in os.walk(sp2):
        for fn in fnames:
            print(os.path.join(root, fn))
except Exception as e:
    print("ERR", e)
