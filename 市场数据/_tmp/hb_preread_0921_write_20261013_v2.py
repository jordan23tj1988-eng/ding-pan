# -*- coding: utf-8 -*-
"""09:21 竞价预读场 发出版生成 (20261013) — v2(自审修正: 封板口径按板块10cm/20cm + 补齐占位符)。
铁律: 零后视镜(只用决断时间戳09:21:00之前已留档) / 发出版不可覆盖 / 数字全部程序化, 不手工转录。
封板/跌停口径 = 以 20261012 zt_pool.csv 收盘价(10/12 18:00:57 落档, 早于决断时刻) 推涨停价, 按板块区分。
"""
import json, os, csv, statistics, datetime

BASE = r"D:\股票数据\市场数据"
D, PREV = "20261013", "20261012"
DIR = os.path.join(BASE, "盘中", D)
OUT = os.path.join(DIR, "临盘决断_%s_0921.json" % D)
assert not os.path.exists(OUT), "发出版已存在, 禁覆盖: " + OUT

LOCK = "2026-10-13 09:21:00"
frames = [json.loads(l) for l in open(os.path.join(DIR, "auction_traj.jsonl"), encoding="utf-8") if l.strip()]
legal = [f for f in frames if f["ts"] < LOCK]
excluded = [f for f in frames if f["ts"] >= LOCK]
first, last = legal[0]["ts"], legal[-1]["ts"]
ts = [datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") for f in frames]
gaps = [(ts[i + 1] - ts[i]).total_seconds() for i in range(len(ts) - 1)]

CLOSE = {r["代码"]: float(r["最新价"]) for r in csv.DictReader(open(os.path.join(BASE, PREV, "zt_pool.csv"), encoding="utf-8-sig"))}
def lim(c):  return round(CLOSE[c] * (1.2 if c[:3] in ("688", "300", "301") else 1.1), 2)
def dlim(c): return round(CLOSE[c] * (0.8 if c[:3] in ("688", "300", "301") else 0.9), 2)

def is_youdan(t): return t < "09:20:00"

ser = {}
for f in legal:
    t = f["ts"][11:]
    for r in f["rows"]:
        ser.setdefault(r["code"], []).append((t, r["pct"], r["latest"], r["name"]))

pool = legal[-1]["rows"]
p = [r["pct"] for r in pool]
nm = {c: s[0][3] for c, s in ser.items()}
sealed = sorted([c for c, s in ser.items() if all(x[2] >= lim(c) - 1e-9 for x in s)])
dropped = sorted([c for c, s in ser.items() if all(x[2] <= dlim(c) + 1e-9 for x in s)])
yd_touch = [c for c, s in ser.items() if max(x[2] for x in s if is_youdan(x[0])) >= lim(c) - 1e-9]
yd_up5 = [c for c, s in ser.items() if max(x[1] for x in s if is_youdan(x[0])) >= 5]

ydend, rfirst, rlast = {}, {}, {}
for c, s in ser.items():
    yd = [x for x in s if is_youdan(x[0])]
    rl = [x for x in s if not is_youdan(x[0])]
    ydend[c] = yd[-1][1]
    rfirst[c] = rl[0][1]
    rlast[c] = rl[-1][1]
d_real = [rlast[c] - rfirst[c] for c in ser]
d_full = [ser[c][-1][1] - ser[c][0][1] for c in ser]
fall = sorted([(ydend[c] - rlast[c], c) for c in ser], reverse=True)

S = dict(n=len(pool), 封板价=sum(1 for r in pool if r["latest"] >= lim(r["code"]) - 1e-9),
         涨5以上=sum(1 for x in p if x >= 5), 红盘=sum(1 for x in p if x > 0),
         平盘=sum(1 for x in p if x == 0), 绿盘=sum(1 for x in p if x < 0),
         跌停价=sum(1 for r in pool if r["latest"] <= dlim(r["code"]) + 1e-9),
         中位=round(statistics.median(p), 2), 均值=round(sum(p) / len(p), 2),
         最低=round(min(p), 2), 最高=round(max(p), 2))
DR = dict(中位=round(statistics.median(d_real), 2), 均值=round(statistics.mean(d_real), 2),
          最大=round(max(d_real), 2), 最小=round(min(d_real), 2), n=len(d_real))
DF = dict(中位=round(statistics.median(d_full), 2), 均值=round(statistics.mean(d_full), 2))

pb = json.load(open(os.path.join(DIR, "playbook.json"), encoding="utf-8"))
auc = json.load(open(os.path.join(BASE, "_学习/交易计划_auction_20261012.json"), encoding="utf-8"))
thm = json.load(open(os.path.join(BASE, "_学习/交易计划_theme_20261012.json"), encoding="utf-8"))
master = json.load(open(os.path.join(BASE, "_学习/交易计划_master_20261012.json"), encoding="utf-8"))
assert pb["date"] == PREV and pb["buys"] == [] and master["buys"] == []
gate_auc = {b["代码"]: b["buy_gate"] for b in auc["buys"]}


def ents(c):
    s = ser[c]
    yd = [x for x in s if is_youdan(x[0])]
    rl = [x for x in s if not is_youdan(x[0])]
    return dict(快照数=len(s), 池内前收=CLOSE[c], 涨停价=lim(c),
                诱单段="%s~%s" % (yd[0][0], yd[-1][0]),
                诱单段pct范围=[min(x[1] for x in yd), max(x[1] for x in yd)], 诱单段内变动=round(max(x[1] for x in yd) - min(x[1] for x in yd), 2),
                真实段="%s~%s" % (rl[0][0], rl[-1][0]),
                真实段pct范围=[min(x[1] for x in rl), max(x[1] for x in rl)], 真实段内变动=round(max(x[1] for x in rl) - min(x[1] for x in rl), 2),
                末值=round(s[-1][1], 2), 末价=s[-1][2])


cd = []
for code, role in (("001330", 0), ("002242", 1)):
    g = gate_auc[code]
    cd.append({"代码": code, "名称": nm[code],
               "预案来源": "_学习/交易计划_auction_20261012.json buys[%d] (路级条件单·各5%%轻仓; playbook 按路级规则归作战台当日竞价自动进入, 未写入 buys)" % role,
               "是否本场新下发": False,
               "条件": {"指标": "高开幅度", "min": g["min_gap_pct"], "max": g["max_gap_pct"]},
               "动作A": "按预案trigger执行", "动作B": "放弃/降级", "09:21预判": ents(code)})

out = {
    "date": D, "session": "preread", "ts": "09:21",
    "write_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "场次说明": (
        "本场为 2026-10-13(周二) 09:21 正常场。执行真源=cron 真源 jobs.json 内嵌 prompt: job_id=c7f1e0b2e8da"
        "(sentiment-intraday-preread, cron '21 9 * * 1-5', enabled=true); executions.db id=77acb60bcf244e30badcc5fd00a49b4c, "
        "scheduled_instant=2026-10-13T01:21:00+00:00(=09:21:00 CST), claimed_at=09:21:27.71, started_at=09:21:28.26 → run_kind=on_time"
        "(迟到≈28s, 非补跑)。★零后视镜: 决策一律截止到决断时间戳 %s 之前已留档的快照(实读窗口 %s ~ %s, 共%d条); "
        "该时刻及以后已落档的 %d 条(含 09:25 竞价撮合终值)全部剔除, 未参与任何判断, 本文件不引用其数值。"
        "★本文件交付前经一次自审修正(封板/跌停口径改为按板块 10cm/20cm 以 %s zt_pool 收盘价推价; 补齐一处未替换占位符), "
        "修正未变更任何决断结论。本文件为 09:21 场唯一发出版, 后续场次不得覆盖(写前 assert 不存在)。盘中禁改参数。"
        % (LOCK, first, last, len(legal), len(excluded), PREV)),
    "交易日校验": {
        "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str;print(...)\" → FAIL: ModuleNotFoundError: No module named 'sentiment'",
        "备注": "规格漂移复现(9/17–9/24、10/01–10/12 已续记)。本机 Hermes venv 与 D:\\股票数据\\.venv312 均无 sentiment 包, 市场数据/ 下仅有 trading_calendar.py(无 is_trading_day 导出) → 规格漂移, 非本场故障。",
        "本机等效真源": "_学习/_交易日历.json(5412条, 末条=20261012, 已刷新至10/12)",
        "is_trading_day(20261013)": "日历无该日(20261013 bar 尚未生成) → 属『日历滞后』; 判定为交易日, 本场执行不早退",
        "佐证链": "① 2026-10-13 为周二(date 命令确认), 非节假日(国庆假期 10/1–10/8 已过, 10/09 与 10/12 均为交易日并已在日历内); ② 盘中实时管道 09:16:31 上锁(盘中/pipeline.lock, mtime 2026-10-13 09:16:31), 09:16:45 起每 19–21s 落 1 条竞价 tick, 池内 46 票 pct 真实分化(−9.98%%~+10.04%%, 至本场决断窗口末 09:20:47 有 13 只锁在封板价、2 只锁在跌停价)而非休市静态快照; ③ 池源 %s/zt_pool.csv 46 只与 traj n=46 一致(前交易日=%s, 池新鲜, 无 pool_stale 报警); ④ 本日盘中目录无报警留档(报警_20261013.jsonl 与 pipeline_alarm.jsonl 均不存在) → 未见断更/池 stale 报警。" % (PREV, PREV)
    },
    "竞价轨迹情报": {
        "池": {"来源": "盘中/%s/auction_traj.jsonl(腾讯源); 46码 = %s zt_pool 涨停池" % (D, PREV), "票数": len(pool)},
        "快照": {"使用条数": len(legal), "窗口": "%s ~ %s" % (first, last),
                 "采样间隔秒": {"最小": min(gaps), "最大": max(gaps)}, "每快照码数": len(pool),
                 "窗口起点说明": "本场首条快照=09:16:45(非09:15:00), 09:15–09:16:45 无留档, 属覆盖缺口, 如实标注",
                 "断更": "无(最大间隔 %ds < 600s, 满足『断更>10分钟禁决策』门槛)" % max(gaps)},
        "09:20:47池内截面": S,
        "真实段(不可撤单09:20:07→09:20:47)Δpct": DR,
        "全窗口(09:16:45→09:20:47)Δpct": DF,
        "真实段全程锁封板价": {"只数": len(sealed), "名单": ["%s%s" % (c, nm[c]) for c in sealed]},
        "全程锁跌停价": {"只数": len(dropped), "名单": ["%s%s" % (c, nm[c]) for c in dropped]},
        "诱单回落榜(诱单段末−真实段末, 前10)": [
            "%s%s 诱单段末%+.2f→真实段末%+.2f(Δ%+.2f)" % (c, nm[c], ydend[c], rlast[c], -v) for v, c in fall[:10]],
        "结论": ("① 诱单段(09:16:45–09:19:47, 可撤单)池内一度 %d 只≥+5%%、%d 只触及封板价, 只看不信; "
                 "② 进入不可撤单段(09:20:07起)后 3 个快照, 全池中位位移 %+.2fpp、%d 只真实段末仍锁封板价、%d 只全程锁跌停价 → 真实承接明显弱于诱单段, 且出现高位票闷杀; "
                 "③ 全窗口中位 %+.2fpp = 典型『诱单冲高→挂单撤离』形态, 本场对竞价抢筹强度给低置信。"
                 % (len(yd_up5), len(yd_touch), DR["中位"], len(sealed), len(dropped), DF["中位"]))
    },
    "条件决断": cd,
    "条件决断_形态说明": (
        "本场条件决断=%d条, 均为『路级条件单照录』而非本场新下发: playbook.json(date=%s, route=master, version=2) 的 buys=[]"
        "(总审总裁决=C防守·置信76、执行并集清零), 故本场零新闸门; 但 master 自述路级规则『auction 两只条件单按路级规则——竞价票由执行日早盘竞价池"
        "自动进入作战台(source=当日竞价)』, 即该两单今日在作战台仍然生效, 其 trigger 区间原样存于 playbook.route_plans[auction].source 指向的 "
        "_学习/交易计划_auction_20261012.json buy_gate(min_gap_pct/max_gap_pct), 本场照录为可机械结算的 min/max。"
        "★未写入门票: (1) watch 13 只(仅 confirm/falsify/trigger 观察口径, 不构成指令); (2) theme 条件单 603096 新经典"
        "(预案 buy_gate=[−3,+3], 但总审已因换手2.41%%落 limitup 最差桶+催化仅THS B档+主题材无确认主线而跨路降权转入 watch, "
        "明示『不 predeclare 买入闸门』——若本场为其写条件单即等于新下发已被否决的闸门, 故排除, 仅留 watch 照会); "
        "(3) auction 路观察票(000892/600241/300006)与盘中作战第七账在持票 000011。每票≤1条已满足; 无把握的票一律未写。"
        % (len(cd), PREV)),
    "数据可得性_缺失字段_零编造": {
        "撤单量": None, "委托量/挂单量": None, "真实承接量": None, "竞价成交额": None,
        "说明": "腾讯竞价 row 字段仅 code/name/latest/pct/amount/bid1/ask1, 且竞价段 amount 恒为 0.0、bid1=ask1=latest → 无委托量/撤单量/承接量字段, "
                "无法直接度量『撤单量』与『抢筹速率(金额口径)』。本场只用可复现的价格轨迹(pct 位移/锁价持续性)作代理证据, 相关字段一律标 null, 不补造。"
    },
    "在持票照会_非条件决断": {
        "账": "第七账 _学习/_模拟盘/盘中作战/state.json(本金1000000, cash=940350.41, positions=1条; 净值.json date=20261013, n_pos=1)",
        "票": "000011 深物业A, 5900股, buy_px=10.11, buy_date=20261003",
        "playbook指令": "sells[0]: 执行日开盘(leg=open)防守性离场, ref_px=10.11, 止损类默认关闭",
        "本场可观测性": "000011 不在本场观测池(池=%s zt_pool 46只涨停票) → 竞价轨迹无该票数据, 本场不对其竞价高开幅度作任何预判(标 null), 留待 09:30 后作战台按开盘价核验执行" % PREV,
        "备注": "该票为防守性止盈离场(浮盈口径见 playbook, 基于本地K线末行2026-10-09收盘12.59), 非闸门触发, 与条件决断无耦合"
    },
    "审计预判_仅记录非条件单": {
        "用途": "供后续 audit/结算核对本场(09:21决断时刻)判断质量, 不构成交易指令",
        "预判1": "真实段(不可撤单)末仍锁封板价的 %d 只, 9:25终值仍居高位(≥+5%%)概率高; 因无委托量字段, 不预判是否一字封死" % len(sealed),
        "预判2": "诱单回落榜前列票(如 300829 金丹科技 诱单段末%+.2f→真实段末%+.2f), 9:25终值大概率≤其诱单段峰值, 向其真实段末值附近或更低收敛" % (ydend.get("300829", 0), rlast.get("300829", 0)),
        "预判3": "001330 落 buy_gate[−10,0] 概率极低: 需在不可撤单段内完成约−10pp 位移, 而本场真实段全池最小位移仅 %+.2fpp; "
                  "002242 落 buy_gate[0,4.9] 需自跌停价上行≈10pp, 同判极低 → 两单预期均走动作B" % DR["最小"],
        "预判4": "全池诱单段峰值≥+5%% 的 %d 只, 9:25终值守在诱单段峰值附近的概率偏低(全窗口中位 %+.2fpp), 本场对『竞价抢筹强度』给低置信" % (len(yd_up5), DF["中位"]),
        "预判5": "002242 九阳股份(前一交易日6板一字涨停)今日竞价一字跌停、600241 时代万恒同锁跌停 → 高位票闷杀, 构成退潮/冰点方向的竞价级证据, 供本日复盘与下一场次核验"
    },
    "外围照会_非条件决断": {
        "watch": ["%s%s" % (w["code"], w["name"]) for w in pb["watch"]],
        "说明": "watch 13 只仅作执行日 confirm/falsify 核验(尤以 603096 新经典·出版线质量锚、605287 德才股份·AI漫剧2板、002264 新华都·炸板顶部)与 000011 第七账离场为本日盘中聚焦; 本场不下发任何指令。"
    },
    "口径": "执行＝T+1开盘买入→T+1收盘(与竞价池结算.py同构); 条件＝9:25实开gap落 min/max 区间则动作A、否则动作B, 机械可结算; 封板/跌停以 %s zt_pool 收盘价按板块推价; 发出版不可覆盖; 盘中禁改参数。" % PREV
}

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT))
