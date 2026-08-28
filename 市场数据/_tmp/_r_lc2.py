# -*- coding: utf-8 -*-
import json
X = "D:/股票数据/市场数据/_学习"
d = json.load(open(X + "/题材生命周期_20260826.json", encoding="utf-8"))
keep = {"有色/工业金属","有色/贵金属","数字经济/数字货币","重组/控制权变更","消费电子",
        "家电/零部件","家居/家居用品","医药/化学制药","农业/种业","电力/电网设备",
        "电力/电力","消费/酒店餐饮","建筑/工程咨询","造纸/造纸"}
for e in d["阶段表"]:
    if e["线"] in keep:
        print(json.dumps(e, ensure_ascii=False))
        print()
