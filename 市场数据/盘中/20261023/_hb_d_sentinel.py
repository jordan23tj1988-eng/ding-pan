# -*- coding: utf-8 -*-
"""hb-d 13:30 哨兵: 发出版 v1 + 补正1 一致性/零后视镜/算术/闸门 校验"""
import json, os, statistics, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
V1 = os.path.join(D, "临盘决断_20261023_1330.json")
V11 = os.path.join(D, "临盘决断_20261023_1330_补正1.json")
DEC = datetime.datetime.strptime("2026-10-23 13:31:22", "%Y-%m-%d %H:%M:%S")
res = []
def chk(name, ok, detail=""):
    res.append((name, "PASS" if ok else "FAIL", detail))

fr = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
elig = [f for f in fr if datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") <= DEC]
last = elig[-1]
pcts = [r["pct"] for r in last["rows"] if r.get("pct") is not None]
med, mean = statistics.median(pcts), statistics.mean(pcts)
up, dn = sum(1 for p in pcts if p > 0), sum(1 for p in pcts if p < 0)
zt_n, dt_n = sum(1 for p in pcts if p > 9.7), sum(1 for p in pcts if p < -9.7)
p370 = [r for r in last["rows"] if r["code"] == "603370"][0]
q = json.load(open(os.path.join(D, "_hb_d_quote_1330.json"), encoding="utf-8"))["rows"]
pl = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))

v1 = json.load(open(V1, encoding="utf-8"))
chk("S01 发版 v1 存在且为合法 JSON(session=hb-d)", v1.get("session") == "hb-d" and v1.get("date") == "20261023")
chk("S02 发版不可覆盖: v1 未被补正覆盖(file mtime < 补正 mtime)",
    (not os.path.exists(V11)) or os.path.getmtime(V1) < os.path.getmtime(V11))

# 零后视镜: v1 池帧窗口必须 <= 决断时点
f0 = v1["数据新鲜度"]["池帧"]
chk("S03 v1 池帧末帧 ≤ 决断时点(零后视镜)", f0["末帧"].startswith(last["ts"][11:]) or f0["末帧"].startswith("13:30:54"),
    "v1末帧=%s vs 应=%s" % (f0["末帧"][:8], last["ts"][11:]))
chk("S04 v1 池帧帧数 = 该时点前可用帧数", f0["帧数"] == len(elig), "v1=%s 应=%d" % (f0["帧数"], len(elig)))

# 池内统计
env = v1["no_action"]["环境读数"]["昨涨停池(13:30:54)"]
chk("S05 池内中位口径(13:30:54)", ("%+.2f%%" % med) in env, "应 %+.2f%% 实文 %s" % (med, env[:24]))
chk("S06 池内均值/涨跌家数", ("%+.2f%%" % mean) in env and ("涨 %d/跌 %d" % (up, dn)) in env,
    "应 均值%+.2f 涨%d跌%d" % (mean, up, dn))
chk("S07 池内涨停/跌停家数", ("涨停 %d" % zt_n) in env and ("跌停 %d" % dt_n) in env, "应 %d/%d" % (zt_n, dt_n))
chk("S08 603370 池帧读数", ("%.2f" % p370["latest"]) in v1["no_action"]["持仓核"]["现价"] and "池帧" in v1["no_action"]["持仓核"]["现价"],
    "应 %.2f(%+.2f%%)" % (p370["latest"], p370["pct"]))

# 算术
px, cost, sh, nav = q["sh603370"]["px"], 28.11, 300, 990120.0
chk("S09 603370 对成本算术", abs((px / cost - 1) * 100 - 5.55) < 0.005, "%.4f%%" % ((px / cost - 1) * 100))
chk("S10 603370 权重算术", abs(px * sh / nav * 100 - float(v1["no_action"]["持仓核"]["对成本"].split("的 ")[1].replace("%）", "").rstrip("%)"))) < 0.01,
    v1["no_action"]["持仓核"]["对成本"])
chk("S11 002242 出口价差算术", abs((q["sz002242"]["px"] / 20.74 - 1) * 100 - 0.53) < 0.02,
    "%.2f%%" % ((q["sz002242"]["px"] / 20.74 - 1) * 100))
# 指数与昨同刻
i = q["sh000001"], q["sz399001"], q["sz399006"]
chk("S12 指数读数与文件一致", v1["no_action"]["环境读数"]["指数(13:31:18)"].startswith("上证 %.2f" % i[0]["px"]),
    v1["no_action"]["环境读数"]["指数(13:31:18)"][:40])
