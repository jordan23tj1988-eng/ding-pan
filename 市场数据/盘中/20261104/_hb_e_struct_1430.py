# -*- coding: utf-8 -*-
"""hb-e 补充: 涨停池结构(题材/封单/新增) + 持仓估值 + 早盘卖出机会成本"""
import json
from collections import Counter

D = r"D:\股票数据\市场数据\盘中\20261104"
now = json.load(open(D + r"\_hb_e_pools_1430.json", encoding="utf-8"))
old = json.load(open(D + r"\_hb_d_pools_1330.json", encoding="utf-8"))
zt_n, zb_n, dt_n = now["zt"], now["zb"], now["dt"]
zt_o = old["zt"]

print("=== 14:33 涨停", len(zt_n), "炸板", len(zb_n), "跌停", len(dt_n), "| 13:37 涨停", len(zt_o), "炸板", len(old["zb"]), "跌停", len(old["dt"]))
print("炸板率 now %.4f / 13:37 %.4f" % (len(zb_n)/(len(zt_n)+len(zb_n)), len(old["zb"])/(len(zt_o)+len(old["zb"]))))
print("二板加 now", sum(1 for x in zt_n if x["lbc"] >= 2), "/ 13:37", sum(1 for x in zt_o if x["lbc"] >= 2))
print("连板分布 now", dict(sorted(Counter(x["lbc"] for x in zt_n).items())))
print("曾炸板(zbc>=1) now", sum(1 for x in zt_n if x.get("zbc", 0) >= 1), "占", round(sum(1 for x in zt_n if x.get("zbc",0)>=1)/len(zt_n), 4))

hy = Counter(x.get("hybk") or "?" for x in zt_n)
print("\n=== 14:33 涨停行业 TOP15 ===")
for k, v in hy.most_common(15):
    print("  %-10s %d" % (k, v))

hy_o = Counter(x.get("hybk") or "?" for x in zt_o)
print("\n=== 13:37 涨停行业 TOP10 ===")
for k, v in hy_o.most_common(10):
    print("  %-10s %d" % (k, v))

new_codes = set(x["c"] for x in zt_n) - set(x["c"] for x in zt_o)
lost_codes = set(x["c"] for x in zt_o) - set(x["c"] for x in zt_n)
print("\n新增涨停(13:37→14:33)", len(new_codes), "消失", len(lost_codes))
print("新增行业", Counter(next(x["hybk"] for x in zt_n if x["c"] == c) or "?" for c in new_codes).most_common(12))
print("消失名单", [(x["n"], x["lbc"]) for x in zt_o if x["c"] in lost_codes][:15])

print("\n=== 封单最大 TOP10 ===")
for x in sorted(zt_n, key=lambda y: -(y.get("fund") or 0))[:10]:
    print("  %-6s %-6s %d板 封单%.2f亿 首封%s 炸%d 换手%.1f%% %s" % (
        x["c"], x["n"], x["lbc"], (x.get("fund") or 0)/1e8, x.get("fbt"), x.get("zbc", 0), x.get("hs") or 0, x.get("hybk")))

print("\n=== 跌停池 ===")
for x in dt_n:
    print("  ", x.get("c"), x.get("n"), x.get("hybk"), round(x.get("zdp") or 0, 2), "lbc", x.get("lbc"))

# 持仓估值
q = json.load(open(D + r"\_hb_e_quote_1430.json", encoding="utf-8"))["rows"]
print("\n=== 持仓/相关票 ===")
for k, v in q.items():
    print("  %-9s %-7s 现%.2f %+6.2f%% 昨收%.2f 开%.2f 高%.2f 低%.2f bid1 %s×%s ask1 %s×%s" % (
        k, v["name"], v["px"], v["pct"], v["pre"], v["open"], v["high"], v["low"], v["bid1"], v["bid1_vol"], v["ask1"], v["ask1_vol"]))

m = json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\state.json", encoding="utf-8"))
print("\n=== master 账本 (mtime 2026-11-03 20:35) cash", m["cash"], "===")
mv = 0
for p in m["positions"]:
    code = ("sh" if p["code"][0] == "6" else "sz") + p["code"]
    px = q.get(code, {}).get("px")
    val = px * p["shares"] if px else None
    if val:
        mv += val
    print("  %s %s %d股 成本%.2f 现价%s 市值%s 浮动%s" % (
        p["code"], p["name"], p["shares"], p["buy_px"], px, round(val, 2) if val else None,
        round((px - p["buy_px"]) * p["shares"], 2) if px else None))
print("  持仓市值 %.2f  合计净值 %.2f  (%+.3f%%)" % (mv, m["cash"] + mv, (m["cash"] + mv) / 1e6 * 100 - 100))

# 早盘卖出机会成本 (推定口径)
print("\n=== 早盘卖出腿 vs 14:33 现价 (机会成本) ===")
legs = [("002652", "扬子新材", 3600, 3.79), ("002365", "永安药业", 1500, 12.18), ("001287", "中电港", 400, 20.04)]
tot = 0
for c, n, sh, px in legs:
    code = ("sh" if c[0] == "6" else "sz") + c
    cur = q[code]["px"]
    diff = (cur - px) * sh
    tot += diff
    print("  %s %s %d股 卖%.2f 现%.2f 差%+.2f元 (%+.2f%%)" % (c, n, sh, px, cur, diff, (cur / px - 1) * 100))
print("  合计机会成本 %+.2f 元" % tot)

# 未成交/推定买入腿
print("\n=== 推定买入腿(无回执) vs 现价 ===")
buys = [("002652", 3600, 4.05), ("603906", 600, 15.56), ("600261", 900, 4.95)]
tb = 0
for c, sh, px in buys:
    code = ("sh" if c[0] == "6" else "sz") + c
    cur = q[code]["px"]
    d = (cur - px) * sh
    tb += d
    print("  %s %d股 开盘价%.2f 现%.2f 差%+.2f元 (%+.2f%%)" % (c, sh, px, cur, d, (cur / px - 1) * 100))
print("  合计 %+.2f 元" % tb)
