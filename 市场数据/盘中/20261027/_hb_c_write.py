# -*- coding: utf-8 -*-
"""hb-c 11:00 场决断件构建：机械算 px_exec / pnl，写入 临盘决断_20261027_1100.json（assert 不存在）。"""
import json, os, math, datetime, statistics

D = os.path.dirname(os.path.abspath(__file__))
SIM = r"D:\股票数据\市场数据\_学习\_模拟盘"
TARGET = os.path.join(D, "临盘决断_20261027_1100.json")

dec = json.load(open(os.path.join(D, "_hb_c_probe.json"), encoding="utf-8"))   # 决断帧 11:04:46
nxt = json.load(open(os.path.join(D, "_hb_c_next.json"), encoding="utf-8"))    # 决断后下一帧 11:06:10
prev = json.load(open(os.path.join(D, "临盘决断_20261027_1030.json"), encoding="utf-8"))

def px_exec_sell(code):
    px = nxt["quote"][code]["px"]
    return math.floor(px * 0.999 * 100) / 100, px

def limit_up(code, pre):
    if code.startswith(("300", "301", "688", "689")):
        return round(pre * 1.2, 2)
    if code.startswith(("8", "4", "920")):
        return round(pre * 1.3, 2)
    return round(pre * 1.1, 2)

# (route, code, name, qty, level, trig, rule_src)
legs = [
    ("limitup", "003021", "兆威机电", 100, "B",
     "本路纪律『当日价差、不留隔夜』违约：买入行 20261026 18:40 补账，T+1=今日，计划 sell 无本票腿（漏腿）",
     "交易计划_limitup_20261026#buys/notes『本路纪律为当日价差、不留隔夜』；同日先例 603370 已按该规则 10/26 清出"),
    ("limitup", "300561", "汇金科技", 600, "B",
     "同上：无卖出腿 + 不留隔夜到期；今日 -2.09% 未封板",
     "交易计划_limitup_20261026#buys/notes『本路纪律为当日价差、不留隔夜』"),
    ("auction", "002474", "榕基软件", 2400, "B",
     "大幅回撤：对成本 -12.87%、今日 -3.99% 且现价距日内低 6.70 仅 +0.6%；买入理由（低开-0.93%后09:31:57秒板=分歧转一致）T+1 已证伪（今日未封板）；本路结算口径=T+1（开买→收），今日到期仍无卖出腿",
     "交易计划_auction_20261026#sells 无 002474（漏腿）；08_竞价命门agent.md『次日结算/T+1执行口径』"),
]

fills = []
stats_by_route = {}
for route, code, name, qty, lvl, trig, src in legs:
    st = json.load(open(os.path.join(SIM, route, "state.json"), encoding="utf-8"))
    pos = None
    for p in st["positions"]:
        if p["code"] == code and abs(p["shares"] - qty) < 1e-6:
            pos = p
            break
    assert pos is not None, f"state 未找到持仓 {route} {code} {qty}"
    px_exec, px_q = px_exec_sell(code)
    proceeds = round(px_exec * qty, 2)
    cost = pos["cost"]
    pnl = round(proceeds - cost, 2)
    ret = round(pnl / cost * 100, 2)
    op = nxt["quote"][code]["open"]
    fills.append({
        "ts": nxt["ts"], "code": code, "name": name, "action": "fill_sell",
        "px": px_q, "px_exec": px_exec, "qty": qty,
        "route": route, "level": lvl, "rule_src": src, "trigger_evidence": trig,
        "buy_px": pos["buy_px"], "buy_date": pos["buy_date"], "cost": cost,
        "proceeds": proceeds, "pnl": pnl, "ret_pct": ret,
        "fill_formula": f"{px_q}×(1-0.10%)={px_q*0.999:.5f}→向下取2位={px_exec}",
        "open_px": op, "diff_vs_open_yuan": round((px_exec - op) * qty, 2),
    })
    agg = stats_by_route.setdefault(route, {"n": 0, "proceeds": 0.0, "cost": 0.0, "pnl": 0.0})
    agg["n"] += 1; agg["proceeds"] += proceeds; agg["cost"] += cost; agg["pnl"] += pnl

