# -*- coding: utf-8 -*-
"""读回发出版，核对关键字段并生成中文汇报（数字取自发出版，非重算）。"""
import json, os
P = r"D:\股票数据\市场数据\盘中\20261012\临盘决断_20261012_1445.json"
d = json.load(open(P, encoding="utf-8"))
print("size", os.path.getsize(P), "| keys", len(d))
print("date/session/ts =", d["date"], d["session"], d["ts"])
print("no_action =", d["no_action"], "| fills =", d["fills"], "| 报警项 =", len(d["报警项"]), "| 缺件 =", len(d["缺件"]))
print("level =", d["decision"]["level"])
print("宽度 =", d["池内技术触发"]["宽度"])
print("封板 =", d["池内技术触发"]["封板(pct>=9.8, 末帧)"][:40], "...")
print("深跌 =", d["池内技术触发"]["深跌(<=-5%, 末帧)"][:60])
print("跌停 =", d["池内技术触发"]["跌停(<=-9.8%)"][:40])
print("决断窗 =", d["池内技术触发"]["决断窗(14:35:04→14:44:05, 10帧)"])
print("尾盘段 =", d["池内技术触发"]["尾盘段(14:14→14:44)"])
print("相对强度 =", d["池内技术触发"]["相对强度"])
print("持仓 =", d["持仓表态"]["合法在持票数"])
print("卖预案 =", d["卖预案执行"]["结果"])
print("reason[:160] =", d["reason"][:160])
print("reason[Δ窗: ] =", d["reason"][d["reason"].find("【决断窗】"):d["reason"].find("【尾盘结构】")])
print("reason[尾盘] =", d["reason"][d["reason"].find("【尾盘结构】"):d["reason"].find("【主线】")])
