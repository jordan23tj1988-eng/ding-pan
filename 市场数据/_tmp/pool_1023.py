# -*- coding: utf-8 -*-
import json, gzip, csv, io, os
B = r"D:/股票数据/市场数据"
L = B + "/_学习"
pool = json.load(open(L + "/竞价评分_20261023.json", encoding="utf-8"))
codes = [x["代码"] for x in pool["明细"]]
print("池", len(codes), codes)
rows = list(csv.DictReader(open(B + "/20261023/zt_pool.csv", encoding="utf-8-sig")))
z = {r["代码"]: r for r in rows}
print("zt", len(z))
# snapshot
snap = {}
with gzip.open(L + "/竞价快照存档/20261023.csv.gz", "rt", encoding="utf-8-sig") as f:
    rd = csv.DictReader(f)
    cols = rd.fieldnames
    print("snap cols", cols)
    data = list(rd)
print("snap rows", len(data), data[0])
# find open/prevclose columns
print("\n== 池票明细 ==")
for it in pool["明细"]:
    c = it["代码"]; r = z.get(c, {})
    print(c, it["名称"], "首封", it["首封"], "末封", r.get("最后封板时间"), "连板", it["连板"], "炸", it["炸板"],
          "封单比", it["封单比"], "行业", r.get("所属行业"), "流通亿", round(float(r.get("流通市值") or 0)/1e8, 2),
          "成交亿", round(float(r.get("成交额") or 0)/1e8, 2), "换手", round(float(r.get("换手率") or 0), 2),
          "封单亿", round(float(r.get("封板资金") or 0)/1e8, 2), "涨停统计", r.get("涨停统计"), "分", it["竞价分"])
print("\n== 金达威 002626 ==")
print(z.get("002626"))
