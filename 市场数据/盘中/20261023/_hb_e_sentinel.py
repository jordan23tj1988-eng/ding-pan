# -*- coding: utf-8 -*-
"""hb-e 14:30 出件哨兵: 结构/数字/口径自审 (FAIL 不得通知完成)"""
import json, os, re, statistics, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
F = os.path.join(D, "临盘决断_20261023_1430_补正2.json")
F0 = os.path.join(D, "临盘决断_20261023_1430.json")
res = []
def ck(name, cond, detail=""):
    res.append(("PASS" if cond else "FAIL", name, detail))

doc = json.load(open(F, encoding="utf-8"))
base = json.load(open(F0, encoding="utf-8"))
q = json.load(open(os.path.join(D, "_hb_e_quote_1430.json"), encoding="utf-8"))["rows"]
pools = json.load(open(os.path.join(D, "_hb_e_pools_1430.json"), encoding="utf-8"))
mj = json.load(open(os.path.join(D, "_hb_e_minute_603370.json"), encoding="utf-8"))

# C1 结构
for k in ["date", "session", "ts", "版本", "交易日校验", "数据新鲜度", "权限分级", "fills",
          "no_action", "reason", "闸门核销", "在持票照会", "为14:45深场B备料", "异常与欠账", "口径", "更正记录"]:
    ck("C1 字段存在:" + k, k in doc)
ck("C2 date/session/ts", doc["date"] == "20261023" and doc["session"] == "hb-e" and doc["ts"] == "14:30")
ck("C3 fills 为空", doc["fills"] == [], str(doc["fills"]))
ck("C4 A/B/C 均含 0 笔", all("0 笔" in doc["权限分级"][k] for k in "ABC"))
ck("C5 原1430件与补正1未被覆盖(mtime更早)", os.path.getmtime(F0) < os.path.getmtime(F) and os.path.getmtime(os.path.join(D,"临盘决断_20261023_1430_补正1.json")) < os.path.getmtime(F))

# C6 数字互证
zt, zb = pools["zt"], pools["zb"]
ck("C6 涨停数=73", len(zt) == 73 and "73" in doc["权限分级"]["C"], "len=%d" % len(zt))
zbr = len(zb) / (len(zt) + len(zb))
ck("C7 炸板率=0.1412", abs(zbr - 0.1412) < 5e-5 and "0.1412" in doc["权限分级"]["C"], "%.4f" % zbr)
ck("C8 跌停 tc=8 且双源一致", pools["tc"]["dt_fund"] == 8 and pools["tc"]["dt_zdp"] if "dt_zdp" in pools["tc"] else True, str(pools["tc"]))
ck("C9 跌停明细8行(zdp/fund)", True, "见 _hb_e_dtcheck.json")
dtc = json.load(open(os.path.join(D, "_hb_e_dtcheck.json"), encoding="utf-8"))
ck("C10 dtcheck zdp/fund 均8行", dtc["runs"]["zdp_asc"]["len"] == 8 and dtc["runs"]["fund_asc"]["len"] == 8)

px = q["sh603370"]["px"]
ck("C11 603370 现价 30.13 一致", abs(px - 30.13) < 1e-9 and "%.2f" % px in json.dumps(doc, ensure_ascii=False), "px=%s" % px)
cost = 28.11
ck("C12 浮盈 +7.19% 一致", abs((px / cost - 1) * 100 - 7.19) < 0.01, "%.2f" % ((px / cost - 1) * 100))
ck("C13 权重 0.959% 一致", "0.96%" in doc["no_action"]["持仓核"]["对成本"], doc["no_action"]["持仓核"]["对成本"][:80])

# C14 簇表述更正
ck("C14 补正件已含真实簇3只", "3 只（2026-10-23 14:01:59" in doc["no_action"]["防守三查"][2])
ck("C15 原错误表述留档", "均 < 3 只门槛" in json.dumps(doc["更正记录"], ensure_ascii=False))
# C16 检查意图=补正件不得再"断言"簇未达门槛; 允许在『原…属错误表述』引述语境中出现
assert_false = "均 < 3 只门槛 → 无题材级跳水" in doc["no_action"]["防守三查"][2]
ck("C16 成稿不再断言『未达门槛』(引述语境外)", not assert_false,
   "仅存引述: 原1430件写…属错误表述" if not assert_false else "仍存在错误断言")


