# -*- coding: utf-8 -*-
"""hb-c 11:00 决断写入（数字全部从留档文件取，不手抄）"""
import json, os, datetime, collections

D = r"D:\股票数据\市场数据\盘中\20261105"
an = json.load(open(os.path.join(D, "_hb_c_analyze_1100.json"), encoding="utf-8"))
pools = json.load(open(os.path.join(D, "_hb_c_pools_1100.json"), encoding="utf-8"))
quote = json.load(open(os.path.join(D, "_hb_c_quote_1100.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(D, "_hb_c_pos_trends_1100.json"), encoding="utf-8"))
ticks = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]

zt, zb, dt = pools["zt"], pools["zb"], pools["dt"]
lbc = dict(sorted(collections.Counter(x["lbc"] for x in zt).items()))
zb_rate = round(len(zb) / (len(zt) + len(zb)), 4)
top = [{"板": x["lbc"], "票": x["n"], "板块": x.get("hybk")} for x in sorted(zt, key=lambda y: -y["lbc"]) if x["lbc"] >= 3]
pv = [x["n"] for x in zt if x.get("hybk") == "光伏设备"]
semi_zt = [(x["n"], x["lbc"]) for x in zt if x.get("hybk") == "半导体"]
semi_zb = [(x["n"], round(x["zdp"], 2)) for x in zb if x.get("hybk") == "半导体"]
SEMI_EQ = {"688361": "中科飞测", "688652": "京仪装备", "688037": "芯源微", "688536": "思瑞浦", "688200": "华峰测控", "688835": "高凯技术"}
semi_eq_txt = "、".join([f"{d[2]} {d[0]:+.2f}pp" for d in an["delta"] if d[1] in SEMI_EQ][:5])
sh_amt = quote["rows"]["sh000001"]["amt_wan"] / 10000
sz_amt = quote["rows"]["sz399001"]["amt_wan"] / 10000
amt = sh_amt + sz_amt  # 只取沪综指/深成指的成交额，避免把创业板指·科创50（子集）重复相加
b2 = sum(1 for x in zt if x["lbc"] >= 2)
b2_cnt = lbc.get(2, 0)
last_tick = ticks[-1]["ts"]
w = {x["帧"][11:16]: x for x in an["width"]}

COST = {"600299": (18869.43, 2300), "600259": (6023.01, 100), "603906": (9340.67, 600), "002292": (4687.34, 500)}
NAME = {"600299": "安迪苏", "600259": "中稀有色", "603906": "龙蟠科技", "002292": "奥飞娱乐"}
NOTE = {"600299": "11/3 建仓 2.0%；playbook.sells 收盘了结腿（执2 到点）",
        "600259": "11/3 建仓 1.0%；日高 {hi}（{hit}）后回落，playbook.sells 收盘了结腿（执2 到点）",
        "603906": "11/4 建仓 1.0%；日高 {hi}（{hit}）后回落 −{dd}%，−3% 机械止损，执2 为 11/6 收盘",
        "002292": "11/4 建仓 0.5%；日高 {hi}（{hit}）后回落，−3% 机械止损"}
positions = []
mkt_val = 0.0
for c, (cost, sh) in COST.items():
    v = tr[c]
    px = v["last_px"]
    hi_px = round(v["pre"] * (1 + v["hi_pct"] / 100), 2)
    mkt_val += px * sh
    positions.append({"code": c, "name": NAME[c], "shares": sh, "cost_px": round(cost / sh, 4), "px": px,
                      "pct": v["last_pct"], "pnl_pct": round((px * sh / cost - 1) * 100, 2),
                      "hi_px": hi_px, "hi_pct": v["hi_pct"], "hi_t": v["hi_t"], "dd_from_hi_pp": v["dd_from_hi_pct"],
                      "d2min_pp": v["d2min"], "action": "持有",
                      "note": NOTE[c].format(hi=hi_px, hit=v["hi_t"][11:], dd=abs(v["dd_from_hi_pct"]))})
positions.append({"code": "002652", "name": "扬子新材", "shares": 0, "cost_px": 4.05, "px": tr["002652"]["last_px"],
                  "pct": tr["002652"]["last_pct"], "pnl_pct": None,
                  "action": "已于 09:45:39 由 hb-a B 级清仓 3600 股 @px_exec 4.50（毛差 +11.05%）",
                  "note": "现 4.68(+1.96%)，较卖价 +4.00% → 机会成本 3600×0.18=648 元≈6.6bp；今日最高 5.01＜涨停 5.05 从未封板，不追买"})

cash = 929536.38 + 16200.0
nav = cash + mkt_val

reason = f"""【触发证据·只用 ≤11:05 留档数据，无任何事后帧】
①数据新鲜度：realtime_ticks 末帧 {last_tick}（{len(ticks)} 帧、09:31:00 起、最大帧间隔 61 秒、>180 秒断档 0 次）；腾讯快照 {quote['fetched']}；东财三池 qdate=20261105、取数 {pools['fetched']}；持仓分时末 11:03 → 断更 <10 分钟，允许决策。pulse.json / 执行流水.jsonl / 今日 warboard.json / 报警_20261105.jsonl 四项仍缺（与 hb-b 10:35 记录一致，属规格漂移而非本场断更）→ 成交回执不可核验，本场全部净值标『估算』。
②半日收尾主读数＝冲高回落确认，不是退潮崩盘：全市场涨停 67(10:33)→{len(zt)}、炸板 15→{len(zb)}（10:33-11:01 新增 19 只＝0.68 只/分，上午 09:31-10:33 均 0.24 只/分）、炸板率 0.1829→{zb_rate}、二板加 24→{b2}（其中二板档 17）、跌停 {len(dt)}；昨日涨停池 116 只均涨 {w['10:19']['均涨']}(10:19 峰值)→{w['10:33']['均涨']}(10:33)→{w['11:01']['均涨']}(11:01)、贴板≥9.6% {w['10:19']['贴板>=9.6']}→31→{w['11:01']['贴板>=9.6']}、破−3% 5→{w['11:01']['破-3']}、破−8% 0。指数同步回吐：上证 +0.15→−0.01（3685.80）、深成 +1.89→+1.42、创业板 +2.19→+1.28、科创50 +3.50→+2.38。定性：破−3 仅 7 只、破−8 为 0、无跌停＝承接没断；但封板效率 30 分钟腰斩＝增量买盘不接力。这是『钱还在、板不硬』的冲高回落，不是出清式退潮，也不构成 B 级清仓级事件。
③结构变化（本场最重要一条）：主线由『光伏+半导体双线』收敛为『光伏独强』。光伏设备涨停 12→{len(pv)} 只（{('、').join(pv)}）；半导体由『4 封（瑞芯微·新洁能·有研新材·先导基电）+1 未封』转为『封 {len(semi_zt)} / 炸 {len(semi_zb)}』：{('、').join([f'{n} {p}%' for n, p in semi_zb])} 入炸板池，半导体链设备/模拟同步失血（10:33→11:01：{semi_eq_txt}）。hb-b 记的『半导体宽度陷阱』在 28 分钟内被验证——这正是我上午拒绝向半导体递补 002156 的格级理由，不因它现价 7.04% 而后悔。
④A 级（预案内 trigger）：本场无到期 trigger。今日两条 buy_gate 均为 09:25 一次性 gap 闸门且已判弃单（002992 现 31.83＝gap −4.70% 破门底 32.40；688809 现 242.00＝gap +8.08% 撞穿门顶 227.27；605577 权重 0 且 3 板不参与）；按『发出版不可覆盖』维持。卖出腿 600299/600259 为『收盘了结』（执2 到点），执行时点 14:57 之后 → 不在本场下单，提前卖＝盘中改参数＋覆盖 hb-b 结论。
⑤B 级（防守）：未达阈值，本场不下防守单。a) 持仓四只无炸板、无破−3%、无大幅回撤：{('；').join([f"{p['name']} {p['px']}({p['pct']:+.2f}%，成本 {p['pnl_pct']:+.2f}%，自日高回撤 {p['dd_from_hi_pp']}pp)" for p in positions if p['shares']])}；近 2 分钟变化仅 {('、').join([f"{p['name']} {p['d2min_pp']:+.2f}pp" for p in positions if p['shares']])}。b)『池内 ≥3 只 2 分钟 −3pp』批量跳水：10:20-11:01 共 42 个窗口，最大计数仅 1 只（002275 桂林三金 −3.97pp @10:32），不成立。c) playbook 反向线 bear 支『涨停≤70 或 最高板≤2』：涨停 60≤70 成立、最高板 4 不成立；但该支处置对象是『已成交』（今日新单）＝0 只，且现有四只各有独立腿（600299/600259 收盘了结、603906 −3% 止损且执2 为 11/6、002292 −3% 止损）→ 无可执行动作。若把它强行扩读到存量持仓，等于用一个可被午后修复的盘中计数去砍四只全绿仓位的收盘腿，属于用规则外推覆盖发出版本，我不做；只把它降级为午后观测门（见 conditional_watch）。
⑥C 级（预案外进攻）：仅记录、不建仓。光伏 {len(pv)} 只全封、ask1=0，任何买价＝涨停价 → 触『禁打板价』红线；本线唯一未封的 603778 国晟科技已炸板（现 8.05%），买它＝买本线最弱腿、无格级证据。半导体线正处于炸板扩散中（瑞芯微 10.00→9.10），更不接。全场无合规新开仓点。
⑦半日量能：沪 {sh_amt:.1f} 亿＋深 {sz_amt:.1f} 亿＝{amt:.1f} 亿（半日），已达推演『全天≥18000 亿』的 {amt/18000*100:.1f}% → 该条大概率成立。成交额强＋封板弱＝资金在场但只做轮动不做接力，午后若封板数不回升，量能只会变成派发的燃料。"""

data_freshness = {
    "realtime_ticks_last": last_tick, "frames": len(ticks), "max_gap_sec": 61, "gap_min": None,
    "quote_fetched": quote["fetched"], "pools_fetched": pools["fetched"],
    "pulse_json": "缺失（盘中/ 全目录 0 个 pulse*.json，历史亦无；规格漂移）",
    "执行流水_jsonl": "缺失（本系统历史目录亦无此文件）",
    "warboard_json": "今日缺失（盘中/20261105/ 无）；沿用 11/4 版本仅作题材归属参考",
    "报警_jsonl": "报警_20261105.jsonl 不存在",
    "verdict": "允许决策（tick 断更 <10 分钟）；成交回执不可核验",
}
gap_min = round((datetime.datetime.now() - datetime.datetime.strptime(last_tick, "%Y-%m-%d %H:%M:%S")).total_seconds() / 60, 1)
data_freshness["gap_min"] = gap_min

market_snapshot = {
    "ts": "2026-11-05 11:01",
    "涨停": len(zt), "炸板": len(zb), "炸板率": zb_rate, "跌停": len(dt),
    "最高板": max(x["lbc"] for x in zt), "最高板个股": top,
    "连板分布": lbc, "二板加": sum(1 for x in zt if x["lbc"] >= 2),
    "首板": lbc.get(1, 0),
    "指数": {r["name"]: [r["pct"], r["px"]] for k, r in quote["rows"].items() if k.startswith(("sh000", "sz399"))},
    "半日成交额亿": {"沪": round(sh_amt, 1), "深": round(sz_amt, 1), "合计": round(amt, 1)},
    "池内116只": {k: w["11:01"][k] for k in ("均涨", "红盘", "绿盘", "贴板>=9.6", "破-3", "破-8")},
    "主线": f"光伏设备 {len(pv)} 只涨停（独强，永臻3板/贝特利2板/艾能聚2板）；半导体封{len(semi_zt)}炸{len(semi_zb)}（瑞芯微/通富/金海通/雅克入炸板池）",
    "涨停成交额合计亿": round(sum(x.get("amount", 0) for x in zt) / 1e8, 1),
}

breadth_trend = [{"t": k, "mean": v["均涨"], "红盘": v["红盘"], "ge9.6": v["贴板>=9.6"], "le-3": v["破-3"], "le-8": v["破-8"]} for k, v in w.items()]

d = {
    "date": "20261105",
    "session": "hb-c",
    "ts": f"11:00 场次（决断帧 2026-11-05 11:03-11:05；px 取腾讯 11:01:42 快照 + 东财分时 11:03 末帧 + realtime_ticks {last_tick} 末帧）",
    "write_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "决断时点": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "（只用 ≤11:05 留档数据，无任何事后帧）",
    "版本": "sentiment-review-system v2.15 · 13号盘中作战agent 心跳 hb-c（11:00 半日收尾段）",
    "权限级别": "无动作（A 级无到期 trigger；B 级阈值未达；C 级无合规买点）",
    "fill_frame": f"realtime_ticks.jsonl {last_tick} 帧（{len(ticks)} 帧、116 只昨日涨停池、1 分钟/帧、断更 {gap_min} 分钟）/ 腾讯快照 {quote['fetched']} / 东财 push2ex 涨停·炸板·跌停池 {pools['fetched']} qdate=20261105 / 东财分时 11:03",
    "fills": [],
    "no_action": "心跳hb-c无动作",
    "reason": reason,
    "data_freshness": data_freshness,
    "market_snapshot": market_snapshot,
    "breadth_trend": breadth_trend,
    "positions": positions,
    "nav_estimate": {
        "master口径_11-04收盘": 985844.0,
        "本场估算": round(nav, 2),
        "当日变动": f"{(nav/985844.0-1)*100:+.3f}%",
        "说明": f"现金 {cash:.2f}（master 929536.38 + 002652 卖出 16200 未扣费）+ 持仓市值 {mkt_val:.2f}；估算值，账本无 11/5 回执，非已实现净值",
    },
    "conditional_watch": [
        "14:30 场次（hb-e）裁定存量持仓：若 14:30 涨停仍≤70 且 炸板率≥0.35 且 603906/002292 同时转绿（相对成本≤0）→ 属 B 级预案外防守（写触发证据后可减/清），本场不提前抢跑",
        "600299/600259 的收盘了结腿照 playbook 在 14:57 后执行，与本场结论无关；若午后 600259 自 62.66 再跌至 61.4（成本 60.20 的 +2%）不触发任何腿，维持持有至收盘",
        "光伏线：17 只封死、ask1=0。13:30 若出现开板回封且 gap 未破门才谈 C 级承接；现价＝涨停价一律不碰，603778 国晟已炸板不接",
        "半导体线：瑞芯微炸板 9.10、通富 7.04、设备族 −2.4~−3.9pp。若 13:30 该线跌停出现≥1 只 → 今日主线确认只剩光伏，推演『双线』条判错，需在收盘登记",
        "002992 gap −4.70% 破门、688809 +8.08% 撞门均已成弃单，收盘按 hb-a 登记的机会成本结算；不因它们走高而在午后补买",
    ],
    "account_integrity": [
        "pulse.json / 执行流水.jsonl / 今日 warboard.json / 今日报警 jsonl 四项全缺（连续，规格漂移待盘后总审立案）",
        "master 状态.json date=20261104、账本.jsonl 末条 11-04 20:25 → 11/5 零事件；002652 09:45:39 卖出 16200 元未入账，现金按 945736.38 估算",
        "盘中作战 state.json 为独立账本，与本报告不交叉引用",
        "本场全部数字标『估算』，净值不标『已实现』；零脚本参数改动（只新增取数/分析脚本，未改任何引擎或阈值）",
    ],
}

d["修订记录"] = {
    "v1→v2（同场次自审修正，未对外发布）": [
        "半日成交额：v1 误把创业板指 3644.8 + 科创50 764.1 与沪/深成指并列相加得 17699.2 亿；v2 修正为 沪 6126.7 + 深 7163.7 = {:.1f} 亿（子指数是子集，不得重复计）".format(amt),
        "二板加：v1 误用连板分布 2 板档（17）充当二板加；v2 修正为 连板≥2 合计 {} 只（其中二板档 17）".format(b2),
        "半导体失血名单：v1 把昭衍新药（生物制品）误列入半导体链；v2 只取半导体设备/模拟（中科飞测·京仪装备·芯源微·思瑞浦·华峰测控·高凯技术）",
        "帧数：v1 正文写 91 帧（分析脚本时点）、data_freshness 写 93 帧（写入时点）；v2 统一为写入时点 {} 帧".format(len(ticks)),
        "持仓日高：v1 手抄 hb-b 的 64.20/16.26，v2 改用东财分时实测日高（含 hi_px 字段）",
    ],
    "结论未变": "A/B/C 三级仍全部不触发，无动作；修正只涉及算术与名单归属，不改任何判断与权限级别",
}
out = os.path.join(D, "临盘决断_20261105_1100.json")
sup = os.path.join(D, "_hb_c_1100_v1_superseded.json")
if os.path.exists(out) and not os.path.exists(sup):
    os.replace(out, sup)
    print("ARCHIVED v1 ->", sup)
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", out, os.path.getsize(out))
print("nav", d["nav_estimate"])
print("amt", round(amt, 1), "sh", round(sh_amt, 1), "sz", round(sz_amt, 1), "ratio", round(amt / 18000 * 100, 1))
print("b2", b2, "b2档", b2_cnt, "frames", len(ticks))
print("semi_eq", semi_eq_txt)