chk("S13 指数pp差算术(上证1.00/深成2.78/创业板4.06)",
    abs((i[0]["pct"] + 1.37) - 1.00) < 0.006 and abs((i[1]["pct"] + 1.87) - 2.78) < 0.006 and abs((i[2]["pct"] + 2.29) - 4.06) < 0.006,
    "%+.2f/%+.2f/%+.2f" % (i[0]["pct"] + 1.37, i[1]["pct"] + 1.87, i[2]["pct"] + 2.29))

# 闸门
zt, zb, dt = pl["zt"], pl["zb"], pl["dt"]
tc = pl["tc"]
zbc = len(zb) / (len(zt) + len(zb))
chk("S14 闸门 跌停<12 → FAIL(实读17)", tc["dt_zdp"] == 17 and "FAIL" in v1["闸门核销"]["10:00跌停<12"]["判定"])
chk("S15 闸门 炸板率 0.18 PASS", abs(zbc - 0.18) < 0.0005 and "PASS" in v1["闸门核销"]["盘中炸板率<0.45"]["判定"], "%.4f" % zbc)
chk("S16 涨停同比 +36.7%", abs((len(zt) / 30 - 1) * 100 - 36.7) < 0.05, "%+.1f%%" % ((len(zt) / 30 - 1) * 100))
chk("S17 DT 三读互证(tc17/fbt0/zdp16)", tc["dt_zdp"] == 17 and pl["dt_len_fbt"] == 0 and pl["dt_len_zdp"] == 16)
chk("S18 权限分级 A0/B0/C0", v1["权限分级"]["A"].startswith("0 笔") and v1["权限分级"]["B"].startswith("0 笔") and v1["权限分级"]["C"].startswith("0 笔"))
chk("S19 无动作场 fills 为空且 no_action 有结论", v1["fills"] == [] and "hb-d无动作" in v1["no_action"]["结论"])

# 防守三查 ② 双条件未达成
m = q["sh603370"]
chk("S20 防守线未触发(今低 27.62 完好 & 现价高于线)", m["low"] >= 27.62 and px > 27.62, "low=%.2f px=%.2f" % (m["low"], px))
# 引用的证据文件全部存在
ev = ["_hb_d_quote_1330.json", "_hb_d_pools_1330.json", "_hb_d_minute_603370.json",
      "realtime_ticks.jsonl", "临盘决断_20261023_1030.json", "临盘决断_20261023_0940.json"]
chk("S21 证据文件齐备", all(os.path.exists(os.path.join(D, e)) for e in ev),
    [e for e in ev if not os.path.exists(os.path.join(D, e))])
# 缺件如实标注
chk("S22 缺件如实标注(pulse/warboard/报警/执行流水)", all(
    v1["数据新鲜度"]["缺件"].get(k) == "不存在" for k in ["pulse.json", "warboard.json", "报警_20261023.jsonl", "执行流水.jsonl"]))
chk("S23 引擎账本未入账如实登记(欠账①)", "933,752.43" in v1["no_action"]["持仓核"]["账本实况"] and "欠账①" in v1["no_action"]["持仓核"]["账本实况"].replace("（欠账①", "欠账①").replace("，", ""))

# 补正文件校验
if os.path.exists(V11):
    c = json.load(open(V11, encoding="utf-8"))
    fix = " ".join(json.dumps(x, ensure_ascii=False) for x in c["修正明细"])
    chk("S24 补正1 修正帧数 243→%d" % len(elig), "243" in fix and str(len(elig)) in fix)
    chk("S25 补正1 修正池内中位 %+.2f%% 与均值 %+.2f%%" % (med, mean), ("%+.2f%%" % med) in fix and ("%+.2f%%" % mean) in fix)
    chk("S26 补正1 结论与 v1 一致(不改决策)", c["未受影响项"] and "不改" in c["性质"])
    chk("S27 补正1 记明 v1 原文保留可查", "保留" in c["口径"])
else:
    chk("S24~S27 补正1 尚未落盘", False, "补正未生成")

for n, s, d in res:
    print("[%s] %s %s" % (s, n, ("| " + str(d)) if d else ""))
fails = [r for r in res if r[1] == "FAIL"]
print("\n合计 %d 项: PASS %d / FAIL %d" % (len(res), len(res) - len(fails), len(fails)))
