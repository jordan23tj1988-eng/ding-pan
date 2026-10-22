# -*- coding: utf-8 -*-
"""hb-e 14:30 决断件哨兵: 逐项回源核对(数字必须能从源文件复现)"""
import json, os, datetime, urllib.request

D = r"D:\股票数据\市场数据\盘中\20261022"
R = []          # (id, desc, pass, detail)
def chk(i, desc, ok, detail=""):
    R.append((i, desc, bool(ok), detail))

J = json.load(open(os.path.join(D, "临盘决断_20261022_1430.json"), encoding="utf-8"))
Q = json.load(open(os.path.join(D, "_hb_e_quote_1430.json"), encoding="utf-8"))
P = json.load(open(os.path.join(D, "_hb_e_pools_1430.json"), encoding="utf-8"))
F = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
t = lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

chk(1, "决断件JSON可解析且session=hb-e/ts=14:30", J["session"] == "hb-e" and J["ts"] == "14:30", J["session"] + J["ts"])
chk(2, "fills为空(本场不产生撮合)", J["fills"] == [] and J["权限分级"]["A"].startswith("0"), str(J["fills"]))
chk(3, "发出版唯一(临盘决断_*_1430 仅1个, 未被覆盖)", len([f for f in os.listdir(D) if f.startswith("临盘决断_20261022_1430")]) == 1,
    str([f for f in os.listdir(D) if f.startswith("临盘决断_20261022")]))

# 池帧
live = F[-1]
F = [f for f in F if f["ts"] <= "2026-10-22 14:31:12"]   # 决断时点快照(零后视镜)
last = F[-1]
chk(4, "决断时点末帧=14:31:12 且未stale", last["ts"] == "2026-10-22 14:31:12" and last["pool_stale"] is False,
    last["ts"] + " | 哨兵运行时活帧 %s" % live["ts"])
chk(5, "决断时点帧数300/窗口起点09:31:08", len(F) == 300 and F[0]["ts"] == "2026-10-22 09:31:08", "%d %s" % (len(F), F[0]["ts"]))
mx = max(((t(b["ts"]) - t(a["ts"])).total_seconds(), b["ts"]) for a, b in zip(F, F[1:]))
chk(6, "最大帧间隔68s(断更<600s)", mx[0] == 68, str(mx))

# 002242 现价/涨幅(c5)
m = {r["code"]: r for r in last["rows"]}
chk(7, "池帧002242=21.37/-5.53%", m["002242"]["latest"] == 21.37 and round(m["002242"]["pct"], 2) == -5.53,
    "%s %.2f%%" % (m["002242"]["latest"], m["002242"]["pct"]))
chk(8, "腾讯002242=21.39", Q["rows"]["sz002242"]["px"] == 21.39, str(Q["rows"]["sz002242"]["px"]))
chk(9, "腾讯002242今低=20.50/今高=22.08", Q["rows"]["sz002242"]["low"] == 20.50 and Q["rows"]["sz002242"]["high"] == 22.08,
    "%s/%s" % (Q["rows"]["sz002242"]["low"], Q["rows"]["sz002242"]["high"]))

# 触发条件复算
tr = [(f["ts"], {r["code"]: r for r in f["rows"]}.get("002242")) for f in F]
tr = [(ts, r) for ts, r in tr if r]
lo_ts, lo_v = min(((ts, r["latest"]) for ts, r in tr), key=lambda x: x[1])
chk(10, "池帧002242最低=20.59 @14:02:07", lo_v == 20.59 and lo_ts == "2026-10-22 14:02:07", "%s @%s" % (lo_v, lo_ts))
i = [k for k, (ts, _) in enumerate(tr) if ts == "2026-10-22 14:02:07"][0]
j = i
while j > 0 and (t(tr[i][0]) - t(tr[j - 1][0])).total_seconds() <= 300:
    j -= 1
