# -*- coding: utf-8 -*-
"""hb-e(20261015 14:30) 自审哨兵: 校验决断文件与留档数据一致、无后视镜、无编造。"""
import json, os, io, statistics as st
from datetime import datetime

D = r"D:\股票数据\市场数据\盘中\20261015"
fp = os.path.join(D, "临盘决断_20261015_1430.json")
fails, oks = [], []
def ck(name, cond, detail=""):
    (oks if cond else fails).append("%s %s" % (name, detail))

d = json.load(open(fp, encoding="utf-8"))
ck("C1_可解析", True)
req = ["date","session","ts","write_ts","交易日校验","数据新鲜度","在持票照会","A级_预案内",
       "B级_防守","C级_预案外","fills","no_action","深场B备料_1445","后视镜边界声明","report"]
miss = [k for k in req if k not in d]
ck("C2_必备字段齐", not miss, "缺失=%s" % miss)
ck("C3_日期场次", d["date"] == "20261015" and d["session"] == "hb-e" and d["ts"] == "14:30", d["date"]+"/"+d["session"]+"/"+d["ts"])

# 帧与后视镜（★决策快照冻结: 该 ticks 文件为盘中实时追加, 必须按 ts<=决断末帧 截断, 否则哨兵会与"仍在增长的文件"比较→假 FAIL）
DECISION_FRAME = "2026-10-15 14:35:01"
frames = []
for line in io.open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8"):
    line = line.strip()
    if line:
        o = json.loads(line); ts = datetime.strptime(o["ts"], "%Y-%m-%d %H:%M:%S")
        if ts <= datetime.strptime(DECISION_FRAME, "%Y-%m-%d %H:%M:%S"):
            frames.append((ts, o))
frames.sort(key=lambda x: x[0])
last_ts = frames[-1][0]
wts = datetime.strptime(d["write_ts"], "%Y-%m-%d %H:%M:%S")
ck("C4_无后视镜_帧", last_ts <= wts, "决策末帧=%s write_ts=%s" % (last_ts, wts))
q = json.load(open(os.path.join(D, "_hb_e_quote.json"), encoding="utf-8"))
qmax = max(datetime.strptime(v["time"], "%Y%m%d%H%M%S") for v in q.values())
ck("C5_无后视镜_行情", qmax <= wts, "行情最大戳=%s" % qmax)
ck("C6_新鲜度", (wts - last_ts).total_seconds() <= 600, "滞后=%.0fs" % (wts-last_ts).total_seconds())
ck("C7_新鲜度声明", d["数据新鲜度"]["末帧"] == last_ts.strftime("%Y-%m-%d %H:%M:%S"),
   "声明=%s 实测=%s" % (d["数据新鲜度"]["末帧"], last_ts.strftime("%Y-%m-%d %H:%M:%S")))

# 派生数重算
ck("C8_持仓数=3", len(d["在持票照会"]["持仓"]) == 3)
for h in d["在持票照会"]["持仓"]:
    r = q[h["code"]]
    ck("C8a_%s_相对成本"%h["code"], abs(h["相对成本pct"] - round((r["last"]/h["cost_px"]-1)*100,2)) < 0.01,
       "声明%+.2f 重算%+.2f" % (h["相对成本pct"], round((r["last"]/h["cost_px"]-1)*100,2)))
    ck("C8b_%s_浮盈"%h["code"], abs(h["浮动盈亏_元"] - round((r["last"]-h["cost_px"])*h["shares"],2)) < 0.01,
       "声明%+.2f 重算%+.2f" % (h["浮动盈亏_元"], round((r["last"]-h["cost_px"])*h["shares"],2)))
    ck("C8c_%s_行情戳一致"%h["code"], h["行情戳"] == r["time"], h["行情戳"])

# 池况重算
def ztpx(r):
    pc = r["preClose"]; lim = 0.20 if str(r["code"]).startswith(("30","68")) else 0.10
    return round(pc*(1+lim),2), lim
last = {r["code"]: r for r in frames[-1][1]["rows"]}
feng = sum(1 for r in last.values() if r["latest"] >= ztpx(r)[0]-0.001)
dt = sum(1 for r in last.values() if ztpx(r)[1]==0.10 and r["latest"] <= round(r["preClose"]*0.9,2)+0.001)
zha = sum(1 for r in last.values() if r["latest"] < ztpx(r)[0]-0.001 and r["high"] >= ztpx(r)[0]-0.001)
med = round(st.median([r["pct"] for r in last.values()]), 2)
pc_claim = d["B级_防守"]["通道C_持仓炸板"]["池况_尾盘1小时对比"]["本场末帧 14:34:01"]
ck("C9_池况重算", (feng, dt, zha, med) == (pc_claim["封板"], pc_claim["跌停"], pc_claim["炸板"], pc_claim["中位pct"]),
   "声明=%s 重算=%s" % ((pc_claim["封板"],pc_claim["跌停"],pc_claim["炸板"],pc_claim["中位pct"]), (feng,dt,zha,med)))
ck("C9b_末帧标识", d["数据新鲜度"]["帧数"] == len(frames) and last_ts.strftime("%H:%M:%S") == "14:35:01",
   "帧数=%d 末帧时刻=%s" % (len(frames), last_ts.strftime("%H:%M:%S")))

# 600693 不可成交声明 ↔ 盘口
h6 = [h for h in d["在持票照会"]["持仓"] if h["code"]=="600693"][0]
ck("C10_600693不可成交声明", h6["bid1"] == 0.0 and h6["今日最高"] == h6["今日最低"] == h6["决断时点实价"],
   "bid1=%s 开=高=低=%.2f" % (h6["bid1"], h6["决断时点实价"]))

# fills 完整性
ck("C11_fills空集一致", d["fills"] == [] and d["A级_合计"]["笔数"] == 0)
ck("C12_B级与no_action", d["B级_防守"]["触发"] is True and d["no_action"] is False)
ck("C13_C级禁行", d["C级_预案外"]["许可"] is False and "零 C 级" in d["C级_预案外"]["本场动作"])
ck("C14_备料非空", len(d["深场B备料_1445"]["尾盘卖预案候选"]) >= 4 and len(d["深场B备料_1445"]["明日预案要点草稿"]) >= 3)

# 605577 回撤三条件自检
h5 = [h for h in d["在持票照会"]["持仓"] if h["code"]=="605577"][0]
cond = (h5["相对成本pct"] < 0) and (h5["自今日高点回撤pct"] <= -10) and (h5["较13:30场变动_pp"] <= -3)
ck("C15_605577回撤三条件", cond, "相对成本%+.2f 自高%+.2f 较前场%+.2f" % (h5["相对成本pct"], h5["自今日高点回撤pct"], h5["较13:30场变动_pp"]))

print("== hb-e 哨兵 ==")
for x in oks: print("  PASS", x)
for x in fails: print("  FAIL", x)
print("RESULT:", "PASS 全通过(%d/%d)" % (len(oks), len(oks)+len(fails)) if not fails else "FAIL %d项" % len(fails))
import sys; sys.exit(1 if fails else 0)
