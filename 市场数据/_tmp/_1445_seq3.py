# -*- coding: utf-8 -*-
"""1445场·取seq3全文+checks+account, 供复盘引用"""
import json, io, os

BASE = r"D:\股票数据\市场数据"
def rd(p):
    return io.open(p, encoding="utf-8").read()

w = json.loads(rd(os.path.join(BASE, "盘中", "20260818", "warboard.json")))
resp = w.get("responses") or []
r = resp[-1]
print("=== seq%d %s %s ===" % (r.get("seq"), r.get("trigger"), r.get("ts")))
print(r.get("note"))
print("\n=== checks ===")
print(json.dumps(w.get("checks"), ensure_ascii=False))
print("\n=== account ===")
print(json.dumps(w.get("account"), ensure_ascii=False))
print("\n=== judgment ===")
print(json.dumps(w.get("judgment"), ensure_ascii=False)[:600])
print("\n=== response(旧字段) ===")
print(json.dumps(w.get("response"), ensure_ascii=False)[:400])
print("\n=== 判断流水 全部今日 ===")
jp = os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "判断流水.jsonl")
for line in rd(jp).splitlines():
    d = json.loads(line)
    if d.get("ts","").startswith("08-19"):
        print(d.get("ts"), d.get("场"), d.get("code"), d.get("name"), d.get("档位"))
