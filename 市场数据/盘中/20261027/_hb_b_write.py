# -*- coding: utf-8 -*-
"""hb-b 10:30 场决断件构建：机械算 px_exec / pnl，写入临盘决断_20261027_1030.json（assert 不存在）。"""
import json, os, math, datetime, statistics

D = os.path.dirname(os.path.abspath(__file__))
SIM = r"D:\股票数据\市场数据\_学习\_模拟盘"
TARGET = os.path.join(D, "临盘决断_20261027_1030.json")

dec = json.load(open(os.path.join(D, "_hb_b_quote_exec.json"), encoding="utf-8"))   # 决断帧 10:38:11
nxt = json.load(open(os.path.join(D, "_hb_b_quote_next.json"), encoding="utf-8"))    # 决断后下一帧 10:38:49

def px_exec_sell(code):
    px = nxt["quote"][code]["px"]
    return math.floor(px * 0.999 * 100) / 100, px

def limit_up(code, pre):
    if code.startswith(("300", "301", "688", "689")):
        return round(pre * 1.2, 2)
    if code.startswith(("8", "4", "920")):
        return round(pre * 1.3, 2)
    return round(pre * 1.1, 2)

legs = [
    # (route, code, name, qty, level, rule_src)
    ("master", "002242", "九阳股份", 800, "A", "交易计划_master_20261026#sells[0] leg=open"),
    ("master", "003021", "兆威机电", 100, "A", "交易计划_master_20261026#sells[1] leg=open（@85.0 批次）"),
    ("master", "300296", "利亚德", 4100, "A", "交易计划_master_20261026#sells[2] leg=open（规则外主动减仓）"),
    ("master", "002979", "雷赛智能", 300, "A", "交易计划_master_20261026#sells[3] leg=open（-3% 机械止损触发）"),
    ("master", "003021", "兆威机电", 100, "A", "交易计划_master_20261026#sells[4] leg=open（@93.0 批次）"),
    ("master", "300561", "汇金科技", 600, "A", "交易计划_master_20261026#sells[5] leg=open"),
    ("auction", "003021", "兆威机电", 200, "A", "交易计划_auction_20261026#sells[1] leg=open（T+1 未涨停→T+2 无条件卖）"),
    ("limitup", "003021", "兆威机电", 100, "A", "交易计划_limitup_20261026#sells[1]（清仓 100 股 @85.0 批次，T+1 开盘腿）"),
]

fills = []
stats_by_route = {}
for route, code, name, qty, lvl, src in legs:
    st = json.load(open(os.path.join(SIM, route, "state.json"), encoding="utf-8"))
    pos = None
    for p in st["positions"]:
        if p["code"] == code and abs(p["shares"] - qty) < 1e-6:
            if pos is not None:
                # 同码同量多条（003021 两批 100 股）：按 buy_px 顺序取未用过的
                continue
            pos = p
    # 003021 100 股两批：按 @85 / @93 顺序消费
    used85 = [f for f in fills if f["code"] == "003021" and f["route"] == route]
    if code == "003021" and qty == 100:
        want = 85.0 if not used85 else 93.0
        pos = next((p for p in st["positions"] if p["code"] == code and p["shares"] == 100
                    and abs(p["buy_px"] - want) < 1e-6), None)
    px_exec, px_q = px_exec_sell(code)
    proceeds = round(px_exec * qty, 2)
    cost = pos["cost"]
    pnl = round(proceeds - cost, 2)
    ret = round(pnl / cost * 100, 2)
    fills.append({
        "ts": nxt["ts"], "code": code, "name": name, "action": "fill_sell",
        "px": px_q, "px_exec": px_exec, "qty": qty,
        "route": route, "level": lvl, "rule_src": src,
        "buy_px": pos["buy_px"], "buy_date": pos["buy_date"], "cost": cost,
        "proceeds": proceeds, "pnl": pnl, "ret_pct": ret,
        "fill_formula": f"{px_q}×(1-0.10%)={px_q*0.999:.5f}→向下取 2 位={px_exec}",
    })
    agg = stats_by_route.setdefault(route, {"n": 0, "proceeds": 0.0, "cost": 0.0, "pnl": 0.0})
    agg["n"] += 1; agg["proceeds"] += proceeds; agg["cost"] += cost; agg["pnl"] += pnl

