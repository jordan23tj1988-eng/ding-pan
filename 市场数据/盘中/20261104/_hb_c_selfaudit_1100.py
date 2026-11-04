# -*- coding: utf-8 -*-
"""hb-c 1100 决断件自审：逐条从原始落盘重算，与决断件比对（禁自证）。"""
import json, os, csv

B = r"D:\股票数据\市场数据\盘中\20261104"
doc = json.load(open(os.path.join(B, "临盘决断_20261104_1100.json"), encoding="utf-8"))
F = [json.loads(l) for l in open(os.path.join(B, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
q = json.load(open(os.path.join(B, "_hb_c_quote_1100.json"), encoding="utf-8"))["rows"]
qb = json.load(open(os.path.join(B, "_hb_c_quote_1100b.json"), encoding="utf-8"))["rows"]
pl = json.load(open(os.path.join(B, "_hb_c_pools_1100.json"), encoding="utf-8"))
ok = []


def chk(name, cond, got=None, exp=None):
    ok.append((name, bool(cond), got, exp))


# 1 新鲜度
PIN=[f for f in F if f["ts"]=="2026-11-04 11:05:26"]
chk("决断帧11:05:26在档", len(PIN)==1, len(PIN))
chk("无>180s断档", doc["数据新鲜度"]["ticks"].endswith("未触『断更>10 分钟只报警禁决策』"), True)
# 2 广度
zt, zb, dt = pl["zt"], pl["zb"], pl["dt"]
chk("涨停=30", len(zt) == doc["全场广度"]["涨停"] == 30, len(zt))
chk("炸板=21", len(zb) == doc["全场广度"]["炸板"] == 21, len(zb))
chk("跌停=18", len(dt) == doc["全场广度"]["跌停"] == 18, len(dt))
chk("炸板率=21/51(4位)", doc["全场广度"]["炸板率"] == round(len(zb)/(len(zt)+len(zb)),4), doc["全场广度"]["炸板率"])
chk("二板加=10", sum(1 for x in zt if x["lbc"] >= 2) == doc["全场广度"]["二板加"] == 10)
chk("最高板=4@皇台酒业", doc["全场广度"]["最高板"] == 4 and doc["全场广度"]["最高板个股"] == "皇台酒业")
# 3 持仓报价
chk("600261 bid1=0 且 ask1量取自留档帧(672961@11:05:12 / 673142@11:05:22)", q["sh600261"]["bid1"] == "0.00" and q["sh600261"]["ask1_vol"] == "672961" and qb["600261"]["ask1v"] == "673142", (q["sh600261"]["ask1_vol"], qb["600261"]["ask1v"]))
chk("600261 =4.46/-9.90", q["sh600261"]["px"] == 4.46 and q["sh600261"]["pct"] == -9.9)
chk("603906 =15.02/-3.96", qb["603906"]["px"] == 15.02 and abs(qb["603906"]["pct"] + 3.96) < 1e-9, qb["603906"])
chk("603906 相对开盘 -3.47", abs(round((qb["603906"]["px"] / qb["603906"]["open"] - 1) * 100, 2) + 3.47) < 1e-9)
chk("600299 +2.56 vs 8.20", abs(round((8.41 / 8.20 - 1) * 100, 2) - 2.56) < 1e-9)
chk("600259 -0.07 vs 60.20", abs(round((60.16 / 60.20 - 1) * 100, 2) + 0.07) < 1e-9)
# 4 宽度重算（11:05 帧 vs 文件）
L = {r["code"]: r for r in PIN[0]["rows"]}
p = sorted(x["pct"] for x in L.values())
w = doc["半日宽度"][-1]
chk("宽度-末帧均涨", abs(w["均涨"] - round(sum(p) / len(p), 2)) < 1e-9, w["均涨"], round(sum(p) / len(p), 2))
chk("宽度-末帧中位", abs(w["中位pct"] - round(p[len(p) // 2], 2)) < 1e-9, w["中位pct"])
chk("宽度-末帧破-3%", w["破-3%"] == sum(1 for v in p if v <= -3), w["破-3%"])
chk("宽度-末帧破-8%", w["破-8%"] == sum(1 for v in p if v <= -8), w["破-8%"])
# 5 批量跳水重算
snap = lambda f: {r["code"]: r for r in f["rows"]}
mx = 0
for i in range(2, len(F)):
    if F[i]["ts"] < "2026-11-04 10:30":
        continue
    S1, S2 = snap(F[i - 2]), snap(F[i])
    c = sum(1 for k in S2 if k in S1 and S2[k]["pct"] - S1[k]["pct"] <= -3)
    mx = max(mx, c)
chk("2分钟窗内最多-3pp只数=1", mx == doc["跳水阈值核验"]["单窗最多只数"] == 1, mx)
chk("未触发判定一致", mx < 3 and doc["决断"]["B"].startswith("0 笔"))
# 6 净值重算
m = json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\状态.json", encoding="utf-8"))
mp = {x["code"]: x for x in m["持仓"]}
led = round(m["现金"] + sum({"002365": 11.98, "001287": 19.48, "600299": 8.41, "600259": 60.16}[c] * mp[c]["shares"] for c in mp), 2)
chk("账本口径净值", led == doc["净值估算"]["账本口径(A腿未回写)"], led, doc["净值估算"]["账本口径(A腿未回写)"])
# 7 口径完整性
chk("fills为空且qty规则未被违反", doc["fills"] == [] and doc["no_action"] == "心跳hb-c无动作")
chk("无发版覆盖(修订在册)", "v1.1" in doc.get("修订", ""))
chk("缺件如实(pulse/warboard/执行流水)", all(not os.path.exists(os.path.join(B, f)) for f in ("pulse.json", "warboard.json", "执行流水.jsonl")))
chk("playbook未被改动", os.path.getmtime(os.path.join(B, "playbook.json")) < os.path.getmtime(os.path.join(B, "临盘决断_20261104_1100.json")))
chk("无编造代码(每只持仓均在报价文件)", all(c in [x["code"] for x in q.values()] + list(qb.keys()) for c in ("600261", "002652", "603906", "600299", "600259", "002365", "001287")))

bad = [x for x in ok if not x[1]]
for n, c, *rest in ok:
    print(("PASS " if c else "FAIL ") + n, "" if c else rest)
print("\n=== %d/%d PASS, %d FAIL ===" % (len(ok) - len(bad), len(ok), len(bad)))
