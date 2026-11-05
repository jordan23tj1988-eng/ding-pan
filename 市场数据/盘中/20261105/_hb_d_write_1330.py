# -*- coding: utf-8 -*-
"""hb-d 13:30 临盘决断写入：无动作场次（数字全部取自已留档文件）"""
import json, os, datetime

D = r"D:\股票数据\市场数据\盘中\20261105"
q = json.load(open(os.path.join(D, "_hb_d_quote_1330.json"), encoding="utf-8"))
pools = json.load(open(os.path.join(D, "_hb_d_pools_1330.json"), encoding="utf-8"))
pos = json.load(open(os.path.join(D, "_hb_d_pos_1330.json"), encoding="utf-8"))
an = json.load(open(os.path.join(D, "_hb_d_analyze_1330.json"), encoding="utf-8"))
prev = json.load(open(os.path.join(D, "临盘决断_20261105_1100.json"), encoding="utf-8"))

rows = q["rows"]
idx = {k: rows[k] for k in ("sh000001", "sz399001", "sz399006", "sh000688")}
zt, zb, dt = pools["zt"], pools["zb"], pools["dt"]
ztn, zbn = len(zt), len(zb)
rate = round(zbn / (ztn + zbn), 4)

POS = [("600299", "安迪苏", 2300), ("600259", "中稀有色", 100), ("603906", "龙蟠科技", 600), ("002292", "奥飞娱乐", 500)]
positions = []
mv = 0.0
for code, name, sh in POS:
    p = pos[code]
    px = p["last"]["px"]
    mv += px * sh
    positions.append({"code": code, "name": name, "shares": sh, "cost_px": p["cost"],
                      "px": px, "pct": p["last"]["pct"], "pnl_pct": p["pnl_pct"],
                      "hi_px": p["hi"]["px"], "hi_t": p["hi"]["t"],
                      "dd_from_hi_pct": p["dd_from_hi_pct"], "d2min_pp": p["d2min_pp"],
                      "limit_px": p["limit_px"], "touched_limit_today": p["touched_limit"],
                      "action": "持有",
                      "note": prev["positions"][[x["code"] for x in prev["positions"]].index(code)]["note"]})
CASH = 945736.38
nav = round(CASH + mv, 2)
base = 985844.0

w = {x["帧"][11:16]: x for x in an["width"]}
new_afternoon = [x for x in zt if str(x.get("fbt", "")).zfill(6) >= "130000"]
from collections import Counter
na_hy = Counter(x.get("hybk") for x in new_afternoon)
zb_hy = Counter(x.get("hybk") for x in zb)
lbc = Counter(x["lbc"] for x in zt)

