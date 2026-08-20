# -*- coding: utf-8 -*-
"""哨兵: 1445场产出自审"""
import json, io, os, glob

p1 = r"盘中/20260819/临盘决断_20260819_1445.json"
d = json.loads(io.open(p1, encoding="utf-8").read())
assert d["session"] == "deepb-1445", d["session"]
assert d["decision"]["level"] == "ALARM_ONLY", d["decision"]["level"]
assert d["条件决断"] == [] and d["decision"]["fills"] == []
print("OK 临盘决断: session=%s level=%s 条件决断=%d fills=%d" % (d["session"], d["decision"]["level"], len(d["条件决断"]), len(d["decision"]["fills"])))

p2 = r"_学习/盘中尾盘复盘_20260819.md"
assert os.path.isfile(p2), p2
print("OK 复盘md: %d bytes" % os.path.getsize(p2))

fs = sorted(glob.glob(r"盘中/20260819/临盘决断_20260819_*.json"))
print("OK 今日临盘决断族(%d份):" % len(fs), [os.path.basename(x) for x in fs])
