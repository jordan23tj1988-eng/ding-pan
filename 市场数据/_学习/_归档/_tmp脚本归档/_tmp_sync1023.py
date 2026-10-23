# -*- coding: utf-8 -*-
import json, io, os
L = r"D:/股票数据/市场数据/_学习"; d = "20261023"

# 1) JSON 同步：认知迭代加第⑤条、可证伪条件加第⑤条
p = os.path.join(L, "limitup判断_%s.json" % d)
j = json.load(io.open(p, encoding="utf-8"))
titles = [x["标题"] for x in j["认知迭代"]]
if not any("反证" in t for t in titles):
    j["认知迭代"].append({
        "日期": d,
        "标题": "高位『未开板优于炸板回封』的裁决被当日反证（记错 1 笔）",
        "正文": "昨日判『可买入口径 002724(炸4) 优于 603278(炸0)』，今日实测 002724 gap-0.62%→执1 +10.68%、603278 gap-4.00%→执1 +14.57%，差 +3.89pp，昨日可证伪条件③触发、记错 1 笔。原因可解释：603278 深水反包（盘中最低 -8.82%）给的是盘中买点，而我的桶表只统计『开盘买→收盘卖』，漏掉了『低开深水』这类可执行形态。假设：连板≥4×炸0 中 gap<-3% 的子集（深水反包）应单独建桶，明日用 n≥10 的子集验证，区分度<3pp 不立项。"
    })
conds = [c for c in j["判断"]["可证伪条件"]]
if not any("深水反包" in c for c in conds):
    conds.append("⑤深水反包子桶：若 连板≥4×炸0 且 gap<-3% 的子集 n≥10 且超额≥+1.0pp → 认知⑤的假设立项，给该子桶 1.0% 权重上限；若超额<0 或 n<10 → 不立项，⑤只记『单日反证』。")
j["判断"]["可证伪条件"] = conds
json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("json 认知迭代", len(j["认知迭代"]), "可证伪", len(conds), "bytes", os.path.getsize(p))

# 2) HTML 同步
h = io.open(os.path.join(L, "limitup_body_%s.html" % d), encoding="utf-8").read()
h = h.replace("含 5 条认知 + 4 条可证伪条件 + 8 条盲区", "含 5 条认知 + 5 条可证伪条件 + 8 条盲区")
old = '<div class="trow"><b>④深水反包子桶</b>'
new = ('<div class="trow"><b>④口径修正</b> <span class="mut">若重算冰点②格两口径符号不反转（同正或同负）→ 今日“可成交判据必须含收盘仍在涨停”的修正记错。</span></div>\n'
       '<div class="trow"><b>⑤深水反包子桶</b>')
assert old in h, "④ row not found"
h = h.replace(old, new)
io.open(os.path.join(L, "limitup_body_%s.html" % d), "w", encoding="utf-8").write(h)
print("html bytes", os.path.getsize(os.path.join(L, "limitup_body_%s.html" % d)),
      "h2", h.count("<h2"), "div", h.count("<div"), h.count("</div>"), "LEDGER", h.count("<!--LEDGER-->"), h.count("<!--/LEDGER-->"))

# 3) 一致性/边界校验
import csv
codes = {r["代码"] for r in csv.DictReader(io.open(r"D:/股票数据/市场数据/20261023/zt_pool.csv", encoding="utf-8-sig"))}
print("池内", len(codes), "只")
recs = [x["代码"] for x in j["荐票"]["标的"]]
print("荐票标的 ∈ 池:", all(c in codes for c in recs), recs)
pl = json.load(io.open(os.path.join(L, "交易计划_limitup_%s.json" % d), encoding="utf-8"))
print("buys ∈ 池:", all(b["代码"] in codes for b in pl["buys"]), [b["代码"] for b in pl["buys"]],
      "权重合计", sum(b["权重"] for b in pl["buys"]))
cap = json.load(io.open(os.path.join(L, "能力回执_limitup_%s.json" % d), encoding="utf-8"))
pre = json.load(io.open(os.path.join(L, "能力预加载_%s.json" % d), encoding="utf-8"))
ids = [r["id"] for r in pre["routes"]["limitup"]["records"]]
print("回执 id 对齐:", [x["id"] for x in cap["回执"]] == ids, "决定:", [x["决定"] for x in cap["回执"]])
for f in ("limitup判断_%s.json","limitup_body_%s.html","交易计划_limitup_%s.json","能力回执_limitup_%s.json"):
    print(f % d, os.path.getsize(os.path.join(L, f % d)), "bytes")
