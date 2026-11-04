# -*- coding: utf-8 -*-
"""交付自检：推演 + master 计划 schema/白名单/算术。"""
import json, re, sys

WL = {"温度","温度档","涨停数","跌停数","炸板率","最高连板","二板加","两市成交额_亿",
      "涨停家数_净","一进二率","二进三率","高度晋级率","昨停溢价","核按钮率","温度变化","代码封板","代码收红"}
CODE_ITEMS = {"代码封板","代码收红"}
err = []

t = json.load(open(r"D:/股票数据/市场数据/_学习/推演_20261104.json", encoding="utf-8"))
for k in ["日期","来源"]:
    if k not in t: err.append("推演缺字段: "+k)
for k in ["情绪几度","明日攻防","主线站队","龙头接力","竞价强弱预判"]:
    if k not in t or not isinstance(t[k],str) or len(t[k])<60:
        err.append("推演缺/过短字段: "+k)
preds = t["次日可证伪预测"]
print("预测条数", len(preds))
from collections import Counter
cnt = Counter()
for i,p in enumerate(preds,1):
    for k in ["项","预测","判定条件"]:
        if k not in p: err.append("预测%d 缺 %s"%(i,k))
    c = p["判定条件"]
    for k in ["指标","方向","阈值"]:
        if k not in c: err.append("预测%d 判定条件缺 %s"%(i,k))
    ind = c.get("指标")
    cnt[ind]+=1
    if ind not in WL: err.append("预测%d 指标不在白名单: %s"%(i,ind))
    if c.get("方向") not in (">=","<=","=="): err.append("预测%d 方向非法: %s"%(i,c.get("方向")))
    if not isinstance(c.get("阈值"), (int,float)): err.append("预测%d 阈值非数值"%i)
    if ind in CODE_ITEMS and not re.fullmatch(r"\d{6}", str(c.get("代码",""))):
        err.append("预测%d 代码类缺 6 位代码"%i)
    txt = json.dumps(c, ensure_ascii=False)
    for bad in ["可能","大概","或许","左右","或","上下"]:
        if bad in txt: err.append("预测%d 判定条件含模糊词 %s"%(i,bad))
print("指标分布", dict(cnt))

m = json.load(open(r"D:/股票数据/市场数据/_学习/交易计划_master_20261104.json", encoding="utf-8"))
allowed = {"002992","688809"}
tot = 0.0
for b in m["buys"]:
    tot += b["权重%"]
    if b["代码"] not in allowed: err.append("buy 越权标的: "+b["代码"])
    g = b.get("buy_gate") or {}
    if g.get("min_gap_pct") is None or g.get("max_gap_pct") is None:
        err.append("buy %s 缺 buy_gate"%b["代码"])
    if not (0 <= b["权重%"] <= 1.0): err.append("buy %s 权重越 1.0%% 单票上限(总裁决)"%b["代码"])
    if not re.fullmatch(r"\d{6}", b["代码"]): err.append("buy 代码格式错")
print("buys 总仓位 %.2f%%" % tot, [ (b["代码"],b["权重%"]) for b in m["buys"]])
if tot > 1.5 + 1e-9: err.append("总仓越 1.5%%: %.2f"%tot)

st = json.load(open(r"D:/股票数据/市场数据/_学习/_模拟盘/master/状态.json", encoding="utf-8"))
held = {p["code"]: p for p in st["持仓"]}
sold = {s["代码"]: s for s in m["sells"]}
print("在持", list(held), "卖单", list(sold))
for c,p in held.items():
    if c not in sold: err.append("在持票未表态: "+c)
for r in m["sells"]:
    if r["腿"] not in ("open","close"): err.append("sell 腿非法: "+r["腿"])
    if not isinstance(r.get("ref_px"), (int,float)): err.append("sell %s 缺 ref_px"%r["代码"])
    elif r["代码"] in held and abs(r["ref_px"]-held[r["代码"]]["buy_px"])>1e-9:
        err.append("sell %s ref_px 与成本不符"%r["代码"])
    if r["代码"] not in held: err.append("sell 指向非持仓: "+r["代码"])

print("="*20)
print("ERRORS:" if err else "ALL CHECKS PASSED")
for e in err: print(" -", e)
sys.exit(1 if err else 0)
