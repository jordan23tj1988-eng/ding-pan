# -*- coding: utf-8 -*-
"""hb-e 自审：决断文件 vs 源文件交叉核对"""
import json, os

D = r"D:\股票数据\市场数据\盘中\20261105"
doc = json.load(open(os.path.join(D, "临盘决断_20261105_1430.json"), encoding="utf-8"))
pools = json.load(open(os.path.join(D, "_hb_e_pools_1430.json"), encoding="utf-8"))
post = json.load(open(os.path.join(D, "_hb_e_pos_1430.json"), encoding="utf-8"))
an = json.load(open(os.path.join(D, "_hb_e_analyze_1430.json"), encoding="utf-8"))
prev = json.load(open(os.path.join(D, "临盘决断_20261105_1330.json"), encoding="utf-8"))
ok = True


def chk(n, c, d=""):
    global ok
    print(("PASS " if c else "FAIL ") + n + (" | " + d if d else ""))
    ok = ok and bool(c)


ms = doc["market_snapshot"]
chk("涨停=源", ms["涨停"] == len(pools["zt"]), f"{ms['涨停']} vs {len(pools['zt'])}")
chk("炸板=源", ms["炸板"] == len(pools["zb"]), f"{ms['炸板']} vs {len(pools['zb'])}")
chk("炸板率算术", abs(ms["炸板率"] - len(pools["zb"]) / (len(pools["zt"]) + len(pools["zb"]))) < 1e-4, str(ms["炸板率"]))
chk("跌停=源", ms["跌停"] == len(pools["dt"]), f"{ms['跌停']} vs {len(pools['dt'])}")
chk("最高板=源", ms["最高板"] == max(x["lbc"] for x in pools["zt"]))
chk("连板分布合计=涨停", sum(ms["连板分布"].values()) == ms["涨停"], str(ms["连板分布"]))
chk("一进二率算术", abs(ms["一进二率"] - ms["连板分布"].get("2", 0) / 116) < 1e-4, str(ms["一进二率"]))
chk("午后新封=源(首封>=13:00)", ms["午后新封"]["数量"] == len([x for x in pools["zt"] if str(x.get("fbt", "")).zfill(6) >= "130000"]),
    f"{ms['午后新封']['数量']}")
chk("fills 为空", doc["fills"] == [])
chk("no_action 文案", doc["no_action"] == "心跳hb-e无动作")
chk("session", doc["session"] == "hb-e")
chk("pools qdate 全=20261105", all(str(pools.get(k)) == "20261105" for k in ("zt_qdate", "zb_qdate", "dt_qdate")))
chk("断更 <10 分钟", doc["data_freshness"]["gap_min"] < 10, str(doc["data_freshness"]["gap_min"]))

for p in doc["positions"]:
    s = post[p["code"]]
    chk(f"{p['code']} px=分时源", abs(p["px"] - s["last"]["px"]) < 1e-9, f"{p['px']} vs {s['last']['px']}")
    chk(f"{p['code']} pnl 算术", abs(p["pnl_pct"] - (p["px"] / p["cost_px"] - 1) * 100) < 0.011, str(p["pnl_pct"]))
    chk(f"{p['code']} 未摸板判据", p["touched_limit_today"] == bool(s["touched_limit"]))
    chk(f"{p['code']} 股数承袭 hb-d", p["shares"] == [x for x in prev["positions"] if x["code"] == p["code"]][0]["shares"])

mv = sum(p["px"] * p["shares"] for p in doc["positions"])
nav = doc["nav_estimate"]
chk("持仓市值算术", abs(nav["持仓市值"] - mv) < 0.51, f"{nav['持仓市值']} vs {round(mv,2)}")
chk("NAV 算术", abs(nav["本场估算"] - (nav["现金"] + mv)) < 0.51)
chk("现金承袭", "945736.38" in json.dumps(prev["nav_estimate"], ensure_ascii=False))
chk("无事后帧(breadth 末条<=14:32)", max(x["t"] for x in doc["breadth_trend"]) <= "14:32")
chk("breadth 末条 mean=源", abs(doc["breadth_trend"][-1]["mean"] - an["width"][-1]["均涨"]) < 1e-9)
chk("批量跳水结论=重算", doc["batch_dive_check"]["午后最大同窗≤-3pp 只数"] < 3, str(doc["batch_dive_check"]["午后最大同窗≤-3pp 只数"]))
chk("备料档存在", len(doc["for_1445_brief"]["尾盘卖预案候选"]) == 4 and len(doc["for_1445_brief"]["明日预案要点草稿"]) == 5)
chk("四只持仓全覆盖", {p["code"] for p in doc["positions"]} == set(post.keys()))
print("\n=== hb-e 自审总判定:", "PASS" if ok else "FAIL", "===")
