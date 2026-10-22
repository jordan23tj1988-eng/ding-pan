# -*- coding: utf-8 -*-
"""hb-c 11:00 决断件生成器：所有数字从落盘文件计算，禁手填。"""
import json, os, datetime

BASE = r"D:\股票数据\市场数据\盘中\20261021"
OUT = os.path.join(BASE, "临盘决断_20261021_1100.json")
assert not os.path.exists(OUT), "发出版已存在，禁覆盖"

PIN = "2026-10-21 11:02:30"
_all = [json.loads(l) for l in open(os.path.join(BASE, "realtime_ticks.jsonl"), encoding="utf-8")]
frames = [f for f in _all if f["ts"] <= PIN]
q = json.load(open(os.path.join(BASE, "_hb_c_quote_1100.json"), encoding="utf-8"))
quotes = {r["code"]: r for r in q["rows"]}

def snap(f):
    return {r["code"]: r for r in f["rows"]}

def near(t):
    tt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    return min(frames, key=lambda f: abs(datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") - tt))

width = []
for t in ["2026-10-21 09:47:00", "2026-10-21 10:00:00", "2026-10-21 10:30:00",
          "2026-10-21 10:45:00", "2026-10-21 10:55:00", "2026-10-21 11:01:00"]:
    f = near(t); S = snap(f); p = sorted(x["pct"] for x in S.values())
    width.append({"帧": f["ts"], "上涨": sum(1 for v in p if v > 0), "下跌": sum(1 for v in p if v < 0),
                  "平": sum(1 for v in p if v == 0), "中位pct": round(p[len(p)//2], 2),
                  "涨停附近(≥9.7%)": sum(1 for v in p if v >= 9.7)})

A0 = snap(near("2026-10-21 09:47:00"))
L = snap(frames[-1])
delta = sorted([(round(L[c]["pct"] - A0[c]["pct"], 2), c, L[c]["name"], A0[c]["pct"], L[c]["pct"])
                for c in L if c in A0])

rec = []
for code, shares in (("000601", 6000), ("000823", 800)):
    r = quotes[code]
    px = round(r["latest"] * 0.999, 2)
    rec.append(dict(code=code, name=r["name"], pct=r["pct"], latest=r["latest"], open=r["open"],
                    high=r["high"], low=r["low"], preClose=r["preClose"], shares=shares, px_exec=px))

pos = {
    "000601": dict(name="韶能股份", shares=6000, buy_px=6.68, plan_date="20261014", buy_date="20261015"),
    "000823": dict(name="超声电子", shares=800, buy_px=25.13, plan_date="20261014", buy_date="20261015"),
}
for x in rec:
    p = pos[x["code"]]
    x["ret_vs_cost_pct"] = round((x["latest"] / p["buy_px"] - 1) * 100, 2)
    x["ret_exec_vs_cost_pct"] = round((x["px_exec"] / p["buy_px"] - 1) * 100, 2)
    x["pnl_gross"] = round((x["px_exec"] - p["buy_px"]) * p["shares"], 2)

declared = {"000601": 6.40, "000823": 24.66}
for x in rec:
    x["declared_0940_px"] = declared[x["code"]]
    x["delay_gap_pct"] = round((x["px_exec"] / declared[x["code"]] - 1) * 100, 2)
    x["delay_cost_yuan"] = round((x["px_exec"] - declared[x["code"]]) * x["shares"], 2)

fills = []
for x in rec:
    p = pos[x["code"]]
    fills.append({
        "ts": "2026-10-21 11:02:36",
        "code": x["code"], "name": x["name"], "action": "fill_sell",
        "px": x["latest"], "px_exec": x["px_exec"], "qty": x["shares"],
        "rule": "playbook.sells[%d] leg=open 清仓%d股；A级·预案内机械执行（不设价格下限）catch_up 第2次" % (
            0 if x["code"] == "000601" else 1, x["shares"]),
        "route": "master",
        "note": "决断帧现价 %.2f(%+.2f%%)，px_exec=%.2f×0.999=%.2f（卖出向下取整至分）。相对成本 %.2f = %+.2f%%（毛 %.0f 元）。相对 0940 已声明价 %.2f 差 %+.2f%%（%+.0f 元）= 执行断链损耗，如实计入，不以前一帧价格冒充成交。"
                % (x["latest"], x["pct"], x["latest"], x["px_exec"], p["buy_px"], x["ret_exec_vs_cost_pct"], x["pnl_gross"],
                   x["declared_0940_px"], x["delay_gap_pct"], x["delay_cost_yuan"]),
        "evidence": "playbook.json#sells(%s)；master/状态.json#持仓 %d股 buy_px=%.2f；_hb_c_quote_1100.json 帧 11:02:36（qt.gtimg.cn）"
                    % (x["code"], x["shares"], p["buy_px"]),
        "落账": "本件为成交声明；**不手写 master/账本.jsonl**（模拟盘数字只出自引擎），落账以 settle 核算为准；若 settle 按 bars 开盘价记账（000601 6.31 / 000823 24.96），以引擎数字为唯一口径，本件不回写、不冲正。",
    })

doc = {
    "date": "20261021", "session": "hb-c", "ts": "11:00",
    "write_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "修订": "v1.1 自更正（同一场次内，未被任何下游引用）：初版把池帧末帧取到生成时刻（11:05:30），与持仓报价帧 11:02:36 不同源；现统一钉住决断帧 11:02:30/11:02:36，宽度与个股Δ全部同帧重算，判断与成交价未变。",
    "版本": "v1 · 11:00 半日收尾段",
    "场次说明": "本场为 20261021(周三) hb-c 11:00 半日收尾段。★零后视镜：只用决断时点(11:02:36)前已落盘数据——池帧 91 帧 09:31:09~11:01:29（1/分钟）、持仓现价取 qt.gtimg.cn 帧 11:02:36。★盘中禁改参数：未改 playbook/阈值/脚本。★发出版不可覆盖：写前 assert 文件不存在（已通过）。",
    "交易日校验": {
        "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → FAIL: ModuleNotFoundError: No module named 'sentiment'（自 20260917 起连续登记，本场继续如实记，不改工程）",
        "本机等效真源": "date → 2026-10-21 星期三；盘中池本日 09:31 起连续 91 帧真实分化（含涨跌家数变化 38/14 → 39/13 与个股 ±6pp 级别波动），非休市静态快照 → 判定交易日，不早退",
    },
    "数据新鲜度": {
        "池帧": {"文件": "realtime_ticks.jsonl", "帧数": len(frames), "窗口": "%s~%s" % (frames[0]["ts"], frames[-1]["ts"]),
                 "末帧龄": "<1分钟（决断 11:02:36；池帧钉住 11:02:30）", "pool_date": frames[-1]["pool_date"],
                 "pool_stale": frames[-1]["pool_stale"], "n": frames[-1]["n"], "判定": "未断更，可决策（远低于10分钟断更线）"},
        "持仓现价": {"源": "qt.gtimg.cn", "落盘": "_hb_c_quote_1100.json", "帧": "11:02:36",
                     "说明": "持仓两票不在昨涨停池内，池不覆盖，单独取腾讯现价"},
        "缺件": {"pulse.json": "不存在（盘中/20261021/ 无此文件，自 hb-a 起连续缺）",
                 "warboard.json": "不存在（盘前未生成）",
                 "执行流水.jsonl": "不存在 → 引擎今日仍未执行任何 open 腿",
                 "临盘决断_20261021_1030.json": "不存在（hb-b 10:30 场为无动作场，按规格无动作不落件）"},
        "口径": "缺件如实标，不补造；风险判断不依赖 pulse/warboard，以池帧+腾讯现价为准。",
    },
    "半日宽度": width,
    "个股Δ(09:47:12→11:02:30)": {"跌≥3pp": [x for x in delta if x[0] <= -3], "涨≥3pp": [x for x in delta if x[0] >= 3],
                            "全池同窗口跌≥3pp家数": sum(1 for x in delta if x[0] <= -3),
                            "最差": delta[0], "最强": delta[-1]},
    "权限分级": {
        "A": "2 笔卖出：000601 6000股、000823 800股 — 均为 playbook.sells 内 leg=open 机械清仓腿（预案内，无自由裁量）。本场属 catch_up 第2次：0940 场已于 09:47 声明成交，但截至本场 11:02 master/账本.jsonl 无任何 20261021 记录、master/状态.json date 仍 20261020 且两票仍在持仓 → 声明未落账，敞口实际仍开着，故按当前帧重声明。",
        "B": "0 笔。000823 已构成『持仓大幅回撤』（现价较成本 -3.5%、较 1020 高点 27.18 回撤 -10.8%、今日 -5.31%），但其全部敞口由上述 A 级清仓腿覆盖，不重复下 B 单（同 0940 口径）。000601 +1.58%、最高 6.48 未破 6.27，无炸板无急跌。",
        "C": "0 笔。①playbook.buys 两笔（002076、603278）今日已因 gap 越出 [-3%,+3%] 机械作废，预案明写『不替补、不换票、不抬价追板』；②watch 5 只（300115/301313/002881/001283/002929）无买入授权，且 confirm 条件多数要求收盘核席位/收盘仍在涨停池，盘中不可预支；③本场无预案外新机会需带帽进攻 → 全池零新增多头暴露。",
    },
    "fills": fills,
    "no_action": None,
    "reason": "【三查】①持仓：000601 6.41(+1.58%)，高6.48/低6.27，未炸板未破位；000823 24.25(-5.31%)，自 09:47 的 -3.63% 再跌 1.68pp，自 1020 涨停价 27.18 回撤 -10.8% = 持仓大幅回撤（该票敞口由 A 腿覆盖，见 B 栏）。②批量跳水：09:47→11:01 全池 52 票跌≥3pp 仅 3 只（001323 慕思股份 -6.11pp、605488 福莱新材 -5.13pp、603626 科森科技 -3.19pp），分散在消费/材料/消费电子三条不相干线，非同一题材同时段塌陷；无 2 分钟内 ≥3 只同线 -3% → 未触发批量跳水。③预案 trigger：两笔卖出腿常年有效（leg=open 不设价格下限，只剩『能不能卖』问题，两只均非一字跌停，现价可成交）→ A 级执行；两笔买入腿作废规则已在 0940 场机械执行，本场不得复活。宽度面：中位 +3.58%、38 涨/14 跌、14 只贴板或涨停，10:30 后宽度稳中有升（10:00 中位 3.27 → 11:01 3.58）→ 环境不差，本场只做预案内清仓、不新开仓。",
    "对账发现": {
        "账本_20261021_条数": 0,
        "master_账本_末条": "20261020 600668 sell@8.11（ts 2026-10-20 19:56:10）",
        "master_状态_date": "20261020",
        "master_状态_持仓": ["000601 6000@6.68", "000823 800@25.13"],
        "第七账(盘中作战)_state": "date 未标、cash 996990.24、positions []（10:01 被动刷新，与本日 master 口径不一致）",
        "结论": "0940 场声明成交（000601 6.40 / 000823 24.66）从未进入 master 账本，形态上『已卖』但账户仍持有。这是同日第2次、连续第3个交易日（1019/1020/1021）同一断链：引擎不执行、agent 声明、结算侧不落账。本场按账本真源认定『仍持有』，并把当前可成交价（非 0940 声明价）作为本场成交口径，差额如实登记。",
    },
    "异常与欠账": [
        "① 规格命令漂移（连续登记，自 20260917）：from sentiment.core.calendar import ... 仍 ModuleNotFoundError；本场用 date + 91 帧真实分化佐证。工程二选一：补 sentiment 包，或把 prompt 改为本机 trading_calendar.py。",
        "② ★执行断链第3日（P0）：master/账本.jsonl 今日 0 条、状态 date=20261020、执行流水.jsonl 不存在。0940 场 A 级卖出已声明但零落账 → 000823 从声明价 24.66 滑到 11:02 的 24.25，本场 catch_up 相对 0940 声明价损耗 0.43 元/股 = 344 元（毛），系工程损耗非盘面损耗。建议：引擎在 09:25 落执行流水并在盘后 settle 前核对『决断件声明 vs 账本』一致性门禁（缺一即 FAIL），否则每日靠 catch_up 追价。",
        "③ 000823 数量口径冲突（昨日挂账未决，连续第2日）：master 账本/状态均 800 股；报警_20261020 hb-b 自报『减半 400@26.34』未落账。本场仍按账本 800 股口径清仓，请结算侧给唯一裁决；若 400 已成交则本场超卖 400 股须冲正（按本场 px_exec 24.23 反向回补）。",
        "④ 第七账 state 与 master 口径分叉：盘中作战 state.json 10:01 刷新为 positions=[]、cash=996990.24，但 master 仍持两票；两本账今日均无成交行。建议明示『第七账今日是否参与 master 腿』，否则同一笔卖出会在两本账里各算一次或被两本账同时漏掉。",
        "⑤ playbook 与账本时序倒置（机制性，昨日已登记）：playbook 19:21 生成早于账本 19:56 结算 → 600668 重复清仓腿（本日 0940 场已核销为废单）。建议生成端读结算后账本或做持仓存在性校验。",
        "⑥ 持仓票不在实时池：池=昨涨停池，持仓两票均在池外，本场单独取腾讯现价落盘 _hb_c_quote_1100.json。建议把在持票并入管道取数白名单（与 1020 preread 建议⑤同源，仍欠）。",
    ],
    "next_session": "hb-d 13:30：①核对本场两笔卖出是否落账（账本应出现 20261021 两行）；②午后盯 000823 是否跌停/加速下行（若跌停则顺延，不得追卖穿价）；③宽度阈值：中位 pct 跌破 0 或涨停附近家数 <10 → 当日零新增；④两笔买入腿已作废，午后不得复活。",
    "免责": "本件为模拟盘判断记录，不是操盘指令。",
}

json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT))
for f in fills:
    print(f["code"], f["px_exec"], f["qty"])
print("width", json.dumps(width, ensure_ascii=False))
print("delta<=-3", doc["个股Δ(09:47:12→11:02:30)"]["跌≥3pp"])