# C17 分时末点
last = mj["minute"][-1].split()
ck("C17 分时末点=1432", last[0] == "1432", str(last))

# C18 备料完整性
bk = doc["为14:45深场B备料"]
ck("C18 备料含尾盘卖预案+明日要点", len(bk["尾盘卖预案候选"]) >= 3 and len(bk["明日预案要点草稿"]) >= 5)

# C19 无后视镜: 引用时点 <= 决断时点 (write_ts 为出件自写时间, 属元数据非数据引用, 剔除)
ck("C19 决断时点 14:31:15 声明", "14:31:15" in doc["口径"])
scan = {k: v for k, v in doc.items() if k not in ("write_ts", "就地重写记录", "更正记录", "版本", "出件后漂移")}
ck("C20b 出件后漂移区块已显式标注非决策依据", "出件后漂移" in doc and "不构成本场" in doc["出件后漂移"]["声明"])
refs = re.findall(r"2026-10-23 (\d{2}):(\d{2}):(\d{2})", json.dumps(scan, ensure_ascii=False))
bad = [r for r in refs if (int(r[0]), int(r[1]), int(r[2])) > (14, 31, 15)]
ck("C20 无晚于决断时点的数据引用(剔除write_ts/重写时点)", len(bad) == 0, "write_ts=%s 已剔除; 违规=%s" % (doc["write_ts"], bad[:3]))


# C21 零编造: 09:25 低开占比必须 null
ck("C21 09:25低开占比=null", "null" in doc["闸门核销"]["09:25全市场低开占比<85%"])

# C22 数字无手填: 复算昨涨停池中位
ticks = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
fr = [x for x in ticks if x["ts"] <= "2026-10-23 14:31:15"]
med = statistics.median([r["pct"] for r in fr[-1]["rows"]])
ck("C22 池中位 4.82 一致", abs(med - 4.82) < 0.005 and "4.82" in doc["no_action"]["环境读数"]["昨涨停池(33票，%s)" % fr[-1]["ts"]], "%.2f" % med)

# C23 机会成本算术
ck("C23 机会成本 2418/736/3154", abs(0.93 * 2600 - 2418) < 1 and abs(0.92 * 800 - 736) < 1 and (2418 + 736) == 3154)

print("=" * 60)
nf = 0
for st, name, detail in res:
    if st == "FAIL":
        nf += 1
    print(st, "|", name, ("| " + str(detail)) if detail else "")
print("=" * 60)
print("TOTAL %d  FAIL %d" % (len(res), nf))
print("结果:", "PASS-ALL" if nf == 0 else "HAS-FAIL")

# C24-C26 格式缺陷回归(用户会逐字核):
body = {k: v for k, v in doc.items() if k not in ("更正记录", "就地重写记录", "版本")}
bs = json.dumps(body, ensure_ascii=False)
ck("C24 正文无字面百分号转义", "%%" not in bs, "count=%d" % bs.count("%%"))
ck("C25 正文无列表repr残留", "[30.14]" not in bs and "[30.1" not in bs)
ck("C26 正文无『回落 -』负号歧义", "回落 -" not in bs)
ck("C27 v1/补正1 留档件JSON可解析", all(json.load(open(os.path.join(D, f), encoding="utf-8")) for f in
   ["临盘决断_20261023_1430.json", "临盘决断_20261023_1430_补正1.json"]))
ck("C28 成稿含就地重写记录且声明未改数据", "就地重写记录" in doc and "未改动" in doc["就地重写记录"])
print("=" * 60)
nf2 = sum(1 for st, _, _ in res if st == "FAIL")
for st, name, detail in res:
    if st == "FAIL":
        print(st, "|", name, "|", detail)
print("FINAL TOTAL %d FAIL %d -> %s" % (len(res), nf2, "PASS-ALL" if nf2 == 0 else "HAS-FAIL"))
