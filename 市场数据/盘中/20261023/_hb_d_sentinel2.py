# -*- coding: utf-8 -*-
"""hb-d 13:30 哨兵 v2: 发版 v1 + 补正1 合并视图 vs 原始数据重算
   用法: python _hb_d_sentinel2.py [补正路径(默认: 正式路径, 缺则用草稿)]
"""
import json, os, sys, statistics, datetime

D = r"D:\股票数据\市场数据\盘中\20261023"
V1 = os.path.join(D, "临盘决断_20261023_1330.json")
V11 = os.path.join(D, "临盘决断_20261023_1330_补正1.json")
DRAFT = os.path.join(D, "_tmp_补正1_draft.json")
if len(sys.argv) > 1:
    V11 = sys.argv[1]
elif not os.path.exists(V11) and os.path.exists(DRAFT):
    V11 = DRAFT
DEC = datetime.datetime.strptime("2026-10-23 13:31:22", "%Y-%m-%d %H:%M:%S")
res = []
def chk(n, ok, d=""):
    res.append((n, "PASS" if ok else "FAIL", d))

fr = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
elig = [f for f in fr if datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") <= DEC]
last = elig[-1]
pcts = [r["pct"] for r in last["rows"] if r.get("pct") is not None]
med, mean = statistics.median(pcts), statistics.mean(pcts)
up, dn = sum(1 for p in pcts if p > 0), sum(1 for p in pcts if p < 0)
p370 = [r for r in last["rows"] if r["code"] == "603370"][0]
q = json.load(open(os.path.join(D, "_hb_d_quote_1330.json"), encoding="utf-8"))["rows"]
pl = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))
v1 = json.load(open(V1, encoding="utf-8"))
px, cost, sh, nav = q["sh603370"]["px"], 28.11, 300, 990120.0

# ---------- A. 发版 v1 原文完整性 ----------
chk("S01 v1 合法且 session=hb-d/date=20261023", v1.get("session") == "hb-d" and v1.get("date") == "20261023")
chk("S02 发版不可覆盖: v1 mtime ≤ 补正 mtime", (not os.path.exists(V11)) or os.path.getmtime(V1) <= os.path.getmtime(V11),
    "v1=%.1f v11=%.1f" % (os.path.getmtime(V1), os.path.getmtime(V11) if os.path.exists(V11) else -1))
chk("S03 v1 原文偏差已登记(池帧 243 帧 / 末帧 13:33:54 越界)", v1["数据新鲜度"]["池帧"]["帧数"] != len(elig))
chk("S04 v1 结论字段齐备(fills=[] + no_action 结论)", v1["fills"] == [] and "无动作" in v1["no_action"]["结论"])

# ---------- B. 合并视图(v1 + 补正) vs 原始数据 ----------
c = json.load(open(V11, encoding="utf-8")) if os.path.exists(V11) else None
fix_txt = " ".join(json.dumps(x, ensure_ascii=False) for x in c["修正明细"]) if c else ""
chk("S05 合并视图: 池帧帧数 = 决断时点前可用帧数", ("帧数 %d" % len(elig)) in fix_txt, "应 %d" % len(elig))
chk("S06 合并视图: 末帧 13:30:54", "09:31:07~13:30:54" in fix_txt)
chk("S07 合并视图: 池内中位 %+.2f%%" % med, ("中位 %+.2f%%" % med) in fix_txt)
chk("S08 合并视图: 池内均值 %+.2f%% / 涨%d跌%d" % (mean, up, dn), ("均值 %+.2f%%" % mean) in fix_txt and ("涨 %d/跌 %d" % (up, dn)) in fix_txt)
chk("S09 合并视图: 603370 池帧 %.2f(%+.2f%%)" % (p370["latest"], p370["pct"]), ("%.2f（%+.2f%%）" % (p370["latest"], p370["pct"])) in fix_txt)

# ---------- C. 决策与算术重算 ----------
chk("S10 603370 对成本 +5.55%", abs((px / cost - 1) * 100 - 5.55) < 0.005, "%.4f%%" % ((px / cost - 1) * 100))
chk("S11 603370 权重 0.90%", abs(px * sh / nav * 100 - 0.90) < 0.006, "%.4f%%" % (px * sh / nav * 100))
chk("S12 002242 出口价差 +0.53%%（20.74→%.2f）" % q["sz002242"]["px"], abs((q["sz002242"]["px"] / 20.74 - 1) * 100 - 0.53) < 0.02,
    "%+.2f%%" % ((q["sz002242"]["px"] / 20.74 - 1) * 100))
