# -*- coding: utf-8 -*-
"""hb-e 14:30 尾盘前哨 决断件写出(发出版不可覆盖)"""
import json, os, datetime, hashlib

D = r"D:\股票数据\市场数据\盘中\20261022"
DATE = "20261022"
OUT = os.path.join(D, "临盘决断_%s_1430.json" % DATE)
assert not os.path.exists(OUT), "发出版已存在，禁止覆盖: " + OUT

q = json.load(open(os.path.join(D, "_hb_e_quote_1430.json"), encoding="utf-8"))["rows"]
pl = json.load(open(os.path.join(D, "_hb_e_pools_1430.json"), encoding="utf-8"))
exec_exists = os.path.exists(os.path.join(D, "执行流水.jsonl"))
pulse_exists = os.path.exists(os.path.join(D, "pulse.json"))
war_exists = os.path.exists(os.path.join(D, "warboard.json"))

# 002242 数学
cost, qty = 21.69, 900
px_frame, px_tx = 21.37, q["sz002242"]["px"]
cost_amt = cost * qty
mv_frame = px_frame * qty
pnl_frame = mv_frame - cost_amt
nav = cost_amt / 0.0197
print("cost_amt %.2f mv %.2f pnl %.2f pct_cost %.3f%% nav反推 %.0f pnl_nav %.4f%%"
      % (cost_amt, mv_frame, pnl_frame, (px_frame / cost - 1) * 100, nav, pnl_frame / nav * 100))
print("tx px", px_tx, "vs cost %.3f%%" % ((px_tx / cost - 1) * 100))
