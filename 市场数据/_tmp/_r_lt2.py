# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
d = json.load(open(X + "/涨停对链条_20260826.json", encoding="utf-8"))
rows = []
for L in d["题材线"]:
    for h in L["环节"]:
        for g in h["个股"]:
            rows.append((L["大方向"], L["家数"], L.get("开板占比"), h["环节"], h["快判"][:14],
                         g["代码"], g["名称"], g["首封"], g["连板"], g["开板次数"], g["封单比"], g["来源档"]))
print("个股总数", len(rows), "| 待归位", d["待归位_行业兜底"], "| 线数", d["题材线数"])
for r in sorted(rows, key=lambda x: -x[10]):
    print(r)
