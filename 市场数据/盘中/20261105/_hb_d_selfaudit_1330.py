# -*- coding: utf-8 -*-
"""hb-d 自审：决断文件 vs 源文件交叉核对（口径/算术/零编造）"""
import json, os

D = r"D:\股票数据\市场数据\盘中\20261105"
doc = json.load(open(os.path.join(D, "临盘决断_20261105_1330.json"), encoding="utf-8"))
pools = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))
quote = json.load(open(os.path.join(D, "_hb_d_quote_1330.json"), encoding="utf-8"))
post = json.load(open(os.path.join(D, "_hb_d_pos_1330.json"), encoding="utf-8"))
prev = json.load(open(os.path.join(D, "临盘决断_20261105_1100.json"), encoding="utf-8"))
ok = True


def chk(name, cond, detail=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + (" | " + detail if detail else ""))
    ok = ok and bool(cond)


ms = doc["market_snapshot"]
chk("涨停数=源", ms["涨停"] == len(pools["zt"]), f"{ms['涨停']} vs {len(pools['zt'])}")
chk("炸板数=源", ms["炸板"] == len(pools["zb"]), f"{ms['炸板']} vs {len(pools['zb'])}")
chk("炸板率算术", abs(ms["炸板率"] - len(pools["zb"]) / (len(pools["zt"]) + len(pools["zb"]))) < 1e-4, str(ms["炸板率"]))
chk("跌停=源", ms["跌停"] == len(pools["dt"]), f"{ms['跌停']} vs {len(pools['dt'])}")
chk("最高板=源", ms["最高板"] == max(x["lbc"] for x in pools["zt"]))
chk("连板分布合计=涨停", sum(int(v) for v in ms["连板分布"].values()) == ms["涨停"], str(ms["连板分布"]))
chk("午后新封计数", ms["午后新封"]["数量"] == len([x for x in pools["zt"] if str(x.get("fbt", "")).zfill(6) >= "130000"]))
chk("fills 为空", doc["fills"] == [])
chk("no_action 文案", doc["no_action"] == "心跳hb-d无动作")
chk("session", doc["session"] == "hb-d")
chk("日期与源一致", quote["fetched"].startswith("2026-11-05") and str(pools["zt_qdate"]) == "20261105"
    and str(pools["zb_qdate"]) == "20261105" and str(pools["dt_qdate"]) == "20261105",
    f"{pools['fetched']} qdate={pools['zt_qdate']}")

# 持仓交叉：决断 px vs 分时源末帧；与腾讯快照差 ≤1.2%（3 分钟内波动）
for p in doc["positions"]:
    src = post[p["code"]]
    chk(f"{p['code']} px=分时源", abs(p["px"] - src["last"]["px"]) < 1e-6, f"{p['px']} vs {src['last']['px']}")
    sh_k = "sh" + p["code"] if p["code"].startswith("6") else "sz" + p["code"]
    chk(f"{p['code']} pnl 算术", abs(p["pnl_pct"] - (p["px"] / p["cost_px"] - 1) * 100) < 0.011,
        f"{p['pnl_pct']} vs {round((p['px']/p['cost_px']-1)*100,2)}")
    chk(f"{p['code']} 未摸板判据", p["touched_limit_today"] == (src["hi"]["px"] >= src["limit_px"] - 0.005))
    chk(f"{p['code']} 股数承袭 hb-c",
        p["shares"] == [x for x in prev["positions"] if x["code"] == p["code"]][0]["shares"])

mv = sum(p["px"] * p["shares"] for p in doc["positions"])
nav = doc["nav_estimate"]
chk("持仓市值算术", abs(nav["持仓市值"] - mv) < 0.51, f"{nav['持仓市值']} vs {round(mv,2)}")
chk("NAV 算术", abs(nav["本场估算"] - (nav["现金"] + mv)) < 0.51, f"{nav['本场估算']} vs {round(nav['现金']+mv,2)}")
chk("现金承袭 hb-c", "945736.38" in json.dumps(prev["nav_estimate"], ensure_ascii=False))

# 破-8 名单与 2 分钟批量跳水结论（用全量 ticks 重算，不用被截断的 win[-15:]）
an = json.load(open(os.path.join(D, "_hb_d_analyze_1330.json"), encoding="utf-8"))
frames = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
frames.sort(key=lambda f: f["ts"])
mx = 0
for i in range(2, len(frames)):
    if frames[i]["ts"] < "2026-11-05 13:00":
        continue
    S1 = {r["code"]: r for r in frames[i - 2]["rows"]}
    S2 = {r["code"]: r for r in frames[i]["rows"]}
    cnt = sum(1 for c in S2 if c in S1 and S2[c]["pct"] - S1[c]["pct"] <= -3)
    mx = max(mx, cnt)
chk("午后无≥3只批量跳水", mx < 3, f"全场午后窗口最大={mx} 只")
chk("breadth 条数≥8", len(doc["breadth_trend"]) >= 8, str(len(doc["breadth_trend"])))
lastw = doc["breadth_trend"][-1]
chk("breadth 末条=源", abs(lastw["mean"] - an["width"][-1]["均涨"]) < 1e-9, str(lastw))
chk("无事后帧", max(x["t"] for x in doc["breadth_trend"]) <= "13:33")
print("\n=== 自审总判定:", "PASS" if ok else "FAIL", "===")
print("reason 字数", len(doc["reason"]))
