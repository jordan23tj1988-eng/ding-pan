import json, os
base = r"D:\股票数据\市场数据"
for d in ("20261029", "20261030", "20261102", "20261103"):
    p = os.path.join(base, d, "summary.json")
    try:
        s = json.load(open(p, encoding="utf-8"))
        print(d, "涨停", s.get("涨停家数"), "跌停", s.get("跌停家数"), "炸板率", s.get("炸板率"),
              "最高", s.get("最高连板"), "量能", s.get("两市成交额_亿"), "梯队", s.get("连板梯队"))
    except Exception as e:
        print(d, "ERR", e)
