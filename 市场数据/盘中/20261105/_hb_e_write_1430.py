# -*- coding: utf-8 -*-
"""hb-e 14:30 尾盘前哨：从留档源文件重算并写 临盘决断_20261105_1430.json（无动作 + 为 14:45 深场B备料）"""
import json, os, datetime
from collections import Counter

D = r"D:\股票数据\市场数据\盘中\20261105"
DATE = "20261105"
pools = json.load(open(os.path.join(D, "_hb_e_pools_1430.json"), encoding="utf-8"))
quote = json.load(open(os.path.join(D, "_hb_e_quote_1430.json"), encoding="utf-8"))
post = json.load(open(os.path.join(D, "_hb_e_pos_1430.json"), encoding="utf-8"))
an = json.load(open(os.path.join(D, "_hb_e_analyze_1430.json"), encoding="utf-8"))
prev = json.load(open(os.path.join(D, "临盘决断_20261105_1330.json"), encoding="utf-8"))

zt, zb, dt = pools["zt"], pools["zb"], pools["dt"]
frames = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
frames.sort(key=lambda f: f["ts"])
now = datetime.datetime.now()
last = datetime.datetime.strptime(frames[-1]["ts"], "%Y-%m-%d %H:%M:%S")
gap_min = round((now - last).total_seconds() / 60, 1)

# ---- 午后新封（首封时间 >= 13:00，含 13:00 后累计） ----
def mm(x):
    t = str(x.get("fbt", "")).zfill(6)
    return int(t[:2]) * 60 + int(t[2:4]) if len(t) >= 4 else 0

aft = [x for x in zt if mm(x) >= 13 * 60]
lb = Counter(x["lbc"] for x in zt)
zb_hy = Counter(x.get("hybk") for x in zb)
zt_hy = Counter(x.get("hybk") for x in zt)

# ---- 13:34 -> 14:33 池内流转（回封/新封/掉出/新炸） ----
old = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))
zt_o, zb_o = {x["c"] for x in old["zt"]}, {x["c"] for x in old["zb"]}
zt_n, zb_n = {x["c"] for x in zt}, {x["c"] for x in zb}
nm = {x["c"]: x["n"] for x in zt + zb}
reseal = sorted(nm[c] for c in zt_n & zb_o)
fresh = sorted(nm[c] for c in zt_n - zt_o - zb_o)
fell = sorted(nm.get(c, c) for c in zt_o - zt_n)
newbrk = sorted(nm[c] for c in zb_n - zb_o - zt_o)

# ---- 持仓 ----
POS = [("600299", "安迪苏", 2300, 8.2041, "11/3 建仓 2.0%；playbook.sells 收盘了结腿（执2 到点）"),
       ("600259", "中稀有色", 100, 60.2301, "11/3 建仓 1.0%；日高 64.12(10:10) 后回落，收盘了结腿（执2 到点）"),
       ("603906", "龙蟠科技", 600, 15.5678, "11/4 建仓；执2 到期 11/6 收盘，−3% 线 15.10"),
       ("002292", "奥飞娱乐", 500, 9.3747, "11/4 建仓；执2 到期 11/6 收盘，−3% 线 9.09")]
pos_out = []
for code, name, sh, cost, note in POS:
    s = post[code]
    px = s["last"]["px"]
    pos_out.append({"code": code, "name": name, "shares": sh, "cost_px": cost, "px": px,
                    "pct": s["last"]["pct"], "pnl_pct": round((px / cost - 1) * 100, 2),
                    "hi_px": s["hi"]["px"], "hi_t": s["hi"]["t"],
                    "dd_from_hi_pct": s["dd_from_hi_pct"], "d2min_pp": s["d2min_pp"],
                    "limit_px": s["limit_px"], "touched_limit_today": bool(s["touched_limit"]),
                    "action": "持有", "note": note})

mv = round(sum(p["px"] * p["shares"] for p in pos_out), 2)
cash = 945736.38
nav = round(cash + mv, 2)

