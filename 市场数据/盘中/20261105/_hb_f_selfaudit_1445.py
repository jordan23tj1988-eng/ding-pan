# -*- coding: utf-8 -*-
"""hb-f 自审：临盘决断_1445 / 复盘md  vs 源文件交叉核对（哨兵）"""
import json, os, re, datetime

D = r"D:\股票数据\市场数据\盘中\20261105"
LX = r"D:\股票数据\市场数据\_学习"
doc = json.load(open(os.path.join(D, "临盘决断_20261105_1445.json"), encoding="utf-8"))
pools = json.load(open(os.path.join(D, "_hb_f_pools_1445.json"), encoding="utf-8"))
qd = json.load(open(os.path.join(D, "_hb_f_quote_1445.json"), encoding="utf-8"))
qe = json.load(open(os.path.join(D, "_hb_f_quote_pxexec.json"), encoding="utf-8"))
q652 = json.load(open(os.path.join(D, "_hb_f_quote_002652.json"), encoding="utf-8"))
mp = json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\state.json", encoding="utf-8"))
pb = json.load(open(os.path.join(D, "playbook.json"), encoding="utf-8"))
md = open(os.path.join(LX, "盘中尾盘复盘_20261105.md"), encoding="utf-8").read()
ok = True


def chk(n, c, d=""):
    global ok
    print(("PASS " if c else "FAIL ") + n + (" | " + d if d else ""))
    ok = ok and bool(c)


ms = doc["市场快照"]
zt, zb, dt = pools["zt"], pools["zb"], pools["dt"]
chk("涨停=源", ms["涨停"] == len(zt), f"{ms['涨停']} vs {len(zt)}")
chk("炸板=源", ms["炸板"] == len(zb), f"{ms['炸板']} vs {len(zb)}")
chk("跌停=源", ms["跌停"] == len(dt), f"{ms['跌停']} vs {len(dt)}")
chk("炸板率算术", abs(ms["炸板率"] - len(zb) / (len(zt) + len(zb))) < 1e-4, str(ms["炸板率"]))
chk("连板分布合计=涨停", sum(ms["连板分布"].values()) == ms["涨停"], str(ms["连板分布"]))
chk("最高板=源", ms["最高板"] == max(x["lbc"] for x in zt))
chk("最高板个股与源一致", all(n.split("(")[0] in [x["n"] for x in zt if x["lbc"] == ms["最高板"]] for n in ms["最高板个股"]))
chk("二板加=源", ms["二板加"] == sum(1 for x in zt if x["lbc"] >= 2), str(ms["二板加"]))
chk("一进二率算术", abs(ms["一进二率"] - ms["连板分布"].get("2", 0) / 116) < 1e-4, str(ms["一进二率"]))
chk("首封时点合计=涨停", sum(ms["首封时点"].values()) == ms["涨停"], str(ms["首封时点"]))
for k, key in (("上证", "sh000001"), ("深成", "sz399001"), ("创业板", "sz399006"), ("科创50", "sh000688")):
    chk(f"指数 {k}=源", abs(ms["指数"][k][0] - qe["rows"][key]["px"]) < 1e-9 and abs(ms["指数"][k][1] - qe["rows"][key]["pct"]) < 1e-9)
chk("pools qdate 全=20261105", all(str(pools.get(k)) == "20261105" for k in ("zt_qdate", "zb_qdate", "dt_qdate")))

# fills 可复现
chk("session hb-f", doc["session"] == "hb-f")
chk("fills=2", len(doc["fills"]) == 2, str(len(doc["fills"])))
mpos = {p["code"]: p for p in mp["positions"]}
for f in doc["fills"]:
    k = ("sh" if f["code"][0] == "6" else "sz") + f["code"]
    exp = round(qe["rows"][k]["px"] * 0.999, 2)
    chk(f"{f['code']} px_exec 可复现", abs(f["px_exec"] - exp) < 1e-9, f"{f['px_exec']} vs {exp}")
    chk(f"{f['code']} px=执行帧", abs(f["px"] - qe["rows"][k]["px"]) < 1e-9)
    chk(f"{f['code']} qty=账本持仓", f["qty"] == mpos[f["code"]]["shares"], f"{f['qty']} vs {mpos[f['code']]['shares']}")
    chk(f"{f['code']} 买一承接足量", float(qe["rows"][k]["bid1_vol"]) * 100 >= f["qty"])
    chk(f"{f['code']} 在 playbook close 腿内", any(s["代码"] == f["code"] and s["腿"] == "close" for s in pb["sells"]))
