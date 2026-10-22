# -*- coding: utf-8 -*-
"""hb-d 出件自审哨兵 v2: 决断件数字 vs 源文件逐项核对
口径:
- 涨停/炸板/连板/炸板率/池内统计/002242/指数 -> 机器严格核对(时点一致)
- 跌停数 -> 决断时点(13:31~13:32)读 14; 正确口径 13:34 重取 16 -> 核对『>=14 且原14名单为子集』
- 高位炸板票 -> 决断件记录 13:32:54 价, 13:34 留档价允许漂移, 只核对成员与方向
"""
import json, statistics, io, os, sys

D = r"D:\股票数据\市场数据\盘中\20261022"
dec = json.load(io.open(D + r"\临盘决断_20261022_1330.json", encoding="utf-8"))
pools = json.load(io.open(D + r"\_hb_d_pools_1330.json", encoding="utf-8"))
dtfix = json.load(io.open(D + r"\_hb_d_pools_1330_dtfix.json", encoding="utf-8"))
q = json.load(io.open(D + r"\_hb_d_quote_1330.json", encoding="utf-8"))["rows"]
hi = json.load(io.open(D + r"\_hb_d_quote_hi.json", encoding="utf-8"))["rows"]
fr = [json.loads(l) for l in io.open(D + r"\realtime_ticks.jsonl", encoding="utf-8") if l.strip()]
f = [x for x in fr if x["ts"] == "2026-10-22 13:33:02"][0]
rows = {x["code"]: x for x in f["rows"]}
v = [x["pct"] for x in f["rows"]]
fails = []

def ck(name, ok, got="", exp=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  got=%s exp=%s" % (got, exp)))
    if not ok:
        fails.append(name)

zt, zb = len(pools["zt"]), len(pools["zb"])
ck("涨停池=30", zt == 30, zt, 30)
ck("炸板池=19", zb == 19, zb, 19)
ck("炸板率=0.3878", round(zb / (zt + zb), 4) == 0.3878, round(zb / (zt + zb), 4), 0.3878)
lb = {}
for p in pools["zt"]:
    lb[p["lbc"]] = lb.get(p["lbc"], 0) + 1
ck("连板分布 22/4/2/2", lb == {1: 22, 2: 4, 3: 2, 5: 2}, lb, {1: 22, 2: 4, 3: 2, 5: 2})

dt_now = set(p["c"] for p in dtfix["pool"])
dt_dec14 = {"000995", "603529", "001368", "600661", "603105", "002835", "600241", "603669",
            "000712", "002815", "002990", "002172", "002388", "000993"}
ck("跌停池(13:34正确口径)>=14", len(dt_now) >= 14, len(dt_now), ">=14")
ck("原14名单为13:34名单子集", dt_dec14 <= dt_now, sorted(dt_dec14 - dt_now), "空")
ck("跌停>=12 闸门FAIL 结论成立", len(dt_dec14) >= 12 and len(dt_now) >= 12)

ck("002242 池帧21.54/-4.77", rows["002242"]["latest"] == 21.54 and rows["002242"]["pct"] == -4.77)
ck("002242 腾讯21.61", q["sz002242"]["px"] == 21.61)
ck("002242 今低20.90 未破", rows["002242"]["low"] == 20.9)
ck("对成本-0.69%", abs((21.54 / 21.69 - 1) * 100 + 0.69) < 0.01)
ck("浮亏-135元", round((21.54 - 21.69) * 900) == -135)

for k, px, pct in [("sh000001", 3658.55, -1.47), ("sz399001", 11376.97, -2.80), ("sz399006", 2590.0, -3.89)]:
    ck("指数 %s" % k, q[k]["px"] == px and abs(q[k]["pct"] - pct) < 0.005, (q[k]["px"], q[k]["pct"]), (px, pct))

ck("池内中位-1.36", round(statistics.median(v), 2) == -1.36)
ck("池内均值-0.32", round(statistics.mean(v), 2) == -0.32)
ck("涨22/跌28", (sum(1 for p in v if p > 0), sum(1 for p in v if p < 0)) == (22, 28))
ck(">=+9 9只 / <=-9 6只", (sum(1 for p in v if p >= 9), sum(1 for p in v if p <= -9)) == (9, 6))

zb_codes = set(p["c"] for p in pools["zb"])
zt_codes = set(p["c"] for p in pools["zt"])
ck("002696/000530 在炸板池", {"002696", "000530"} <= zb_codes)
ck("002724/603278/600293/002076 在涨停池", {"002724", "603278", "600293", "002076"} <= zt_codes)
print("INFO 高位炸板票 13:34 现价%:", [(c, hi[("sh" if c.startswith("6") else "sz") + c]["pct"])
                                 for c in ["002696", "000530", "600202", "002520", "601091"]])
ck("高位炸板票未回封", all(hi[("sh" if c.startswith("6") else "sz") + c]["pct"] < 9.9
                       for c in ["002696", "000530", "600202", "002520", "601091"]))
for c in ["002724", "603278", "600293", "002076"]:
    k = ("sh" if c.startswith("6") else "sz") + c
    ck("封板票 %s 仍涨停" % c, hi[k]["pct"] >= 9.9, hi[k]["pct"], ">=9.9")

ck("fills 为空", dec["fills"] == [])
ck("A/B/C 均 0 笔", all(dec["权限分级"][k].startswith("0 笔") for k in "ABC"))
alm = [json.loads(l) for l in io.open(D + r"\报警_20261022.jsonl", encoding="utf-8")]
ck("报警>=3 条", len(alm) >= 3, len(alm), ">=3")
ck("含闸门击穿告警", any(a["type"] == "intraday_dt_gate_breached" for a in alm))
ck("含查询口径陷阱告警", any(a["type"] == "dtpool_query_param_trap" for a in alm))
ck("决断件存在(发出版)", os.path.exists(D + r"\临盘决断_20261022_1330.json"))

print("\n结论:", "ALL PASS" if not fails else "FAIL %d 项: %s" % (len(fails), fails))
sys.exit(1 if fails else 0)