chk("S13 防守线未触发(今低 27.62 完好 & 现价高于线)", q["sh603370"]["low"] >= 27.62 and px > 27.62,
    "low=%.2f px=%.2f" % (q["sh603370"]["low"], px))
i0, i1, i2 = q["sh000001"], q["sz399001"], q["sz399006"]
chk("S14 指数读数与报价文件一致", v1["no_action"]["环境读数"]["指数(13:31:18)"].startswith("上证 %.2f" % i0["px"]),
    v1["no_action"]["环境读数"]["指数(13:31:18)"][:46])
chk("S15 指数 pp 差 +1.00/+2.78/+4.06", abs((i0["pct"] + 1.37) - 1.00) < 0.006 and abs((i1["pct"] + 1.87) - 2.78) < 0.006 and abs((i2["pct"] + 2.29) - 4.06) < 0.006,
    "%+.2f/%+.2f/%+.2f" % (i0["pct"] + 1.37, i1["pct"] + 1.87, i2["pct"] + 2.29))
zt, zb, tc = pl["zt"], pl["zb"], pl["tc"]
zbc = len(zb) / (len(zt) + len(zb))
chk("S16 闸门 跌停<12 FAIL(tc=17)", tc["dt_zdp"] == 17 and "FAIL" in v1["闸门核销"]["10:00跌停<12"]["判定"])
chk("S17 闸门 炸板率 %.4f PASS(<0.45)" % zbc, abs(zbc - 0.18) < 0.0005 and "PASS" in v1["闸门核销"]["盘中炸板率<0.45"]["判定"])
chk("S18 涨停同比 +36.7%(41 vs 昨同刻30)", abs((len(zt) / 30 - 1) * 100 - 36.7) < 0.05, "%+.1f%%" % ((len(zt) / 30 - 1) * 100))
chk("S19 DT 决断证据只用 tc(明细 0 行已登记)", pl["dt_len_fbt"] == 0 and pl["dt_len_zdp"] == 0 and v1["数据新鲜度"]["市场闸门源"]["跌停_明细_fbt"] == 0)
chk("S20 权限分级 A0/B0/C0", v1["权限分级"]["A"].startswith("0 笔") and v1["权限分级"]["B"].startswith("0 笔") and v1["权限分级"]["C"].startswith("0 笔"))
chk("S21 补正1 已把 DT 明细旁证降级为事后复核", ("事后探针" in fix_txt) and ("非决断证据" in fix_txt or "降级" in fix_txt))
chk("S22 补正1 声明不改决策", ("不改任何决策" in c["口径"] and "无动作" in c["未受影响项"][0]) if c else False)
chk("S23 补正1 声明 v1 原文保留可查", ("补正" in c["口径"] and "保留" in c["口径"]) if c else False)
chk("S24 补正1 记明根因(fr[-1] 取帧 / 双 sort 参数)", (("fr[-1]" in c["发现方式"]) and ("sort" in c["发现方式"])) if c else False)

# ---------- D. 证据与缺件 ----------
ev = ["_hb_d_quote_1330.json", "_hb_d_pools_1330.json", "_hb_d_minute_603370.json",
      "realtime_ticks.jsonl", "临盘决断_20261023_1030.json", "临盘决断_20261023_0940.json"]
chk("S25 证据文件齐备", all(os.path.exists(os.path.join(D, e)) for e in ev), [e for e in ev if not os.path.exists(os.path.join(D, e))])
miss = v1["数据新鲜度"]["缺件"]
chk("S26 缺件如实标注(4 项均以『不存在』开头)", all(str(miss.get(k, "")).startswith("不存在") for k in ["pulse.json", "warboard.json", "报警_20261023.jsonl", "执行流水.jsonl"]))
chk("S27 引擎未入账如实登记(欠账①)", "933,752.43" in v1["no_action"]["持仓核"]["账本实况"])
chk("S28 零后视镜: 报价 t ≤ 决断时点", all(str(q[k]["t"]) <= "20261023133122" for k in ("sh603370", "sz002242", "sh000001")))

for n, s, d in res:
    print("[%s] %s %s" % (s, n, ("| " + str(d)) if d else ""))
fails = [r for r in res if r[1] == "FAIL"]
print("\n合计 %d 项: PASS %d / FAIL %d" % (len(res), len(res) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