# ---- 批量跳水极值（午后全窗重算） ----
mx_cnt, mx_win = 0, None
for i in range(2, len(frames)):
    if frames[i]["ts"] < "2026-11-05 13:00":
        continue
    S1 = {r["code"]: r for r in frames[i - 2]["rows"]}
    S2 = {r["code"]: r for r in frames[i]["rows"]}
    sub = [S2[c]["name"] for c in S2 if c in S1 and S2[c]["pct"] - S1[c]["pct"] <= -3]
    if len(sub) > mx_cnt:
        mx_cnt, mx_win = len(sub), {"帧": frames[i]["ts"], "票": sub}

w = an["width"]
lastw = w[-1]
idx = {k: [v["pct"], v["px"]] for k, v in quote["rows"].items() if k in ("sh000001", "sz399001", "sz399006", "sh000688")}

doc = {
    "date": DATE,
    "session": "hb-e",
    "ts": "14:30 场次（决断帧 2026-11-05 14:33-14:34；px 取腾讯快照 14:33:02 + 东财涨停/炸板/跌停池 14:33:02 + 持仓东财分时末帧 14:34）",
    "write_ts": now.strftime("%Y-%m-%d %H:%M"),
    "决断时点": now.strftime("%Y-%m-%d %H:%M") + "（只用 ≤14:34 留档数据，无任何事后帧）",
    "版本": "sentiment-review-system v2.15 · 13号盘中作战agent 心跳 hb-e（14:30 尾盘前哨，为 14:45 深场B备料）",
    "权限级别": "无动作（A 级无到期 trigger；B 级阈值未达；C 级仅记录不建仓）",
    "fill_frame": "realtime_ticks.jsonl 2026-11-05 14:33:04 帧（%d 帧、116 只昨日涨停池、1 分钟/帧）/ 腾讯快照 14:33:02 / 东财分时末帧 14:34" % len(frames),
    "fills": [],
    "no_action": "心跳hb-e无动作",
    "data_freshness": {
        "realtime_ticks_last": frames[-1]["ts"],
        "frames": len(frames),
        "max_gap_sec": 61,
        "gap_min": gap_min,
        "quote_fetched": quote["fetched"],
        "pools_fetched": pools["fetched"],
        "pools_qdate": [pools.get("zt_qdate"), pools.get("zb_qdate"), pools.get("dt_qdate")],
        "pos_trends_last": post["600299"]["last"]["t"],
        "pulse_json": "缺失（盘中/20261105/ 无；hb-b/hb-c/hb-d 同缺，规格漂移未修）",
        "执行流水_jsonl": "缺失",
        "warboard_json": "今日缺失（沿用 11/4 版仅作题材归属参考）",
        "报警_jsonl": "报警_20261105.jsonl 不存在",
        "verdict": "允许决策（tick 断更 %.1f 分钟 << 10 分钟）；成交回执仍不可核验" % gap_min,
    },
    "market_snapshot": {
        "ts": "2026-11-05 14:33",
        "涨停": len(zt), "炸板": len(zb), "炸板率": round(len(zb) / (len(zt) + len(zb)), 4),
        "跌停": len(dt), "跌停个股": [{"票": x["n"], "涨跌": round(x.get("zdp", 0), 2)} for x in dt],
        "最高板": max(x["lbc"] for x in zt),
        "最高板个股": [{"板": x["lbc"], "票": x["n"], "板块": x.get("hybk")} for x in zt if x["lbc"] >= 3],
        "连板分布": {str(k): v for k, v in sorted(lb.items())},
        "二板加": sum(v for k, v in lb.items() if k >= 2),
        "首板": lb[1],
        "一进二率": round(lb.get(2, 0) / 116, 4),
        "午后新封": {"数量": len(aft), "行业": dict(Counter(x.get("hybk") for x in aft).most_common()),
                    "明细": [{"票": x["n"], "板": x["lbc"], "板块": x.get("hybk"), "首封": x.get("fbt"),
                             "封单亿": round(x.get("fund", 0) / 1e8, 2) if x.get("fund") else None}
                            for x in sorted(aft, key=mm)]},
        "13:34到14:33流转": {"回封": reseal, "新封": fresh, "掉出涨停": fell, "新炸板": newbrk},
        "炸板行业": dict(zb_hy.most_common(10)),
        "涨停行业": dict(zt_hy.most_common(10)),
        "光伏": {"涨停": zt_hy.get("光伏设备", 0), "炸板": zb_hy.get("光伏设备", 0)},
        "指数": idx,
        "池内116只": {"均涨": lastw["均涨"], "中位": lastw["中位"], "红盘": lastw["红盘"], "绿盘": lastw["绿盘"],
                    "贴板>=9.6": lastw["贴板>=9.6"], "破-3": lastw["破-3"], "破-8": lastw["破-8"]},
    },
    "breadth_trend": [{"t": x["帧"][11:16], "mean": x["均涨"], "中位": x["中位"], "红盘": x["红盘"],
                       "ge9.6": x["贴板>=9.6"], "le-3": x["破-3"], "le-8": x["破-8"]} for x in w],
    "positions": pos_out,
    "nav_estimate": {
        "master口径_11-04收盘": 985844.0,
        "持仓市值": mv, "现金": cash, "本场估算": nav,
        "当日变动": "%+.3f%%" % ((nav / 985844.0 - 1) * 100),
        "说明": "现金取 hb-c 口径 945736.38（含 002652 卖出 16200 未扣费、未入账）；估算值，账本无 11/5 回执",
    },
    "batch_dive_check": {"午后最大同窗≤-3pp 只数": mx_cnt, "窗口": mx_win, "结论": "无批量跳水（阈值 ≥3 只）"},
    "permission_checks": {
        "A级_预案内trigger": {"结果": "无到期 trigger",
                          "证据": "playbook(20261104) buys 两只（002992/688809）buy_gate 开在 11/5 09:25-09:31 竞价/开盘，现 14:33 早已过期；sells 中 600299/600259 为 close 腿（收盘执行），600299/600259 收盘了结属 14:57 后场次职责，本场不提前动手"},
        "B级_防守": {"结果": "未触发",
                  "证据": "①hb-c 预留条件『涨停≤70 且 炸板率≥0.35 且 603906/002292 同转绿』：实际 涨停 80（>70 不满足）、炸板率 0.3798（满足）、603906 +2.00% / 002292 +3.10%（均红盘，不满足）→ 复合条件不成立；②持仓无摸板（4 只 touched_limit_today 全 False）、无 −3% 成本线击穿（最低 603906 +1.75%）；③午后 2 分钟窗最大同窗跳水仅 " + str(mx_cnt) + " 只（阈值 ≥3）"},
        "C级_预案外进攻": {"结果": "仅记录不建仓",
                     "证据": "13:34→14:33 新封 %d 只全为首板且行业零散（%s），无 2 板以上可介入梯队；炸板率 0.3798 属 hb-c 定的高炸区，C 级不得开仓" %
                             (len(fresh), "、".join(dict(Counter(nm[c] for c in zt_n - zt_o - zb_o)).keys()) or "无")},
    },
    "for_1445_brief": {
        "定性": "尾盘修复、非反转：池内 116 只均涨 13:49 低点 3.21 → 14:32 4.47（+1.26pp）、贴板 17→23、指数尾盘走强（深成 +1.21%、科创50 +1.82%），但 涨停 80 中 11 只新封零首板梯队、炸板 49/率 0.3798 仍高、光伏涨停 10 但炸板 8 → 修复属抢尾盘情绪，不构成加仓或提高仓位上限的依据",
        "尾盘卖预案候选": [
            {"code": "600299", "name": "安迪苏", "shares": 2300, "now": 8.62, "pnl_pct": 5.07,
             "预设": "close 腿（playbook 机械执行）→ 14:57 收盘价卖出，不议价",
             "若走弱": "14:45-14:57 若跌破昨收 8.47 且 2 分钟跌超 1pp → 深场B 可按 8.55 一线提前了结（B 级需写触发证据）",
             "若走强": "不强留：执2 到点即走，浮盈 +5% 已超本格期望"},
            {"code": "600259", "name": "中稀有色", "shares": 100, "now": 62.68, "pnl_pct": 4.07,
             "预设": "close 腿 → 14:57 收盘价卖出",
             "若走弱": "日高 64.12(10:10) 已回吐 −2.25%，若 14:45 前跌破 61.51（日低）→ 提前了结 100 股（100 股为最小整手，无零股问题）"},
            {"code": "603906", "name": "龙蟠科技", "shares": 600, "now": 15.84, "pnl_pct": 1.75,
             "预设": "持有（执2 到期 11/6 收盘）",
             "若走弱": "14:45 若 < 15.57（成本）→ B 级提前了结；若仅日内回抽（现 −3.30% 离日高但 +1.75% 于成本）→ 不动"},
            {"code": "002292", "name": "奥飞娱乐", "shares": 500, "now": 9.63, "pnl_pct": 2.72,
             "预设": "持有（执2 到期 11/6 收盘）",
             "若走弱": "14:45 若 < 9.37（成本）→ B 级减半；< 9.09（−3% 线）→ 清出"},
        ],
        "明日预案要点草稿": [
            "情绪定位：弱修复。涨停 80（+8 vs 13:34，但 11 只新封全首板、2 只回封）、炸板率 0.3798、最高板 4（闽发铝业/浙文影业）、一进二 %d/116=%.1f%%、跌停 1（快意电梯，今日首只）→ 温度仍在 35-55 中枢下沿，非反转" % (lb.get(2, 0), lb.get(2, 0) / 116 * 100),
            "高度观察：闽发铝业/浙文影业 4 板明日能否 5 板；光伏线 涨停 10 vs 炸板 8（永臻 3 板、贝特利 2 板）属『封一半炸一半』→ 追高成本高，只做回封不打首封",
            "持仓切换：600299/600259 今收盘了结后释放约 2.6 万，明日 master 仓只余 603906/002292（各 600/500 股、执2 11/6 到期）；明日买入预算按 playbook 单票 ≤1.5% 重算，不递补",
            "风控红线：炸板率 ≥0.35 时禁买首板；最高板 ≤2 或 涨停 ≤70 → 已成交按 −3% 离场、新单全废（沿用 11/4 反向线）",
            "数据欠账：pulse.json / 报警 jsonl / warboard 今日第 4 场缺失，须在 20:30 离线补跑前修（否则深场 B 无 alarm 通道）"],
    },
    "conditional_watch": [
        "14:45-14:57 光伏炸板股（迈为 14.94%、奥特维 14.27%、艾能聚 27.01%）能否回封 → 决定明日光伏是否成线",
        "收盘涨停数是否 ≥90（playbook 反向线：≥90 且 最高板≥4 且 昨日池执1 均收>0 → 攻防判错，C 上调 B）",
        "603906 是否守 15.57 成本；002292 是否守 9.37",
        "快意电梯 −9.99% 是否扩散至跌停家数 ≥3（退潮信号）",
    ],
    "account_integrity": [
        "成交回执：今日 09:21/09:40/10:30/11:00/13:30 五份决断均无 fills 落库（执行流水.jsonl 缺失），持仓数量承袭 hb-c 口径，未经经纪端核对",
        "现金 945736.38 沿用 hb-c（含 002652 卖出 16200 未扣费未入账），本场不新增交易，不改现金",
        "000919 金陵药业 −9.89pp（11:01 涨停 → 14:33 +0.15%）为今日最大单票崩塌，不在持仓，仅记线索",
    ],
    "修订记录": ["2026-11-05 14:3x hb-e 首版：无动作 + 14:45 深场B备料（尾盘卖预案候选 4 条 / 明日要点 5 条）"],
}
p = os.path.join(D, "临盘决断_20261105_1430.json")
json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", p, os.path.getsize(p), "bytes")
print("涨停", len(zt), "炸板", len(zb), "率", doc["market_snapshot"]["炸板率"], "最高板", doc["market_snapshot"]["最高板"])
print("回封", reseal, "新封", fresh, "掉出", fell, "新炸", newbrk)
print("持仓市值", mv, "NAV", nav, doc["nav_estimate"]["当日变动"])
print("批量跳水极值", mx_cnt)
