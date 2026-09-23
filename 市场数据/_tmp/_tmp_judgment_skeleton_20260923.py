# -*- coding: utf-8 -*-
"""judgment 骨架(20260923): 注入类脚本(j 资金温度 / 台账三件套)前必须存在。"""
import json, os
BASE = r"D:\股票数据\市场数据"
D = "20260923"
p = os.path.join(BASE, "_学习", "judgment_%s.json" % D)
obj = {"date": D, "更新label": "%s 复盘" % D, "一句话": "", "ticker": "",
       "bodies": {}, "archive_body": ""}
if os.path.exists(p):
    old = json.load(open(p, encoding="utf-8-sig"))
    merged = dict(old)
    for k, v in obj.items():
        merged.setdefault(k, v)
    merged["date"] = D
    json.dump(merged, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("已存在→补键:", p, list(merged.get("bodies", {}).keys()))
else:
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("judgment骨架已建:", p)
