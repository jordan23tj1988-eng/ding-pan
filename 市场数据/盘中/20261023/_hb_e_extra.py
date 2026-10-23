# -*- coding: utf-8 -*-
"""hb-e 补充: 002639(已清)现价 + 高位6板 + 持仓/止损机会成本实算"""
import json, urllib.request, os
D = r"D:\股票数据\市场数据\盘中\20261023"
codes = "sz002639,sh603278,sz002724,sh600838,sz003021"
u = "https://qt.gtimg.cn/q=" + codes
raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"}), timeout=15).read().decode("gbk", "replace")
rows = {}
for seg in raw.strip().split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    k, _, b = seg.partition("=")
    f = b.strip().strip('"').split("~")
    if len(f) < 40:
        continue
    rows[k.strip()[2:]] = {"name": f[1], "px": float(f[3]), "pct": float(f[32]), "high": float(f[33]),
                           "low": float(f[34]), "pre": float(f[4]), "t": f[30], "amt_wan": f[37]}
print(json.dumps(rows, ensure_ascii=False, indent=1))

# 机会成本实算(002242 机械止损 vs 现价)
sell_242 = 20.74
px_242 = rows.get("sz002242") or {}
px_242 = 21.66
diff = (px_242 - sell_242) * 800
print("\n002242 止损 20.74 卖出800股 → 现价 %.2f, 差额 %+.0f 元 (%+.2f%%)" % (px_242, diff, (px_242 / sell_242 - 1) * 100))

# 603370 持仓浮盈
cost, qty = 28.11, 300
px = 30.13
print("603370 成本 %.2f × %d = %.2f；现价 %.2f → 市值 %.2f，浮盈 %+.2f 元 (%+.2f%%)" % (
    cost, qty, cost * qty, px, px * qty, (px - cost) * qty, (px / cost - 1) * 100))
print("距今日高 30.16 回落 %.2f%%；距涨停 %.2f 需 %+.2f%%" % ((px / 30.16 - 1) * 100, 28.71 * 1.1, (28.71 * 1.1 / px - 1) * 100))
print("昨收 28.71 → 涨停价 %.2f" % (28.71 * 1.1))