for r, a in stats_by_route.items():
    a["proceeds"] = round(a["proceeds"], 2); a["cost"] = round(a["cost"], 2); a["pnl"] = round(a["pnl"], 2)
    a["ret_pct"] = round(a["pnl"] / a["cost"] * 100, 2)

delay_total = round(sum(f["diff_vs_open_yuan"] for f in fills), 2)

# 持仓核_执行前（机械读 state，禁手抄）
pre_hold = {}
for b in ("master", "auction", "limitup", "lhb", "logic"):
    st = json.load(open(os.path.join(SIM, b, "state.json"), encoding="utf-8"))
    pre_hold[b] = {
        "positions": [f"{p['code']} {p['name']} {p['shares']}股@{p['buy_px']}（成本{p['cost']}）" for p in st["positions"]],
        "cash": st["cash"],
    }

# 幂等：今日成交行数（本场前应为 hb-b 的 8 条）
_today_rows = {}
for b in ("master", "auction", "limitup"):
    rows = [json.loads(l) for l in open(os.path.join(SIM, b, "账本.jsonl"), encoding="utf-8") if l.strip()]
    _today_rows[b] = sum(1 for r in rows if str(r.get("ts", "")).startswith("2026-10-27"))
assert sum(_today_rows.values()) == 8, f"预期 hb-b 后今日 8 条、实际 {_today_rows}"
assert not [f for f in fills if f["route"] not in ("limitup", "auction")]

# 防守三查·炸板（机械算涨停价）
q = dec["quote"]; q2 = nxt["quote"]
hold_codes = [("003021", q2["003021"]), ("300561", q2["300561"]), ("002474", q2["002474"]),
              ("300296", q2["300296"]), ("002979", q2["002979"])]
no_zt = "；".join(
    f"{c} {m['name']} 今高 {m['high']} vs 涨停 {limit_up(c, m['pre'])}（{'未触及' if m['high'] < limit_up(c, m['pre']) else '触及'}）"
    for c, m in hold_codes)

# 池内衰减：与 hb-b 决断帧比
p_prev = prev["环境读数"]["昨涨停池n=55"]
pool_now = dec["pool_now"]
pool_prev = {"median": 2.92, "mean": 3.42, "up": 40, "down": 15, "ge98": 15, "le5": 4, "le98": 1}

zt_n = dec["zt_n"]; zb_n = dec["zb_n"]; dt_n = dec["dt_n"]
zt_rows = dec.get("zt_rows") or []
early = sum(1 for r in zt_rows if (r.get("fbt") or 999999) <= 93500)