for r, a in stats_by_route.items():
    a["proceeds"] = round(a["proceeds"], 2); a["cost"] = round(a["cost"], 2); a["pnl"] = round(a["pnl"], 2)
    a["ret_pct"] = round(a["pnl"] / a["cost"] * 100, 2)
    st = json.load(open(os.path.join(SIM, r, "state.json"), encoding="utf-8"))
    a["cash_before"] = st["cash"]
    a["cash_after"] = round(st["cash"] + a["proceeds"], 2)

# 与「若按时开盘价成交」的对比（延误副产品，仅披露，不作为延误理由）
open_basis = {"002242": 21.25, "003021": 93.60, "300296": 6.60, "002979": 54.65, "300561": 14.85}
delay_cmp = []
for f in fills:
    ob = open_basis[f["code"]]
    delay_cmp.append({"code": f["code"], "route": f["route"], "qty": f["qty"],
                      "open_px": ob, "fill_px": f["px_exec"],
                      "diff_yuan": round((f["px_exec"] - ob) * f["qty"], 2)})
delay_total = round(sum(x["diff_yuan"] for x in delay_cmp), 2)

# 执行前在持市值（按决断帧 10:38:11 报价）
_qd = dec["quote"]
_mv = 0.0
_mv_detail = []
for p in json.load(open(os.path.join(SIM, "master", "state.json"), encoding="utf-8"))["positions"]:
    px = _qd[p["code"]]["px"]
    v = round(px * p["shares"], 2)
    _mv += v
    _mv_detail.append(f"{p['code']} {p['shares']}×{px}={v}")
_mv = round(_mv, 2)
_master_cash = 895652.28
_nav_pre = round(_master_cash + _mv, 2)
_pos_pct = round(_mv / _nav_pre * 100, 2)
# 涨停价（按昨收×板别限幅，用于「无板可炸」论证）
_lim = {c: limit_up(c, _qd[c]["pre"]) for c in ("002242", "003021", "300296", "002979", "300561")}
_no_zt = "；".join(
    f"{c} {_qd[c]['name']} 今高 {_qd[c]['high']} vs 涨停 {_lim[c]}（{'未触及' if _qd[c]['high'] < _lim[c] else '触及'}）"
    for c in ("002242", "003021", "300296", "002979", "300561"))

# 三本账今日成交行数（证明 hb-a 未入账）
_today_rows = {}
for _b in ("master", "auction", "limitup"):
    _rows = [json.loads(l) for l in open(os.path.join(SIM, _b, "账本.jsonl"), encoding="utf-8") if l.strip()]
    _today_rows[_b] = sum(1 for r in _rows if str(r.get("ts", "")).startswith("2026-10-27"))
assert sum(_today_rows.values()) == 0, f"今日已有成交行，禁止重复执行: {_today_rows}"

_zt_early = sum(1 for r in dec["zt"] if (r.get("fbt") or 999999) <= 93500)

for f in fills:
    f["rule"] = ("A 级·预案内 catch_up：卖出腿原文均已写死『开盘无条件平出、不限价、不等反抽』/『T+2 开盘无条件卖』；"
                 "今日 09:40 场（hb-a，executions.db 记 09:40:12→09:45:33 completed）未落任何决断件、未入账，"
                 "开盘卖出腿 8 条全部漏执行 → 本场补执行（与 20261026 hb-a 同一 catch_up 口径）")