doc = {
    "date": "20261105",
    "session": "hb-d",
    "ts": "13:30 场次（决断帧 2026-11-05 13:34-13:36；px 取腾讯快照 13:34:22 + 东财涨停/炸板/跌停池 13:34:22 + 持仓东财分时末帧 13:36 + realtime_ticks 末帧 13:35:52）",
    "write_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "决断时点": "2026-11-05 13:37（只用 ≤13:36 留档数据，无任何事后帧）",
    "版本": "sentiment-review-system v2.15 · 13号盘中作战agent 心跳 hb-d（13:30 午后延续段）",
    "权限级别": "无动作（A 级无到期 trigger；B 级阈值未达；C 级仅记录不建仓）",
    "fill_frame": "realtime_ticks.jsonl 2026-11-05 13:35:52 帧（243 帧、116 只昨日涨停池、1 分钟/帧、最大间隔 61 秒、断更 0 次）/ 腾讯快照 13:34:22 / 东财 push2ex 涨停·炸板·跌停池 13:34:22 qdate=20261105 / 持仓东财分时 13:36",
    "fills": [],
    "no_action": "心跳hb-d无动作",
    "reason": "",
    "data_freshness": {
        "realtime_ticks_last": "2026-11-05 13:35:52",
        "frames": 243,
        "max_gap_sec": 61,
        "gap_min": 0.7,
        "quote_fetched": q["fetched"],
        "pools_fetched": pools["fetched"],
        "pools_qdate": [pools.get("zt_qdate"), pools.get("zb_qdate"), pools.get("dt_qdate")],
        "pos_trends_last": pos["600299"]["last"]["t"],
        "pulse_json": "缺失（盘中/20261105/ 无；与 hb-b/hb-c 记录一致，规格漂移）",
        "执行流水_jsonl": "缺失",
        "warboard_json": "今日缺失（沿用 11/4 版仅作题材归属参考）",
        "报警_jsonl": "报警_20261105.jsonl 不存在",
        "verdict": "允许决策（tick 断更 0.7 分钟 << 10 分钟）；成交回执仍不可核验"
    },
    "market_snapshot": {
        "ts": "2026-11-05 13:34",
        "涨停": ztn, "炸板": zbn, "炸板率": rate, "跌停": len(dt),
        "最高板": max(x["lbc"] for x in zt),
        "最高板个股": [{"板": x["lbc"], "票": x["n"], "板块": x.get("hybk")} for x in zt if x["lbc"] >= 3],
        "连板分布": {str(k): v for k, v in sorted(lbc.items())},
        "二板加": sum(1 for x in zt if x["lbc"] >= 2),
        "首板": sum(1 for x in zt if x["lbc"] == 1),
        "午后新封": {"数量": len(new_afternoon), "行业": dict(na_hy.most_common()),
                    "明细": [{"票": x["n"], "板": x["lbc"], "板块": x.get("hybk"), "首封": x.get("fbt"),
                             "封单亿": round(x.get("fund", 0) / 1e8, 2)} for x in new_afternoon]},
        "炸板行业": dict(zb_hy.most_common(8)),
        "光伏涨停数": sum(1 for x in zt if x.get("hybk") == "光伏设备"),
        "指数": {k: [v["pct"], v["px"]] for k, v in idx.items()},
        "池内116只": {"均涨": w["13:33"]["均涨"] if "13:33" in w else an["width"][-1]["均涨"],
                     "红盘": an["width"][-1]["红盘"], "绿盘": an["width"][-1]["绿盘"],
                     "贴板>=9.6": an["width"][-1]["贴板>=9.6"], "破-3": an["width"][-1]["破-3"],
                     "破-8": an["width"][-1]["破-8"]}
    },
    "breadth_trend": [{"t": x["帧"][11:16], "mean": x["均涨"], "中位": x["中位"], "红盘": x["红盘"],
                       "ge9.6": x["贴板>=9.6"], "le-3": x["破-3"], "le-8": x["破-8"]} for x in an["width"]],
    "positions": positions,
    "nav_estimate": {"master口径_11-04收盘": base, "持仓市值": round(mv, 2), "现金": CASH,
                     "本场估算": nav, "当日变动": "%+.3f%%" % ((nav / base - 1) * 100),
                     "说明": "现金取 hb-c 口径 945736.38（含 002652 卖出 16200 未扣费、未入账）；估算值，账本无 11/5 回执"},
    "conditional_watch": [
        "14:30 场次（hb-e）裁定存量持仓的预案条件不变：涨停≤70 且 炸板率≥0.35 且 603906/002292 同时转绿（相对成本≤0）→ B 级预案外防守；本场 13:34 涨停 72（>70）、603906 +1.49%／002292 +3.26%（均未转绿）→ 条件不成立，不提前抢跑",
        "龙蟠科技 603906 自日高 16.38（10:48）回落至 15.80（−3.54%），仍在成本 +1.49%；其所在锂电材料链在炸板池有 石大胜华 5.38／盛新锂能 5.72／融捷股份 6.47 三只。若 14:30 前再破 15.57（成本）→ 进 hb-e 讨论，本场不抢跑",
        "中稀有色 600259 自日高 64.12（10:10）回落 −2.81%，成本 +3.47%；收盘了结腿照 playbook 14:57 后执行，盘中不动",
        "传媒线午后转强（吉视传媒 13:16 封、博纳影业 13:25 封、广告营销 3 只涨停）但全为首板无梯队；若 14:30 出现该线 2 板 + 奥飞同步走强，才谈预案外承接，且禁打板价",
        "光伏线 17→12 只涨停、炸 6（迈为 14.95／奥特维 14.55／正泰电源 7.5／福斯特 6.1／国晟 5.32／清源 4.59）＝主线午后扩散炸板，今日不接该线任何票",
        "002992 宝明科技现 −5.78%、688809 强一股份现 +5.24%：09:25 双弃单的机会成本待收盘按 hb-a 结算，不在盘中补买"
    ],
    "account_integrity": [
        "pulse.json / 执行流水.jsonl / 今日 warboard.json / 报警_20261105.jsonl 四项全缺（连续第 3 场，规格漂移待盘后总审立案）",
        "master 状态.json date=20261104、账本.jsonl 末条 11-04 20:25 → 11/5 零事件，净值全部标『估算』",
        "本场零参数改动、零引擎改动：只新增取数/分析/写入三类脚本（_hb_d_*），playbook 未动、阈值未动"
    ],
    "修订记录": []
}