hi5 = max(x[1]["latest"] for x in tr[j:i + 1])
drop5 = (tr[i][1]["latest"] / hi5 - 1) * 100
chk(11, "14:02:07 5分钟跌幅=-3.87%(窗口高21.42)", round(drop5, 2) == -3.87 and hi5 == 21.42, "%.2f%% hi=%.2f" % (drop5, hi5))
chk(12, "双条件成立(新低20.59<20.90 且 -3.87%≤-2%)", lo_v < 20.90 and drop5 <= -2.0, "")
# 前一日内低 <20.90 的第一次探底时刻(池帧内 20.90 附近)
below = [(ts, r["latest"]) for ts, r in tr if r["latest"] < 20.90]
chk(13, "20.90以下仅在14:02后出现(前场20.90为日内低)", below and below[0][0] == "2026-10-22 14:02:07", str(below[:3]))

# 池计数
chk(14, "涨停32/炸板22/跌停27", len(P["zt"]) == 32 and len(P["zb"]) == 22 and len(P["dt"]) == 27,
    "%d/%d/%d" % (len(P["zt"]), len(P["zb"]), len(P["dt"])))
chk(15, "炸板率0.4074", abs(len(P["zb"]) / (len(P["zt"]) + len(P["zb"])) - 0.4074) < 0.0001, "%.4f" % (len(P["zb"]) / (len(P["zt"]) + len(P["zb"]))))
lb = {}
for p in P["zt"]:
    lb[p["lbc"]] = lb.get(p["lbc"], 0) + 1
chk(16, "连板分布{1:23,2:5,3:2,5:2}", lb == {1: 23, 2: 5, 3: 2, 5: 2}, str(dict(sorted(lb.items()))))
chk(17, "DT池fbt排序仍返回0(陷阱对照)", P["dt_fbt_sort_count"] == 0 and P["rc"] == [0, 0, 0, 0], str(P["rc"]))
# 跌停名单关键票在跌停价
dtset = {p["c"] for p in P["dt"]}
need = {"002469", "002085", "001317", "600860", "002388", "002347", "002980"}
chk(18, "跌停名单含002469/002085/001317/600860/002388/002347/002980", need <= dtset, str(sorted(need - dtset)))
dt_p = {p["c"]: p["p"] for p in P["dt"]}
chk(19, "002388在跌停价8.19(东财池p=8190, 口径=价×1000)", dt_p.get("002388") == 8190, str(dt_p.get("002388")))

# 指数
def idx(code, pct):
    return Q["rows"][code]["pct"] == pct
chk(20, "指数 -1.15/-2.12/-3.06", idx("sh000001", -1.15) and idx("sz399001", -2.12) and idx("sz399006", -3.06),
    "%s/%s/%s" % (Q["rows"]["sh000001"]["pct"], Q["rows"]["sz399001"]["pct"], Q["rows"]["sz399006"]["pct"]))

# 池内宽度
def stat(fr):
    v = sorted(r["pct"] for r in fr["rows"]); n = len(v)
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    return round(med, 2), sum(1 for x in v if x >= 9), sum(1 for x in v if x <= -9)
s_last = stat(last)
ref1333 = [f for f in F if f["ts"] <= "2026-10-22 13:33:10"][-1]
ref1104 = [f for f in F if f["ts"] <= "2026-10-22 11:05:00"][-1]
chk(21, "池内中位 -2.92 / -1.36 / 0.47", s_last[0] == -2.92 and stat(ref1333)[0] == -1.36 and stat(ref1104)[0] == 0.47,
    "%s / %s / %s" % (s_last[0], stat(ref1333)[0], stat(ref1104)[0]))
chk(22, "≤-9% 7/6/2", s_last[2] == 7 and stat(ref1333)[2] == 6 and stat(ref1104)[2] == 2,
    "%d/%d/%d" % (s_last[2], stat(ref1333)[2], stat(ref1104)[2]))
chk(23, "≥+9% 10/9/9", s_last[1] == 10 and stat(ref1333)[1] == 9 and stat(ref1104)[1] == 9,
    "%d/%d/%d" % (s_last[1], stat(ref1333)[1], stat(ref1104)[1]))

