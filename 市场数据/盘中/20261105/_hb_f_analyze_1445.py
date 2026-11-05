# -*- coding: utf-8 -*-
"""hb-f 14:45 尾盘深场B 分析: 池/广度/持仓结构/连板天梯/行业分歧"""
import json, os
from collections import Counter

D = r"D:\股票数据\市场数据\盘中\20261105"
P = json.load(open(os.path.join(D, "_hb_f_pools_1445.json"), encoding="utf-8"))
Q = json.load(open(os.path.join(D, "_hb_f_quote_pxexec.json"), encoding="utf-8"))
QD = json.load(open(os.path.join(D, "_hb_f_quote_1445.json"), encoding="utf-8"))
zt, zb, dt = P["zt"], P["zb"], P["dt"]


def fbt6(x):
    return str(x.get("fbt", "")).zfill(6)


zt_sorted = sorted(zt, key=lambda x: (fbt6(x)))
after13 = [x for x in zt if fbt6(x) >= "130000"]
print("涨停", len(zt), "炸板", len(zb), "跌停", len(dt), "炸板率", round(len(zb) / (len(zt) + len(zb)), 4))
print("连板分布", dict(sorted(Counter(x["lbc"] for x in zt).items())))
print("午后新封(>=13:00)", len(after13), Counter(x.get("hybk") for x in after13).most_common(8))
print("午后新封明细", [(x["n"], x["lbc"], x.get("hybk"), fbt6(x), round(float(x.get("fund", 0)) / 1e8, 2)) for x in after13])
print("首封时点分布", Counter(("早盘<10:00" if fbt6(x) < "100000" else "10-13" if fbt6(x) < "130000" else "尾盘>=13") for x in zt))
print("二板+", [(x["n"], x["lbc"], x.get("hybk"), fbt6(x), round(float(x.get("fund", 0)) / 1e8, 2), x.get("zbc")) for x in sorted(zt, key=lambda y: -y["lbc"]) if x["lbc"] >= 2])
print("行业涨停", Counter(x.get("hybk") for x in zt).most_common(8))
print("行业炸板", Counter(x.get("hybk") for x in zb).most_common(8))
print("跌停", [(x["n"], x.get("hybk"), x.get("zdp")) for x in dt])
# 光伏线内部分歧
pv = [x for x in zt if x.get("hybk") == "光伏设备"]
pvb = [x for x in zb if x.get("hybk") == "光伏设备"]
print("光伏 涨停", len(pv), [x["n"] for x in pv], "炸板", len(pvb), [x["n"] for x in pvb])
# 封单厚度
fund = sorted(zt, key=lambda x: -float(x.get("fund", 0)))[:8]
print("封单前8", [(x["n"], x["lbc"], round(float(x.get("fund", 0)) / 1e8, 2)) for x in fund])
# 持仓
mp = json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\state.json", encoding="utf-8"))
cost = {p["code"]: p for p in mp["positions"]}
rows = Q["rows"]
print("=== 持仓表态 ===")
for k in ("sh600299", "sh600259", "sh603906", "sz002292"):
    e = rows[k]
    c = cost.get(e["code"], {})
    pnl = (e["px"] / c["buy_px"] - 1) * 100 if c.get("buy_px") else None
    print(e["code"], e["name"], "px", e["px"], "day%", e["pct"], "open", e["open"], "hi", e["high"], "lo", e["low"],
          "cost", c.get("buy_px"), "buy_date", c.get("buy_date"), "shares", c.get("shares"),
          "pnl_vs_buy%", round(pnl, 2) if pnl is not None else None,
          "mv", round(e["px"] * c.get("shares", 0), 2), "day_ret_yuan", round((e["px"] - e["pre"]) * c.get("shares", 0), 2))
# ticks 尾盘趋势
rows_t = []
with open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") as f:
    for ln in f:
        try:
            rows_t.append(json.loads(ln))
        except Exception:
            pass
print("=== 池内116只 尾盘广度 ===")
for r in rows_t[-10:]:
    p = [x["pct"] for x in r["rows"]]
    print(r["ts"], "均", round(sum(p) / len(p), 2), "中位", sorted(p)[len(p) // 2],
          "红", sum(1 for x in p if x > 0), "绿", sum(1 for x in p if x < 0),
          "贴板", sum(1 for x in p if x >= 9.6), "破-3", sum(1 for x in p if x <= -3), "破-8", sum(1 for x in p if x <= -8))
# 全天极值帧
best = max(rows_t, key=lambda r: sum(x["pct"] for x in r["rows"]) / len(r["rows"]))
print("池均最高帧", best["ts"], round(sum(x["pct"] for x in best["rows"]) / len(best["rows"]), 2))
print("末帧龄(s)", round((__import__("datetime").datetime.strptime(rows_t[-1]["ts"], "%Y-%m-%d %H:%M:%S") - __import__("datetime").datetime.now()).total_seconds()))