# ---- reason（触发证据，逐条来自本场文件）----
p2900 = pos["600299"]; p2905 = pos["600259"]; p3906 = pos["603906"]; p2292 = pos["002292"]
reason = f"""【触发证据·只用 ≤13:36 留档数据，无任何事后帧】
①数据新鲜度：realtime_ticks 末帧 13:35:52（243 帧、09:31:00 起、最大帧间隔 61 秒、>180 秒断档 0 次）、腾讯快照 {q['fetched'][11:]}、东财三池 qdate={pools.get('zt_qdate')} 取数 {pools['fetched'][11:]}、持仓分时末 {pos['600299']['last']['t'][11:]} → 断更 0.7 分钟 << 10 分钟，允许决策。pulse.json / 执行流水.jsonl / 今日 warboard.json / 报警_20261105.jsonl 四项仍缺（连续第 3 场），成交回执不可核验，净值标『估算』。
②午后主读数＝涨停数修复但含金量下降：涨停 {ztn}（11:01 为 60，+{ztn-60}）、炸板 {zbn}（34→{zbn}）、炸板率 {rate}（0.3617→{rate}）、跌停 {len(dt)}、最高板 {max(x['lbc'] for x in zt)}（闽发铝业/浙文影业）。表面回暖，但结构反证：午后新封 {len(new_afternoon)} 只全部首板、行业高度分散（{('、'.join(f'{k}{v}' for k,v in na_hy.most_common(6)))}），无一条线形成梯队；同时光伏设备涨停 17→{sum(1 for x in zt if x.get('hybk')=='光伏设备')}、炸板池光伏 6 只（迈为 14.95／奥特维 14.55／正泰电源 7.5／福斯特 6.1／国晟 5.32／清源 4.59），半导体炸 4（雅克 6.12／通富 6.17／新洁能 6.86／金海通 6.86）→ 两大主线双双扩散炸板。昨日涨停池 116 只均涨 4.74（11:30）→4.35（13:04）→{an['width'][-1]['均涨']}（13:33）、贴板≥9.6% 由 21 降至 {an['width'][-1]['贴板>=9.6']}、破-3 由 6 升至 {an['width'][-1]['破-3']}、破-8 由 0 升至 {an['width'][-1]['破-8']}（大连友谊 −8.52）。定性：不是新资金进攻，是主线熄火后低位杂线轮流脉冲＋首板囤积；指数同步走弱（上证 −0.26%、深成 +0.78% 从 +1.42% 回落、创业板 +0.29% 从 +1.28% 回落）。
③A 级（预案内 trigger）：本场无到期 trigger。playbook 两条 buy_gate 均为 09:25 一次性 gap 闸门且已判弃单（002992 现 −5.78% 已在破面；688809 现 +5.24%），按『发出版不可覆盖』维持弃单、不盘中补买。卖出腿 600299/600259 为收盘了结（执2 到点），执行时点 14:57 之后；603906 −3% 成本止损（15.10）未触、002292 −3% 止损（9.09）未触 → 全部持有。
④B 级（防守）：未达阈值，不下防守单。a) 持仓四只今日均未摸涨停价（涨停价 600299 9.32／600259 69.47／603906 17.08／002292 10.27，日高分别 8.59／64.12／16.38／9.75）→ 无炸板；无一只跌破成本：安迪苏 {p2900['pnl_pct']:+.2f}%（{p2900['last']['px']}，日高 {p2900['hi']['px']}@{p2900['hi']['t'][11:]}，创日新高于 13:36）、中稀有色 {p2905['pnl_pct']:+.2f}%（{p2905['last']['px']}，自日高 −{abs(p2905['dd_from_hi_pct']):.2f}%）、龙蟠科技 {p3906['pnl_pct']:+.2f}%（{p3906['last']['px']}，自日高 16.38 −{abs(p3906['dd_from_hi_pct']):.2f}%）、奥飞娱乐 {p2292['pnl_pct']:+.2f}%（{p2292['last']['px']}，自日高 −{abs(p2292['dd_from_hi_pct']):.2f}%）；近 2 分钟变化 安迪苏 {p2900['d2min_pp']:+.2f}pp／中稀有色 {p2905['d2min_pp']:+.2f}pp／龙蟠科技 {p3906['d2min_pp']:+.2f}pp／奥飞娱乐 {p2292['d2min_pp']:+.2f}pp → 三升一平，无同向跳水。b) 池内 2 分钟批量跳水（≤−3pp，午后 34 个窗口）：最大计数仅 1 只（13:00:45 大连友谊），无 ≥3 只窗口 → 不成立。c) 题材批量跳水对持仓：持仓所在线 化工/稀土/锂电材料/传媒 —— 传媒午后反而转强（吉视传媒 13:16、博纳影业 13:25 封板、广告营销 3 只涨停）；锂电线在炸板池 3 只（石大胜华／盛新锂能／融捷），龙蟠 −3.54% 自日高、但仍在成本 +1.49% 且 2 分钟仅 −0.13pp，属线内回吐不属批量跳水。hb-c 预留的 14:30 裁定条件（涨停≤70 且 炸板率≥0.35 且 603906/002292 同转绿）本场检查：涨停 {ztn}（不成立）、炸板率 {rate}（成立）、两只均未转绿（不成立）→ 不提前抢跑。
⑤C 级（预案外进攻）：仅记录、不建仓。午后唯一走强方向是传媒（3 只新封＋广告营销 3 只），但封板者全为首板、最高连板仅 1，无梯队无格级证据；且今日炸板率 {rate}、破-8 已出现、池内均涨单边下滑 → 进攻胜率条件不成立。持仓 002292 已覆盖该线 0.5%，再买＝单题材暴露翻倍而宽度不增。光伏线 12 只封死 ask1=0，任何买价＝涨停价，触『禁打板价』红线；半导体炸 4 中，接它＝接炸板。全场无合规新开仓点。
⑥自我审计（本场唯一可量化对错）：09:25 双弃单当前 002992 −5.78%（弃对，省亏）、688809 +5.24%（弃错，少赚），两笔反向、净额待 15:00 按 hb-a 口径结算，本场不改判。"""
doc["reason"] = reason

fn = os.path.join(D, "临盘决断_20261105_1330.json")
json.dump(doc, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written", fn, os.path.getsize(fn), "bytes")
print("涨停", ztn, "炸板", zbn, "率", rate, "跌停", len(dt), "最高板", max(x["lbc"] for x in zt))
print("持仓市值", round(mv, 2), "NAV估算", nav, "当日", "%+.3f%%" % ((nav / base - 1) * 100))
for p in positions:
    print(p["code"], p["name"], p["px"], p["pct"], "pnl", p["pnl_pct"], "dd_hi", p["dd_from_hi_pct"], "摸板", p["touched_limit_today"])