# 13:34 DT=16 对照
dtfx = json.load(open(os.path.join(D, "_hb_d_pools_1330_dtfix.json"), encoding="utf-8"))
n16 = dtfx.get("n")
chk(24, "13:34 DT池修正值=16(前场留档)", n16 == 16 and len(dtfx.get("pool") or []) == 16, str(n16))

# 成本数学
cost_amt = 21.69 * 900
pnl = 21.37 * 900 - cost_amt
chk(25, "成本19521/浮亏-288/-1.48%", abs(cost_amt - 19521) < 1e-9 and abs(pnl + 288) < 1e-9 and round((21.37 / 21.69 - 1) * 100, 2) == -1.48,
    "%.2f %.2f" % (cost_amt, pnl))

# 002639/002076/002724/603278/600293/601091/002696 照会数字
o = Q["rows"]
chk(26, "002639=15.29 未破15.20", o["sz002639"]["px"] == 15.29 and o["sz002639"]["px"] > 15.20, str(o["sz002639"]["px"]))
chk(27, "002076=2.70(+10.20%)/002724=11.21/603278=14.51/600293=5.23",
    o["sz002076"]["px"] == 2.70 and o["sz002724"]["px"] == 11.21 and o["sh603278"]["px"] == 14.51 and o["sh600293"]["px"] == 5.23,
    "%s/%s/%s/%s" % (o["sz002076"]["px"], o["sz002724"]["px"], o["sh603278"]["px"], o["sh600293"]["px"]))
chk(28, "601091现价=涨停价21.58(回封)", o["sh601091"]["px"] == 21.58, "%s" % o["sh601091"]["px"])
ztp = {p["c"]: p.get("ztp") for p in P["zb"]}
chk(29, "601091 东财ztp=21580(=现价)", ztp.get("601091") == 21580, str(ztp.get("601091")))
chk(30, "002696=10.22(-2.85%) 今高11.57曾触板", o["sz002696"]["px"] == 10.22 and o["sz002696"]["high"] == 11.57, "%s hi=%s" % (o["sz002696"]["px"], o["sz002696"]["high"]))
chk(31, "000530=9.43 未封(涨停价9.49)", o["sz000530"]["px"] == 9.43 and ztp.get("000530") == 9490, "%s" % o["sz000530"]["px"])

# 断更判定一致性: 末帧龄写件时 <600s
age = (datetime.datetime.now() - t(last["ts"])).total_seconds()
chk(32, "决断时点末帧龄<600s(可决策)", (datetime.datetime.strptime(J["write_ts"], "%Y-%m-%d %H:%M:%S") - t(last["ts"])).total_seconds() < 600,
    "%.0fs" % (datetime.datetime.strptime(J["write_ts"], "%Y-%m-%d %H:%M:%S") - t(last["ts"])).total_seconds())
DRIFT = {"活帧": live["ts"], "002242现价": {r["code"]: r for r in live["rows"]}.get("002242", {}).get("latest"),
         "002242现涨幅": round({r["code"]: r for r in live["rows"]}.get("002242", {}).get("pct", 0), 2)}
# 002242 从未涨停(无板可炸)
chk(33, "002242今日未触涨停(高22.08<昨收22.62)", Q["rows"]["sz002242"]["high"] < Q["rows"]["sz002242"]["pre"], "hi=%.2f pre=%.2f" % (Q["rows"]["sz002242"]["high"], Q["rows"]["sz002242"]["pre"]))

print("=" * 96)
ok = 0
for i, desc, p, det in R:
    print("%-4s %-52s %s  %s" % ("C%d" % i, desc, "PASS" if p else "FAIL", det))
    ok += p
print("=" * 96)
print("TOTAL %d/%d PASS" % (ok, len(R)))
print("DRIFT(哨兵运行时, 仅记录不入决断): %s" % DRIFT)
if ok != len(R):
    raise SystemExit(1)