chk("卖出均为 A 级预案内", all(f["route"].startswith("A-") for f in doc["fills"]))

# 持仓表态
pos = {p["code"]: p for p in doc["持仓快照"]["逐票"]}
chk("持仓覆盖=账本在持(剔除已卖002652)=4", set(pos) == {"600299", "600259", "603906", "002292"}, str(set(pos)))
for c, p in pos.items():
    chk(f"{c} px=执行帧", abs(p["px"] - qe["rows"][("sh" if c[0] == "6" else "sz") + c]["px"]) < 1e-9)
    chk(f"{c} pnl算术", abs(p["pnl_pct_vs_buy"] - (p["px"] / p["buy_px"] - 1) * 100) < 0.011, str(p["pnl_pct_vs_buy"]))
    chk(f"{c} shares=账本", p["shares"] == mpos[c]["shares"])
chk("600299/600259 标卖出", pos["600299"]["action"].startswith("卖出") and pos["600259"]["action"].startswith("卖出"))
chk("603906/002292 标持有", pos["603906"]["action"].startswith("持有") and pos["002292"]["action"].startswith("持有"))

# 002652 结算
chk("002652 现价=源", str(q652["px"]) in json.dumps(doc["执行对账"], ensure_ascii=False))

# 账本断链断言（600261）
chk("600261 确不在账本 positions", "600261" not in mpos)
chk("600261 确不在账本 closed", "600261" not in [c.get("code") for c in mp["closed"]])
nav = 8.47 * 2300 + 63.15 * 100 + 4.59 * 3600 + 15.53 * 600 + 9.34 * 500
chk("11-04 mv 复算=净值.json", abs(nav - json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\净值.json", encoding="utf-8"))["20261104"]["mv"]) < 0.01, str(nav))

# 新鲜度
last_tick = None
with open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") as f:
    for ln in f:
        if ln.strip():
            last_tick = json.loads(ln)["ts"]
age_min = (datetime.datetime.strptime(doc["write_ts"], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(last_tick, "%Y-%m-%d %H:%M:%S")).total_seconds() / 60
chk("断更 <10 分钟", age_min < 10, f"末帧 {last_tick}, 龄 {age_min:.1f} 分")
chk("决断时戳单调(14:45<=write_ts)", doc["write_ts"] >= "2026-11-05 14:45")

# 发出版不可覆盖
prev = sorted(x for x in os.listdir(D) if re.match(r"临盘决断_20261105_\d{4}\.json$", x))
chk("今日决断文件共 7 份(6 前序+本场)", len(prev) == 7, str(prev))
mine_mtime = os.path.getmtime(os.path.join(D, "临盘决断_20261105_1445.json"))
chk("前序 6 份 mtime 均早于本场写入",
    all(os.path.getmtime(os.path.join(D, x)) < mine_mtime for x in prev if x != "临盘决断_20261105_1445.json"))
chk("1430 场文件 mtime 仍为 14:35", datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(D, "临盘决断_20261105_1430.json"))).strftime("%H:%M") == "14:35")

# md 与 JSON 一致性
for s in ("81 / 50 / 0", "38.17%", "8.63", "62.53", "4.35", "600261"):
    chk(f"md 含 {s}", s in md)
chk("md 有7节", all(h in md for h in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7.")))
chk("md 无占位残字", not any(x in md for x in ("TODO", "待填", "XX", "undefined", "None")))
chk("md 无编造成交(600261 未称已卖)", "600261" in md and "卖在当日最低点" in md)

print("\n=== hb-f 自审总判定:", "PASS" if ok else "FAIL", "===")
