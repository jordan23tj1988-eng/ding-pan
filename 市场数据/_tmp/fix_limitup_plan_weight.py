# -*- coding: utf-8 -*-
"""修 limitup 交易计划 buys 的权重字段名（'权重'→'权重%'），模拟盘引擎.py 消费 '权重%'"""
import json, shutil, os

os.chdir(r"D:\股票数据\市场数据")
p = "_学习/交易计划_limitup_20261023.json"
shutil.copy2(p, p + ".bak_weightkey")
o = json.load(open(p, encoding="utf-8"))
fixed = []
for b in o.get("buys", []):
    if "权重%" not in b and "权重" in b:
        b["权重%"] = b.pop("权重")
        fixed.append((b.get("代码"), b.get("权重%")))
# 保持键顺序与昨日一致：代码/名称/权重%/理由/buy_gate
order = ["代码", "名称", "权重%", "理由", "buy_gate"]
o["buys"] = [{k: b[k] for k in order if k in b} for b in o["buys"]]
json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("修正:", fixed)
chk = json.load(open(p, encoding="utf-8"))
print("回读 buys:", [(b["代码"], b.get("权重%")) for b in chk["buys"]], "合计", sum(b.get("权重%") or 0 for b in chk["buys"]))
print("sells:", chk.get("sells"), "| 在持仓表态含002242:", "002242" in chk.get("notes", ""))
