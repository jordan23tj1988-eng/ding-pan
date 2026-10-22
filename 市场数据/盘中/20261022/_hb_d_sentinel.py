# -*- coding: utf-8 -*-
"""hb-d 出件自审哨兵: 数字台账 vs 源文件逐项核对"""
import json, statistics, io, sys

D = r"D:\股票数据\市场数据\盘中\20261022"
dec = json.load(io.open(D + r"\临盘决断_20261022_1330.json", encoding="utf-8"))
pools = json.load(io.open(D + r"\_hb_d_pools_1330.json", encoding="utf-8"))
q = json.load(io.open(D + r"\_hb_d_quote_1330.json", encoding="utf-8"))["rows"]
fr = [json.loads(l) for l in io.open(D + r"\realtime_ticks.jsonl", encoding="utf-8") if l.strip()]
f = [x for x in fr if x["ts"] == "2026-10-22 13:33:02"][0]
rows = {x["code"]: x for x in f["rows"]}
v = [x["pct"] for x in f["rows"]]
fails = []

def ck(name, ok, got="", exp=""):
    print(("PASS " if ok else "FAIL ") + name + ("  got=%s exp=%s" % (got, exp) if not ok else ""))
    if not ok:
        fails.append(name)

# 1 池计数
zt, zb, dt = len(pools["zt"]), len(pools["zb"]), len(pools["dt"])
ck("涨停池=30", zt == 30, zt, 30)
ck("炸板池=19", zb == 19, zb, 19)
ck("跌停池=14", dt == 14, dt, 14)
lb = {}
for p in pools["zt"]:
    lb[p["lbc"]] = lb.get(p["lbc"], 0) + 1
ck("连板分布", lb == {1: 22, 2: 4, 3: 2, 5: 2}, lb, {1: 22, 2: 4, 3: 2, 5: 2})
rate = round(zb / (zt + zb), 4)
ck("炸板率 0.3878", rate == 0.3878, rate, 0.3878)

# 2 002242 双源
ck("002242 池帧 21.54/-4.77", rows["002242"]["latest"] == 21.54 and rows["002242"]["pct"] == -4.77, rows["002242"]["latest"], 21.54)
ck("002242 腾讯 21.61", q["sz002242"]["px"] == 21.61, q["sz002242"]["px"], 21.61)
ck("002242 今低 20.90 未破", rows["002242"]["low"] == 20.9, rows["002242"]["low"], 20.9)
ck("对成本 -0.69%", abs((21.54 / 21.69 - 1) * 100 + 0.69) < 0.01, (21.54 / 21.69 - 1) * 100, -0.69)
ck("浮亏 -135", round((21.54 - 21.69) * 900) == -135, (21.54 - 21.69) * 900, -135)

# 3 指数
exp_idx = {"sh000001": (3658.55, -1.47), "sz399001": (11376.97, -2.80), "sz399006": (2590.0, -3.89)}
for k, (px, pct) in exp_idx.items():
    ck("指数 %s %s/%s" % (k, px, pct), q[k]["px"] == px and abs(q[k]["pct"] - pct) < 0.005, (q[k]["px"], q[k]["pct"]), (px, pct))

# 4 池内统计
ck("池内中位 -1.36", round(statistics.median(v), 2) == -1.36, statistics.median(v), -1.36)
ck("池内均值 -0.32", round(statistics.mean(v), 2) == -0.32, statistics.mean(v), -0.32)
ck("涨22/跌28", (sum(1 for p in v if p > 0), sum(1 for p in v if p < 0)) == (22, 28))
ck(">=9 9只 / <=-9 6只", (sum(1 for p in v if p >= 9), sum(1 for p in v if p <= -9)) == (9, 6))

# 5 高位票
for c, px, pct in [("002696", 10.76, 2.28), ("000530", 9.27, 7.42), ("600202", 5.97, 7.18), ("601091", 21.36, 8.87), ("002520", 6.08, 7.42)]:
    k = ("sh" if c.startswith("6") else "sz") + c
    ck("高位炸板 %s %s/%s" % (c, px, pct), q[k]["px"] == px and abs(q[k]["pct"] - pct) < 0.005, (q[k]["px"], q[k]["pct"]), (px, pct))

# 6 无成交
ck("fills 为空", dec["fills"] == [] and all(x.get("fill") is None for x in dec["fills"]) if dec["fills"] else True)
ck("A/B/C 全 0 笔", all(dec["权限分级"][k].startswith("0 笔") for k in "ABC"))
ck("权限分级键齐全", set(dec["权限分级"]) == {"A", "B", "C"})

# 7 报警文件
alm = [json.loads(l) for l in io.open(D + r"\报警_20261022.jsonl", encoding="utf-8")]
ck("报警 3 条", len(alm) == 3, len(alm), 3)
ck("报警含闸门击穿", any(a["type"] == "intraday_dt_gate_breached" for a in alm))

# 8 文件不可覆盖语义(存在即发出版)
import os
ck("决断件存在", os.path.exists(D + r"\临盘决断_20261022_1330.json"))

print("\n结论:", "ALL PASS" if not fails else "FAIL %d 项: %s" % (len(fails), fails))
sys.exit(1 if fails else 0)
