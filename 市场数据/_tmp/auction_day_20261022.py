# -*- coding: utf-8 -*-
"""auction 20261022 当日原始数据核算:zt_pool/zb_pool 结构、池内逐票、炸板反证。"""
import csv, json, sys, os
BASE = r"D:\股票数据\市场数据"
D = os.path.join(BASE, "20261022")
out = {}
def rows(f):
    return list(csv.DictReader(open(os.path.join(D, f), encoding="utf-8-sig")))

zt = rows("zt_pool.csv"); zb = rows("zb_pool.csv")
pool = json.load(open(os.path.join(BASE, "_学习", "竞价池发出_20261022.json"), encoding="utf-8"))["池"]
pcode = {p["代码"] for p in pool}

def fnum(x):
    try: return float(x)
    except Exception: return None

# 池内逐票原始字段
det = []
for r in zt:
    if r["代码"] in pcode:
        amt = fnum(r["封板资金"]); mv = fnum(r["流通市值"])
        det.append(dict(代码=r["代码"], 名称=r["名称"], 涨跌幅=round(fnum(r["涨跌幅"]), 2),
                        成交额亿=round(fnum(r["成交额"])/1e8, 2), 流通亿=round(mv/1e8, 2),
                        换手=round(fnum(r["换手率"]), 2), 封单亿=round(amt/1e8, 3),
                        封单比=round(amt/mv*100, 2), 首封=r["首次封板时间"], 末封=r["最后封板时间"],
                        炸板=int(r["炸板次数"]), 涨停统计=r["涨停统计"], 连板=int(r["连板数"]),
                        行业=r["所属行业"], 封单比_成交=round(amt/fnum(r["成交额"])*100, 2)))
out["池内逐票"] = sorted(det, key=lambda x: -x["封单比"])

# 全池结构
def dist(keyf, rr):
    o = {}
    for r in rr:
        k = keyf(r)
        if k is None: continue
        o[k] = o.get(k, 0) + 1
    return o

def fdb(r):
    amt = fnum(r["封板资金"]); mv = fnum(r["流通市值"])
    if not amt or not mv: return None
    v = amt/mv*100
    return "<0.5%" if v < 0.5 else ("0.5~1.5%" if v < 1.5 else ("1.5~4%" if v < 4 else "≥4%"))

def first_hm(r):
    s = str(r["首次封板时间"]).zfill(6)
    return s[:2]+":"+s[2:4]

out["zt封单比分布"] = dist(fdb, zt)
out["zt首封时段"] = dist(lambda r: "≤09:25一字" if first_hm(r) <= "09:25" else ("09:26~09:31" if first_hm(r) <= "09:31" else ("09:32~10:30" if first_hm(r) <= "10:30" else ">10:30")), zt)
out["zt炸板分布"] = dist(lambda r: "炸0" if int(r["炸板次数"]) == 0 else ("炸1-2" if int(r["炸板次数"]) <= 2 else "炸≥3"), zt)
out["zt连板分布"] = dist(lambda r: str(r["连板数"]), zt)
out["zt合计"] = len(zt)

# 池内票的炸板情况
out["池内"] = dict(
    只数=len(det),
    一字=sum(1 for x in det if x["首封"] <= "092500"),
    封单比lt05=[x["名称"] for x in det if x["封单比"] < 0.5],
    封单比lt05只数=sum(1 for x in det if x["封单比"] < 0.5),
    未炸=sum(1 for x in det if x["炸板"] == 0),
    炸1plus=sum(1 for x in det if x["炸板"] >= 1),
    封单比均值=round(sum(x["封单比"] for x in det)/len(det), 2),
    封单额合计亿=round(sum(x["封单亿"] for x in det), 3),
    流通市值合计亿=round(sum(x["流通亿"] for x in det), 2),
)

# 炸板反证:zb_pool
zbdet = []
for r in zb:
    zbdet.append(dict(代码=r["代码"], 名称=r["名称"], 涨跌幅=round(fnum(r["涨跌幅"]), 2),
                      首封=first_hm(r), 炸板=int(r["炸板次数"]), 涨停统计=r["涨停统计"],
                      行业=r["所属行业"], 换手=round(fnum(r["换手率"]), 2),
                      成交额亿=round(fnum(r["成交额"])/1e8, 2)))
out["zb首封≤0931"] = sum(1 for x in zbdet if x["首封"] <= "09:31")
out["zb首封≤0925"] = sum(1 for x in zbdet if x["首封"] <= "09:25")
out["zb合计"] = len(zbdet)
out["zb按首封分段"] = dist(lambda x: "≤09:25" if x["首封"] <= "09:25" else ("09:26~09:31" if x["首封"] <= "09:31" else (">09:31")), zbdet)
out["zb明细首封≤0931"] = [x for x in zbdet if x["首封"] <= "09:31"]
out["zb跌幅<=-9%只数"] = sum(1 for x in zbdet if x["涨跌幅"] <= -9)

# 竞价首封≤09:31 的"候选池"最终存活率(封住 vs 炸板)
out["竞价候选存活"] = dict(
    封住=sum(1 for r in zt if first_hm(r) <= "09:31"),
    炸板=out["zb首封≤0931"],
    存活率pct=round(sum(1 for r in zt if first_hm(r) <= "09:31")/(sum(1 for r in zt if first_hm(r) <= "09:31")+out["zb首封≤0931"])*100, 1),
)

json.dump(out, open(os.path.join(BASE, "_学习", "子agent增强", "auction_当日结构_20261022.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in out.items():
    if k == "池内逐票":
        for x in v: print(json.dumps(x, ensure_ascii=False))
    else:
        print("##", k, json.dumps(v, ensure_ascii=False))