judgment = {
    "date": "20261027", "session": "hb-c", "ts": "11:00",
    "write_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "版本": ("v1 · 11:00 半日收尾段（决断帧=腾讯报价 11:04:46；成交基准=决断后下一帧 11:06:10；"
           "池帧 09:31:02~11:04:18 共 94 帧；东财 ZT/ZB/DT 池 11:04:46）"),
    "场次说明": ("20261027(周二) hb-c。★零后视镜：决策仅用 11:04:46 之前已落盘数据；fills 的 px_exec 只由决断后"
             "下一帧 11:06:10 留档价机械算出（向下取 2 位、滑点 -0.10%）。★盘中禁改参数：未改任何生产脚本/预案/权重/阈值。"
             "★发版不可覆盖：写前 assert 目标文件不存在。"),
    "交易日校验": {
        "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → FAIL: ModuleNotFoundError: No module named 'sentiment'（规格漂移第 7 个交易日，非本场故障）",
        "本机等效真源": "系统时间 2026-10-27 星期二 11:00；池帧 94 帧持续更新（末帧 11:04:18、最大间隔 61s）且东财 ZT 池 44 只 → 判交易日，不早退",
    },
    "数据新鲜度": {
        "pulse.json": "不存在（连续缺件，第 8 个交易日）→ 改用 realtime_ticks.jsonl 作新鲜度真源",
        "池帧": {"文件": "盘中/20261027/realtime_ticks.jsonl", "帧数": 94,
               "窗口": "2026-10-27 09:31:02 ~ 2026-10-27 11:04:18",
               "末帧龄_决断时": "29s", "最大间隔": "61s", "pool_date": dec["frame"]["pool_date"],
               "pool_stale": dec["frame"]["stale"], "n": 55,
               "判定": "未断更（29s << 10 分钟门槛）→ 可决策"},
        "个股/指数": {"源": "qt.gtimg.cn", "时戳": "2026-10-27 11:04:46（决断帧）/ 11:06:10（成交帧）"},
        "市场闸门源": {"源": "push2ex.eastmoney.com getTopicZTPool/ZBPool/DTPool", "date": "20261027",
                  "取数时点": "11:04:46", "涨停": zt_n, "炸板": zb_n, "跌停": dt_n,
                  "炸板率": dec["zb_rate"], "最高连板": dec["max_lb"]},
        "缺件": {"warboard.json": "不存在", "执行流水.jsonl": "不存在", "报警_20261027.jsonl": "不存在",
               "playbook.json": "不存在（连续第 7 次）"},
        "口径": "缺件如实标注、不补造；warboard 缺失 → 预案内 trigger 只能用 _学习/交易计划_*_20261026.json 作真源",
    },
    "权限分级": {
        "A": "0 笔。三张 20261026 计划的买卖腿已在 hb-b 全部执行完毕（8 笔），本场无新增预案内腿；无买入腿。",
        "B": ("3 笔卖出（预案外防守，均写触发证据）：limitup 003021 100@93.0、limitup 300561 600@14.90"
              "（本路『当日价差、不留隔夜』违约+T+1 到期漏腿）；auction 002474 2400@7.72（对成本 -12.87% 大幅回撤 + "
              "买入理由 T+1 证伪 + 本路 T+1 口径到期漏腿）。0 笔买入。"),
        "C": (f"0 笔。①池内 ≥+9.8% 家数 15 只未破 12（修复未夭折）、全市场涨停 44 家、跌停 0 → 无恐慌杀跌型机会；"
              f"②涨停结构仍以早封/秒板为主（44 只中 {early} 只首封 ≤09:35），追买=打板价，C 级铁律禁；"
              f"③今日计划前置条件单已在 09:21 场双弃，无预案背书 → 不新开仓。"),
    },
    "fills": fills,
    "fills_汇总": {"按账": stats_by_route,
                "合计": {"n": len(fills), "proceeds": round(sum(f["proceeds"] for f in fills), 2),
                       "cost": round(sum(f["cost"] for f in fills), 2),
                       "pnl": round(sum(f["pnl"] for f in fills), 2)}},
    "延误披露": {
        "口径": "三条腿均无计划腿、非 hb-a 漏执行；本场是『计划漏腿 + 规则到期』的补处置，执行时点 11:06（T+1 开盘腿应为 09:30）",
        "对照开盘价": [{"code": f["code"], "open": f["open_px"], "px_exec": f["px_exec"],
                   "差额元": f["diff_vs_open_yuan"]} for f in fills],
        "合计差额_元": delay_total,
        "结论": ("迟到约 96 分钟对本批为净不利 -452 元（003021 +10、300561 -198、002474 -264）；"
               "不以结果反推时点合理，漏腿本身记入异常与欠账，责任在晚间计划未给腿、非本场决策。"),
    },
    "持仓核_执行前": {**pre_hold,
                 "盘中作战": "空仓（09:21 场两只 buys 双弃，仓位 0%）",
                 "账本实况": f"master/auction/limitup 账本.jsonl 今日成交行数={_today_rows}（=hb-b 8 笔）"},
    "防守三查": [
        f"①持仓炸板：五只在持今日均未触及涨停价（{no_zt}）→ 无板可炸，不适用（002474 今高 7.08 vs 涨停 7.71、300561 今高 14.85 vs 17.82 均为开盘价=最高价，全天单边弱）",
        ("②大幅回撤：触发 1 只——002474 对成本 -12.87%（成本 18,537.26、决断帧 6.73×2400=16,152）、今日 -3.99%、"
         "现价距日内低 6.70 仅 +0.6%（弱势贴低）；对照：300296 -8.55%（今低 6.49→6.63 为日内修复方向，未达本场口径）、"
         "003021 +1.24%、300561 -2.35%、002979 +1.70%。本场口径=『对成本 ≤-10% 且日内无修复』→ 仅 002474 命中，"
         "不临时放宽到 -8% 档（避免为凑动作改阈值）。"),
        ("③题材批量跳水：94 帧 3 分钟配对扫描（间隔≥150s，91 对），近 30 分钟跌≥3pp 最大簇=0 只（阈值 3 只→未触发）；"
         "全天最大簇 5 只（09:34:02：科瑞思 15.5→8.62、兰生股份 9.98→6.93、林州重机 6.91→-3.9、延华智能 3.37→0.0、良品铺子 6.18→3.09），已过 1.5 小时。"),
    ],
    "环境读数": {
        "指数": {"上证": "3689.31 -0.22%", "深成": "11487.33 -0.41%", "创业板": "2623.24 -0.57%", "科创50": "1293.25 -1.69%",
               "对比 hb-b 10:38": "上证 -0.09→-0.22、创业板 -0.45→-0.57、科创50 -1.27→-1.69 → 三项同步小幅走弱，仍未破位"},
        "昨涨停池n=55": {"中位": f"+{pool_now['median']}%", "均值": f"+{pool_now['mean']}%", "涨": pool_now["up"], "跌": pool_now["down"],
                     "≥+9.8%": pool_now["ge98"], "≤-5%": pool_now["le5"], "≤-9.8%": pool_now["le98"],
                     "对比 hb-b 10:35": "中位 +2.92→+1.72（-1.20pp）、均值 +3.42→+2.73、涨 40→36、≤-5% 4→5 → 修复动能衰减（未反转）",
                     "轨迹": "中位 09:31 +1.09 → 10:01 +1.45 → 10:21 +2.54 → 10:35 +2.92 → 11:04 +1.72",
                     "掉板": f"首帧 9 只 ≥9.8% 中现仍 ≥9.8% 7 只（掉板 2：301314 科瑞思 15.5→{dec['lost'][0][3] if len(dec['lost'])>1 else '—'}、600826 兰生股份 9.98→{dec['lost'][1][3] if len(dec['lost'])>1 else '—'}；其中 301314 为 20cm 未涨停大涨，严格口径首帧真涨停 8 只）"},
        "全市场": {"涨停": zt_n, "炸板": zb_n, "跌停": dt_n, "炸板率": dec["zb_rate"], "最高连板": dec["max_lb"],
                "最大行业": f"汽车零部 {dict(dec['hy_top']).get('汽车零部')} 只（未扩张，hb-c 观察项③→未达成扩张条件）",
                "对比 hb-b 10:38": f"涨停 43→{zt_n}、炸板 12→{zb_n}、跌停 0→{dt_n}、炸板率 0.218→{dec['zb_rate']} → 宽度微扩但封板质量小幅走弱"},
        "判断": (f"情绪=『冰点后修复日的确认正在衰减』：昨涨停池溢价中位 +2.92→+1.72（首度回落）、≤-5% 由 4 增至 5、"
               f"三大指数跌幅同步扩大、炸板率 21.8%→22.8%；但 ≥+9.8% 仍 15 只（>12 未夭折）、涨停 44 家、跌停 0、"
               f"汽车零部 12 只未扩张 → 属『修复停滞』而非『二次跳水』。结论：环境不支持任何新开仓（C=0），"
               f"只支持两类动作——规则到期清出（limitup T+1）+ 已证伪的重仓亏损止血（002474）。"),
    },
    "复盘_上一场清单核销": [
        "①hb-b 观察项①『limitup 003021@93 与 300561 是否按不留隔夜清出』→ 本场决断：清出（B 级，见 fills 前 2 条），依据为买入行明文纪律『当日价差、不留隔夜』+ T+1=今日 + 计划无腿。",
        f"②hb-b 观察项②『池内 ≥+9.8% 能否守住 12 只』→ 15 只，守住（余量 3），修复未夭折。",
        f"③hb-b 观察项③『汽车零部 12 只是否扩张』→ 仍 12 只（{dict(dec['hy_top']).get('汽车零部')}），未扩张 → 线级门不构成买入放行依据。",
        f"④hb-b 观察项④『上证能否收复零轴』→ 未收复，由 -0.09% 扩至 -0.22%（{nxt['quote']['000001']['px']}）。",
    ],
    "观察照会_非条件决断": [
        ("lhb 300296 利亚德 5500@7.25（成本 39,894.94，决断帧 6.63 -2.21%，对成本 -8.55%）：T+1 无卖出腿；本路执行口径"
         "执2=至 T+2 收盘（今日到期）。本场不动（未达 -10% 口径、日内为修复方向 6.49→6.63）。照会+预置条件见下一场。"),
        ("logic 002979 雷赛智能 300@55.86（成本 16,766.38，决断帧 56.81 +4.89%，对成本 +1.70%）：T+1 无卖出腿；卡位纯度"
         "53.02%+三季报预增 70~90% 的买入理由今日未证伪（+4.89% 为全市场强侧）。不动，留晚间计划按执2/T+2 表态。"),
        ("跨账方向冲突（hb-b 已登记，本场未收口）：002979 master 已清 / logic 仍在场（+1.70%）；300296 master 已清 / lhb 仍在场"
         "（-8.55%）——两账对同票方向相反，需 20261027 晚间计划统一，本场不越界改路。"),
        ("预案外新机会仅记录不动作：池内 ≥9.8% 15 只中 002820 桂发祥、001318 阳光乳业、605333 沪光股份为上午新封（汽车零部/食品线），"
         "均属早封/直线拉板，追买=打板价 → 记 C=0，不追、不排次。"),
        ("002474 是否该更早处置：hb-b 10:38 已照会『若 11:00 仍无腿建议按路线自订止损表态』→ 本场按口径到期+证伪执行；"
         "若用户认定 auction 路应按 T+1 开盘硬性清出，则本场仍属迟到 96 分钟，已在延误披露如实计入 -264 元机会成本。"),
    ],
    "异常与欠账": [
        "★计划漏腿（本场核心，责任在晚间计划非执行层）：limitup 20261026 计划 buys 写死『当日价差、不留隔夜』，但 sells 未给 003021@93/300561 的 T+1 腿；auction 计划 sells 未给 002474（T+1）→ 3 只共 26,786.38 元成本仓位无腿在场，靠盘中场次兜底。建议晚间计划生成加『买入日+1 必有卖出腿』强制校验（待批，本场不动工程）。",
        "hb-a 09:40 场仍无决断件（hb-b 已登记执行断链），本场未见 0940 件补写 → 断链证据链只能靠 hb-b 决断件回溯；建议 13 号 agent 心跳落最小审计件（no_action 也写）。",
        "缺件：pulse.json / warboard.json / 执行流水.jsonl / 报警_20261027.jsonl 全缺；playbook 缺件第 7 次。",
        "规格漂移：sentiment 包不存在第 7 个交易日（本场不修工程）。",
        "本场口径新增披露：『大幅回撤』触发阈值取『对成本 ≤-10% 且日内无修复』——这不是改生产参数，是本场临时口径，已写明以便事后复算与质询；若用户否决此口径，本场 002474 一笔应按越界处理（不回滚成交，仅记纪律例外）。",
    ],
    "下一场预置观察条件_非指令": [
        "13:00/14:30 场：①lhb 300296 若跌破今低 6.49 或对成本 ≤-10%（≤6.53）→ 按执2 到期+续弱清出，需写触发证据；②logic 002979 若跌回成本 55.86 下方且当日转负 → 按执2 到期表态；③池内 ≥+9.8% 家数若 <12 → 修复夭折，全场转入纯防守（禁任何买入）；④上证若失守 3685（上午低点）→ 升级为退潮确认，持仓一律只减不加；⑤汽车零部若 >12 只继续扩张且出现连板股，才允许重新评估 C 级空间（仍需计划背书）。",
    ],
    "口径": ("fill 价=决断后下一帧留档价×(1-0.10%) 向下取 2 位，毛利差未扣费用；『盘中快照』与『收盘结算』严格区分，本件不做任何收盘结算；"
           "005 席位/lhb 与本场无关的池数据不引用。"),
}

assert not os.path.exists(TARGET), "目标已存在，禁止覆盖"
with open(TARGET, "w", encoding="utf-8") as f:
    json.dump(judgment, f, ensure_ascii=False, indent=1)
print("WROTE", TARGET, os.path.getsize(TARGET))
for f_ in fills:
    print(f_["route"], f_["code"], f_["qty"], "px", f_["px"], "px_exec", f_["px_exec"],
          "pnl", f_["pnl"], f_["ret_pct"], "%")
print("汇总", judgment["fills_汇总"]["按账"], judgment["fills_汇总"]["合计"])
print("对照开盘差额", delay_total)
print("early35", early)