judgment = {
    "date": "20261027", "session": "hb-b", "ts": "10:30",
    "write_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "版本": "v1 · 10:30 趋势确认段（决断帧=腾讯报价 10:38:11；成交基准=决断后下一帧 10:38:49；池帧 09:31:02~10:35:13 共 65 帧；东财 ZT/ZB/DT 池 10:38:11）",
    "场次说明": ("20261027(周二) hb-b。★零后视镜：决策仅用 10:38:11 之前已落盘数据（池帧 65 帧 + 决断帧报价 + 东财池）；"
             "fills 的 px_exec 只由决断后下一帧 10:38:49 留档价机械算出（向下取 2 位、滑点 -0.10%）。"
             "★盘中禁改参数：未改任何生产脚本/预案/权重/阈值。★发版不可覆盖：写前 assert 目标文件不存在。"),
    "交易日校验": {
        "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → FAIL: ModuleNotFoundError: No module named 'sentiment'（规格漂移第 7 个交易日，非本场故障）",
        "本机等效真源": "系统时间 2026-10-27 星期二；池帧 65 帧真实分化（末帧中位 +2.92%、15 只≥+9.8%、1 只≤-9.8%）→ 判交易日，不早退",
    },
    "数据新鲜度": {
        "pulse.json": "不存在（连续缺件；本场改用 realtime_ticks.jsonl 作新鲜度真源）",
        "池帧": {"文件": "盘中/20261027/realtime_ticks.jsonl", "帧数": 65,
               "窗口": "2026-10-27 09:31:02 ~ 2026-10-27 10:35:13",
               "末帧龄_决断时": "≈3 分钟（10:35:13 → 10:38:11）", "最大间隔": "61s",
               "pool_date": "20261026", "pool_stale": False, "n": 55,
               "判定": "未断更（最大间隔 61s << 10 分钟门槛）→ 可决策"},
        "个股/指数": {"源": "qt.gtimg.cn", "时戳": "2026-10-27 10:38:11（决断帧）/ 10:38:49（成交帧）"},
        "市场闸门源": {"源": "push2ex.eastmoney.com getTopicZTPool/ZBPool/DTPool", "date": "20261027",
                  "取数时点": "10:38:11", "涨停": 43, "炸板": 12, "跌停": 0, "炸板率": round(12 / 55, 4), "最高连板": 5},
        "缺件": {"warboard.json": "不存在", "执行流水.jsonl": "不存在", "报警_20261027.jsonl": "不存在", "playbook.json": "不存在（连续第 6 次）"},
        "口径": "缺件如实标注、不补造；warboard 缺失使『预案内 trigger』只能用 _学习/交易计划_*_20261026.json 作真源",
    },
    "权限分级": {
        "A": f"8 笔卖出（预案内 catch_up）：master 6 笔（002242 800 / 003021 100@85 / 003021 100@93 / 300296 4100 / 002979 300 / 300561 600）＋auction 003021 200 ＋ limitup 003021 100。0 笔买入。",
        "B": "0 笔。三项防守触发条件均未达成（见 防守三查）；limitup 两条无腿仓位（003021@93 100、300561 600）已具『本路不留隔夜』违约证据，但无卖出腿，按不越界原则留 11:00 hb-c 处置（照会非决断）。",
        "C": "0 笔。预案外不做进攻：①master 今日计划为纯现金（09:21 场两只条件单已双弃），防守档 + 冰点档环境下加仓无预案背书；②池内 15 只涨停多为一字/秒板（001219/600558/603528/603028/002708 首封 09:25 附近），追买 = 打板价，C 级铁律禁；③只记录不动作（见 观察照会）。",
    },
    "fills": fills,
    "fills_汇总": {"按账": stats_by_route,
                "合计": {"n": len(fills), "proceeds": round(sum(f["proceeds"] for f in fills), 2),
                       "cost": round(sum(f["cost"] for f in fills), 2),
                       "pnl": round(sum(f["pnl"] for f in fills), 2)}},
    "延误副产品披露": {
        "口径": "若 8 条腿按 09:30 开盘价成交的对照（仅披露迟到的影响，不构成对迟到的辩护）",
        "逐笔": delay_cmp, "合计差额_元": delay_total,
        "结论": ("迟到 70 分钟对本批成交为净有利（主因 002979 由开盘 54.65 拉到 57.16、002242 21.25→21.71）；"
               "但纪律上不得以结果反推延误合理——迟到本身已违反『开盘无条件平出、不等反抽』的时点条款，属系统执行断链，已入异常与欠账。"
               "唯一逆行的是 300561（14.85→14.58，-1.8%）。"),
    },
    "持仓核_执行前": {
        "master": f"002242 800@22.02 / 003021 100@85.0 / 003021 100@93.0 / 300296 4100@7.25 / 002979 300@55.86 / 300561 600@14.90；现金 {_master_cash}；在持市值按决断帧 {_mv}（{'; '.join(_mv_detail)}）→ 仓位 {_pos_pct}%",
        "auction": "003021 200@85.0、002474 2400@7.72；现金 923,460.04",
        "limitup": "003021 100@85.0、003021 100@93.0、300561 600@14.90；现金 961,980.98",
        "lhb": "300296 5500@7.25；现金 963,832.36",
        "logic": "002979 300@55.86；现金 994,008.99",
        "盘中作战": "空仓（09:21 场两只 buys 双弃，仓位 0%）",
        "账本实况": f"master/auction/limitup 账本.jsonl 今日成交行数={_today_rows}（hb-a 09:40 场未入账）→ 卖出腿 8 条处于『计划已写、执行未落』状态",
    },
    "防守三查": [
        f"①持仓炸板：master 6 只在持今日均未触及涨停价（{_no_zt}）→ 无板可炸，不适用。",
        "②大幅回撤：最深为 300296 对成本 -7.6%（今开 6.60、现 6.69，日内为修复方向、非新增破位）；002979 今日 +5.65% 已回到成本上方；002242 今日 +1.02% → 未出现『单票 2 分钟内 -3% 且对成本加速恶化』的新增回撤，不临时自造阈值。",
        "③题材批量跳水：65 帧逐帧 2 分钟扫描（间隔≥100s 配对），近 30 分钟最大簇 = 1 只跌≥3pp（10:18:10 正裕工业 -3.22pp），阈值 3 只 → 未触发；全天最大簇 3 只（09:34:02 科瑞思 -4.97 / 兰生股份 -3.05 / 林州重机 -6.90，已过 1 小时）。",
    ],
    "环境读数": {
        "指数": {"上证": "3694.18 -0.09%", "深成": "11509.28 -0.22%", "创业板": "2626.29 -0.45%", "科创50": "1298.79 -1.27%",
               "对比昨日同时段": "昨日 hb-b 为 上证 -0.63 / 创业板 -2.83 / 科创50 -2.81 → 今日全面收敛，风险偏好由恐慌转中性偏弱"},
        "昨涨停池n=55": {"中位": "+2.92%", "均值": "+3.42%", "涨": 40, "跌": 15, "≥+9.8%": 15, "≤-5%": 4, "≤-9.8%": 1,
                     "轨迹": "中位 09:31 +1.09 → 10:01 +1.45 → 10:21 +2.54 → 10:35 +2.92（单边抬升，与昨日单边收敛相反）",
                     "掉板": "首帧 9 只涨停中现仍涨停 7 只（掉板 2：301314 科瑞思 15.5→7.71、600826 兰生股份 9.98→5.23），掉板率 22.2%"},
        "全市场": {"涨停": 43, "炸板": 12, "跌停": 0, "炸板率": 0.218, "最高连板": 5,
                "最大行业": "汽车零部 12 只（≥8 → 线级门若用于汽车零部为放行态；本场无买入腿，不涉及）",
                "对比昨日同时段": "涨停 32→43、跌停池 0→0、炸板率 0.385→0.218 → 宽度修复、封板质量改善"},
        "判断": f"情绪=冰点后修复日的第一次确认：昨涨停池溢价单边抬升（中位 +1.09→+2.92）、全市场涨停 43 / 炸板率 21.8% / 跌停 0、指数跌幅收敛至 -0.1~-0.5%。属『修复但未转强』——全市场 43 只涨停中 {_zt_early} 只首封 ≤09:35:00（09:25:00 附近 5 只：000058/001219/600558/603528/603028），秒板占近半、承接未经换手检验；指数仍在零轴下方；汽车零部单线 12 只扎堆=结构单薄。结论：环境支持『按计划清仓兑现』，不支持『新开仓』。",
    },
    "复盘_上一场清单核销": [
        "①09:21 场『6 条卖出腿仅登记、成交=null』→ 本场核销：证实未执行（三本账今日 0 条成交行、state 仓位未变），本场按 catch_up 全部补执行，成交价见 fills（非开盘价，已披露延误）。",
        "②09:21 场两只条件单双弃（688386 gap+0.95 判 B、000700 gap-1.30 落带外判 B）→ 盘中机会成本如实记（快照非收盘结算）：688386 现 48.74（开盘 47.00，+3.70%）、000700 现 13.83（开盘 12.90，+7.21%）→ 弃单今日为双向错失，两笔若各 1.0% 权重，错失约 +0.037% / +0.072%（按 nav 985,076）。不因结果改判：09:21 的弃买依据是『竞价单边回落 + 闸门临界不可核验』，逻辑当时成立。",
        "③09:21 场『全场否决门覆盖 71%、判定=无法核验』→ 今日无需再核（无买入腿）；登记为流程欠账（缺 09:25:05 全量快照口径）。",
        "④playbook 缺件（09:21 场登记第 5 次）→ 今日盘中/20261027/ 仍无 playbook.json，缺件第 6 次；本场未依赖。",
    ],
    "观察照会_非条件决断": [
        "limitup 003021@93.0 100 股（成本 9,304.65，现 95.18 +2.3%）与 300561 600 股（成本 8,944.47，现 14.60 -2.2%）：无卖出腿，但本路买入理由写明『当日价差、不留隔夜』→ 已过夜违约。本场不越界代路处置，留 11:00 hb-c 决断（建议：按违约清出，证据为 limitup 账本 20261026 18:40 补账买入行 + 20261026 hb-a 对同一规则已执行的先例）。",
        "auction 002474 榕基软件 2400@7.72（现 6.81，-11.8%，今日 -2.85%）：无卖出腿、最深浮亏。照会：若 11:00 仍无腿，建议按路线自订止损表态，不代决。",
        "lhb 300296 5500@7.25（现 6.70，-7.6%）：T+1 无卖出腿（lhb 今日计划 sell 仅 002639 且已于 10/26 落地）。照会：master 同票 4100 已按预案清出，lhb 5500 仍全额在场，两账对同票方向相反并存，需晚间计划统一。",
        "logic 002979 300@55.86（现 57.22，+2.4%）：T+1 无卖出腿；master 同票 300 已按 -3% 止损腿清出。同上，跨账方向冲突需晚间统一。",
        "预案外新机会（仅记录、不动作）：002820 桂发祥 10 分钟 +11.87pp 直线拉板、001318 阳光乳业 +6.78pp 至涨停、605333 沪光股份 +3.92pp 至涨停——均为汽车零部/食品线内新首板，属本场无买入权限下的『只记录』；不追、不进 C 级。",
    ],
    "异常与欠账": [
        "★执行断链（本场核心）：hb-a 09:40 场 executions.db 记 completed（09:40:12→09:45:33，delivery=suppressed），但盘中/20261027/ 无 0940 决断件、三本账 0 条成交 → 开盘卖出腿 8 条漏执行约 70 分钟，本场补执行。『无动作』与『空转/静默失败』在现有留档下不可区分。",
        "机制建议（待批，不动手）：hb 场次即使 no_action 也应落最小审计件（ts + 数据新鲜度 + 三查结论 + 未执行腿清单），否则事后无法举证；建议在 hb 模板第 4 步把『秒退』改为『写 _no_action_{session}.json 后退出』。",
        "缺件：pulse.json / warboard.json / 执行流水.jsonl / 报警_20261027.jsonl 全缺；playbook 缺件第 6 次。",
        "规格漂移：sentiment 包不存在第 7 个交易日（本场不修工程）。",
        "跨账镜像仓位未收口：003021 在 master/auction/limitup 三账共存 600 股、300561 在 master/limitup 共存 1200 股、300296 在 master/lhb 共存 9600 股 → 本场清了 master 全部 + auction/limitup 的计划腿，剩余 3 条无腿仓位留照会。",
    ],
    "下一场预置观察条件_非指令": [
        "11:00 hb-c：①limitup 003021@93 与 300561 是否按『不留隔夜』清出；②池内 ≥+9.8% 家数能否守住 12 只（当前 15），掉到 <12 = 修复夭折；③汽车零部 12 只扎堆是否继续扩张（>12 则线级门对任何买入放行，需重新评估 C 级空间）；④上证能否收复零轴（当前 -0.09%）。",
    ],
    "口径": "fill 价=决断后下一帧留档价×(1-0.10%) 向下取 2 位，毛利差未扣费用；『盘中快照』与『收盘结算』严格区分，本件不做任何收盘结算。",
}

assert not os.path.exists(TARGET), "目标已存在，禁止覆盖"
with open(TARGET, "w", encoding="utf-8") as f:
    json.dump(judgment, f, ensure_ascii=False, indent=1)
print("WROTE", TARGET, os.path.getsize(TARGET))
for f_ in fills:
    print(f_["route"], f_["code"], f_["qty"], "px_exec", f_["px_exec"], "pnl", f_["pnl"], f_["ret_pct"], "%")
print("汇总", judgment["fills_汇总"]["按账"])
print("延误差额", delay_total)
