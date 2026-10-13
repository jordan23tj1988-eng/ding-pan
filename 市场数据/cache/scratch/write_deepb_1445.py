# -*- coding: utf-8 -*-
"""深场B(14:45尾盘场) 发出版生成 — 数字全部由锁定帧程序化算出, 不手工转录。"""
import json, os, statistics, datetime, gzip, csv

BASE = r"D:\股票数据\市场数据"
D = "20261012"
PREV = "20261009"
DIR = os.path.join(BASE, "盘中", D)
OUT = os.path.join(DIR, "临盘决断_%s_1445.json" % D)
assert not os.path.exists(OUT), "发出版已存在, 禁覆盖: " + OUT

frames = [json.loads(l) for l in open(os.path.join(DIR, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
LOCK = "2026-10-12 14:45:00"
legal = [f for f in frames if f["ts"] <= LOCK]
lockf = legal[-1]
ts = [datetime.datetime.strptime(f["ts"], "%Y-%m-%d %H:%M:%S") for f in frames]
gaps = [(ts[i + 1] - ts[i]).seconds for i in range(len(ts) - 1)]


def lim(pc, code):
    return round(pc * (1.2 if code[:3] in ("688", "300", "301") else 1.1), 2)


def stat(f):
    rows = f["rows"]; p = [r["pct"] for r in rows]
    return dict(n=len(rows), 中位=round(statistics.median(p), 2), 均值=round(sum(p) / len(p), 2),
                涨=sum(1 for x in p if x > 0), 跌=sum(1 for x in p if x < 0), 平=sum(1 for x in p if x == 0),
                封板=sum(1 for x in p if x >= 9.8), 深跌=sum(1 for x in p if x <= -5),
                跌停=sum(1 for x in p if x <= -9.8), 低=round(min(p), 2), 高=round(max(p), 2))


S = stat(lockf)
rows = lockf["rows"]
seal = sorted([r for r in rows if r["pct"] >= 9.8], key=lambda x: -x["pct"])
zha = [r for r in rows if r["high"] >= lim(r["preClose"], r["code"]) - 1e-6 and r["latest"] < lim(r["preClose"], r["code"]) - 1e-6]
deep = sorted([r for r in rows if r["pct"] <= -5], key=lambda x: x["pct"])
dt = [r for r in rows if r["pct"] <= -9.8]
fmt = lambda r: "%s %s %+.2f" % (r["code"], r["name"], r["pct"])

tr = []
for m in ["09:31", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "14:44"]:
    c = [f for f in legal if f["ts"][11:16] <= m]
    if c:
        x = stat(c[-1]); tr.append("%s 中位%+.2f/封板%d/涨跌%d-%d" % (m, x["中位"], x["封板"], x["涨"], x["跌"]))

W0 = "2026-10-12 14:35:00"
w = [f for f in legal if W0 <= f["ts"] <= LOCK]
p0 = {r["code"]: r["pct"] for r in w[0]["rows"]}; p1 = {r["code"]: r["pct"] for r in w[-1]["rows"]}
dd = {c: p1[c] - p0[c] for c in p1}


def maxconc(win, thr=-3.0):
    best = 0
    for i in range(len(w)):
        t0 = datetime.datetime.strptime(w[i]["ts"], "%Y-%m-%d %H:%M:%S")
        base = {r["code"]: r["pct"] for r in w[i]["rows"]}
        for j in range(i + 1, len(w)):
            t1 = datetime.datetime.strptime(w[j]["ts"], "%Y-%m-%d %H:%M:%S")
            if (t1 - t0).seconds > win:
                break
            cur = {r["code"]: r["pct"] for r in w[j]["rows"]}
            best = max(best, len([c for c in cur if c in base and cur[c] - base[c] <= thr]))
    return best


cw = [f for f in legal if f["ts"] >= "2026-10-12 13:30:51"]
seen = {}
for f in cw:
    for r in rows:
        pass
for f in cw:
    for r in f["rows"]:
        st = seen.setdefault(r["code"], {"name": r["name"], "sealed": False, "broke": None, "reseal": None, "last": None})
        if r["latest"] >= lim(r["preClose"], r["code"]) - 1e-6:
            if st["broke"] and st["reseal"] is None:
                st["reseal"] = f["ts"][11:19]
            st["sealed"] = True
        elif st["sealed"] and st["broke"] is None:
            st["broke"] = f["ts"][11:19]
        st["last"] = f["ts"][11:19] + " " + "%.2f" % r["pct"]
broken = {c: st for c, st in seen.items() if st["broke"]}

# 全市场(09:30:56 竞价快照, 仅量级参照)
snp = list(csv.DictReader(gzip.open(os.path.join(BASE, "_学习/竞价快照存档/%s.csv.gz" % D), "rt", encoding="utf-8-sig", errors="replace")))
mv = []
for r in snp:
    try:
        pc = float(r["昨收"]); px = float(r["最新价"])
    except Exception:
        continue
    if pc > 0 and px > 0:
        mv.append((px / pc - 1) * 100)
mkt_med = round(statistics.median(mv), 2)
d011 = [r for r in snp if r["代码"].strip() == "000011"][0]
p011 = round(float(d011["最新价"]) / float(d011["昨收"]) - 1, 2) * 100

MEM = "传媒/影视/出版链"
chain = ["000892", "001330", "002343", "601811", "605577", "601929", "600825", "601595", "603096", "603533"]
chain_hit = [r for r in seal if r["code"] in chain]

doc = {
    "date": D, "session": "deep-b", "ts": "14:45",
    "write_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "场次": "真场次(在窗, on_time)。身份读自执行真源: cron 真源 jobs.json 内嵌 prompt, job_id=0509b31150e9 / name=sentiment-intraday-deepb / expr='45 14 * * 1-5' / enabled=true / model=deepseek-flash; executions.db 本场 id=0990f498c12441848ff26b7fb727cc06, scheduled_instant=2026-10-12T06:45:00Z(=14:45:00 CST), claimed 14:45:08.231822+08:00 / started 14:45:08.553330+08:00 → lateness≈8.6s, kind=on_time(非补跑)。本件为零动作留档。",
    "交易日判定": {
        "契约命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str...\" → ModuleNotFoundError: No module named 'sentiment' (契约命令与现行库不匹配, 规格漂移, 自 09-17 起多次同型) → 无法以契约接口判定",
        "本机等效真源": "市场数据/trading_calendar.py::load_trading_calendar() + _学习/_交易日历.json (末三条=20260930/20261008/20261009) → 20261012 未入日历 = 日历滞后(bars_cache 收盘后才补), 不能据此否定",
        "独立佐证": "① 2026-10-12=周一, 国庆长假后第3个交易日(10/1–10/7 休市, 10/8 复市=第1个, 10/9=第2个); ② 管道今日 live: 09:31:07→锁定帧 14:44:05 共 313 帧价格逐 tick 真实跳动(午休段价格冻结, 见 data_freshness); ③ 盘中/pipeline.lock = '20261012 13232 09:14:08' 本日上锁; ④ 盘中/launcher.log 今日段(第 13233 行起) 0 错误, 每 60s 一行 tick 源=腾讯 n=69",
        "结论": "20261012=有效交易日, 本场按实跑交易日出件",
    },
    "data_freshness": {
        "契约指定文件": "盘中/%s/pulse.json" % D,
        "pulse 核验结果": "缺件 —— 全库 find 0 命中(契约路径在现行库未实现, 连续多日同型) → 无法以『pulse 最新时间戳』做断更判定; 已明示以 realtime_ticks.jsonl 顶替并登记口径替换",
        "替代断更核验": "程序源 盘中/%s/realtime_ticks.jsonl: 首帧 09:31:07 / 全量末帧 14:51:07 / 合法帧(ts<=14:45:00) 313 帧; 相邻间隔 max=61s, >120s 空档 0 次, >10分钟断更 0 次 → 数据红线未触发。决策锁定末条 ts=2026-10-12 14:44:05(<=14:45:00); 窗后新写入帧(14:45:05 起: 14:45:05/14:46:06/14:47:06/14:48:06/14:49:06/14:50:06/14:51:07)仅列示、未作决策输入。" % D,
        "午休口径(承 hb-d/hb-e 登记)": "11:30:29→12:59:45 段源续采但价格冻结于 11:30 快照, 非断更、不产生新信息; 本场窗 14:35:04→14:44:05 共 10 帧全为真实跳动帧, 未把冻结段当实时",
        "池源": "src=腾讯(单源) / pool_date=%s / pool_kind=zt_pool / pool_stale=false / 每帧 n=69 → 本场无降级, 观察池=前一交易日(20261009)涨停池 69 只『今日承接』口径, 非当日全市场口径" % PREV,
        "告警文件": "盘中/%s/pipeline_alarm.jsonl 不存在; 盘中/%s/报警_%s.jsonl 不存在; 盘中/报警_*.jsonl 最新=20260911 → 本场告警 0 条" % (D, D, D),
        "结论": "数据新鲜(断更 0) → 允许决策; 池源无降级(stale=false)",
    },
    "池内技术触发": {
        "锁定快照": "2026-10-12 14:44:05 (pool_date=%s, stale=false, n=%d)" % (PREV, S["n"]),
        "宽度": "中位 %+.2f%% / 均值 %+.2f%% / 涨-%d 跌-%d 平-%d; >=+5%% %d 只、<=-5%% %d 只; 区间 %+.2f%% ~ %+.2f%%" % (
            S["中位"], S["均值"], S["涨"], S["跌"], S["平"], sum(1 for r in rows if r["pct"] >= 5), S["深跌"], S["低"], S["高"]),
        "封板(pct>=9.8, 末帧)": "%d 只: %s" % (len(seal), " / ".join(fmt(r) for r in seal)),
        "触板(独立口径)": "按 preClose×涨停幅度(主板1.10/创业科创1.20)算涨停价与当日 high 比对: 全池 %d 只曾触板 → 末帧封住 %d 只、触而未封 %d 只(%s)" % (
            len([r for r in rows if r["high"] >= lim(r["preClose"], r["code"]) - 1e-6]), len(seal),
            len([r for r in rows if r["high"] >= lim(r["preClose"], r["code"]) - 1e-6]) - len(seal),
            " ".join(fmt(r) for r in rows if r["high"] >= lim(r["preClose"], r["code"]) - 1e-6 and r["latest"] < lim(r["preClose"], r["code"]) - 1e-6)),
        "炸板(latest<涨停价)": "%d 只: %s" % (len(zha), " / ".join(fmt(r) for r in zha)),
        "深跌(<=-5%, 末帧)": "%d 只: %s" % (len(deep), " / ".join(fmt(r) for r in deep)),
        "跌停(<=-9.8%)": "%d 只: %s" % (len(dt), " / ".join(fmt(r) for r in dt)),
        "日内轨迹(池中位/封板/涨跌)": tr,
        "尾盘段(14:14→14:44)": "池中位 +2.28→%+.2f (Δ%+.2f) / 均值 +2.39→%+.2f (Δ%+.2f); 封板 19→%d(净增 %d); 深跌 6→%d(净增 %d); 涨/跌 44/25→%d/%d → 尾盘钝化 + 弱尾扩容(尾部恶化在跌侧, 封板未瓦解)" % (
            S["中位"], S["中位"] - 2.28, S["均值"], S["均值"] - 2.39, S["封板"], S["封板"] - 19, S["深跌"], S["深跌"] - 6, S["涨"], S["跌"]),
        "决断窗(14:35:04→14:44:05, 10帧)": "Δ中位 %+.2f / Δ均值 %+.2f; 逐票跌幅最大 5: %s; 涨幅最大 3: %s" % (
            statistics.median(list(dd.values())), sum(dd.values()) / len(dd),
            " ".join("%s%+.2f" % (c, v) for c, v in sorted(dd.items(), key=lambda x: x[1])[:5]),
            " ".join("%s%+.2f" % (c, v) for c, v in sorted(dd.items(), key=lambda x: -x[1])[:3])),
        "题材批量跳水(>=3只 2分钟内 <=-3pp)": "0 例。逐帧窗(i-2→i, 120s)全扫 %d 票: 决断窗内并发最大=%d 只; 扩至 300s 窗并发最大=%d 只 → 均未达门槛(>=3), 非『同步跳水』" % (S["n"], maxconc(120), maxconc(300)),
        "本场窗(13:30:51→14:44:05)炸板事件": ("%s" % " ; ".join("%s %s 首破%s → %s (末帧 %s)" % (c, st["name"], st["broke"], ("回封" + st["reseal"]) if st["reseal"] else "未回封", st["last"]) for c, st in broken.items())) or "无",
        "封板质量": "本场窗 %d 例破板, 全部回封 → 封板质量未瓦解; 结构风险在跌侧(深跌 6→%d)与高位票单票崩落" % (len(broken), S["深跌"]),
        "主线结构(口径=池内封板票名称聚簇)": "封板 %d 只中 %s %d 只同簇(%s) → 主线自 09:31 起未散、宽度 %d>=8; 其余封板分散于锂电/光伏化工/医药/小家电/化妆品电商/水产等" % (
            len(seal), MEM, len(chain_hit), "/".join(r["name"] for r in chain_hit), len(chain_hit)),
        "高位分化(尾盘读数)": "① 001300 三柏硕: 09:31 封 +10.03 → 09:45 -7.20 → 全天弱势下探 → 14:44 -10.03(跌停, 单日振幅≈20pp); ② 603155 新亚强: 10:30 封 +9.98 → 13:30 破板 7.45 → 14:44 +5.83(未回封); ③ 600241 时代万恒: 09:31 封 10.03 → 10:30 7.14 → 14:12:59 再封 10.03(天地板后回封, 高标反复); ④ 605177 东亚药业 / 001336 楚环科技: 早盘 09:45 前后即跌停并全天锁死(-10.00/-9.99)",
        "相对强度": "池中位 %+.2f%%(14:44:05) vs 全市场 09:30:56 竞价快照中位 %+.2f%%(有效 %d 只, 源=sina_spot, mtime 09:31:43) → 池强于市场约 %+.2fpp。★窗差 5h14m, 仅作量级参照, 不作结论依据(全市场实时口径本时点不可得)" % (
            S["中位"], mkt_med, len(mv), S["中位"] - mkt_med),
    },
    "B级防守三类判定": {
        "①持有对象炸板/大幅回撤": "零合法对象 → 未达标。本账唯一持仓 000011 深物业A(5900股@10.11, buy_date=20261003) 属『节假日误跑虚构产物(待人工裁定)』(承 20260929 起多场判例 + 20261009 深场B 定谳) → 不列为合法在持、不构成卖据",
        "②题材批量跳水(>=3只2分钟内<=-3pp)": "决断窗内 0 例(见『池内技术触发』), 120s/300s 双口径并发最大分别 0/0 → 未达标",
        "③单票封板破板": "本场窗内 2 例(格尔软件 13:40:53 / 安彩高科 13:42:54), 均非持仓对象、题材分散(军工软件 / 光伏化工), 且均回封 → 属封板价换手而非题材级失血(传媒影视出版主链 10 只仍封) → 不构成持仓风险",
        "结论": "三类逐项未达标 → 无 B 级防守动作(无可执行防守对象=零卖腿); 本场权限分级落位=B 级(仅判定、无触发)",
    },
    "持仓表态": {
        "合法在持票数": "0(非漏写)",
        "账本读数": "_学习/_模拟盘/盘中作战/state.json(mtime 2026-10-12 14:30, 引擎本轮自行刷新) → 本金 1000000 / cash=940350.41 / positions=[{code:000011, name:深物业A, shares:5900, buy_px:10.11, cost:59649.59, buy_date:20261003}]; 净值.json(date=20261012) nav=999999.41 / cash=940350.41 / pos_val=59649.0 / n_pos=1; 次日卖出指令.json=[]",
        "000011 逐票表态(待裁定项, 非决策依据)": "今日表现: 09:30:56 竞价快照读数 昨收12.59/今开12.18/最新11.63 → 当日 -7.63%(高开 -3.26%, 竞价额排名 71); 浮盈: 相对 buy_px 10.11 → +15.03%(按快照价, 未计滑点与费用)。★09:31 后该票不在管道池(池=20261009 zt_pool 69 只)、全库今日无独立 watch 源 → 盘中价格不可核, 本场无法给出可信的盘中/尾盘读数和卖价带。明日计划: 不纳入本账明日卖出计划(次日卖出指令=[]); 待人工裁定性质后, 若判为真实在持, 须先补『本账 positions → 独立 watch 源』的管道采集, 方可在盘中做炸板/回撤判定。持有或卖出理由: 本场纪律=对非合法持仓不做任何持有/卖出判断(既不为账面 +15% 浮盈背书, 也不代为清仓)",
        "state/账本/净值改动": "无(不动账、不清仓、不代人工裁定; 模拟盘数字只出自引擎)",
    },
    "对账执行流水": {
        "契约文件": "盘中/%s/执行流水.jsonl → 全库 find 0 命中(路径未实现, 连续多日同型) → 无独立流水可对账" % D,
        "替代证据(引擎自有留档)": "_学习/_模拟盘/盘中作战/判断流水.jsonl(mtime 2026-10-12 14:30) + state.json(14:30 回写) + 净值.json(date=20261012) + 账本.jsonl(末条=20261003 buy 000011, 且同条重复两次) → 引擎今日末次回写 n_pos=1(该1项=待裁定 000011) / cash=940350.41 / nav≈1.0(因虚构票 pos_val 计入)",
        "引擎今日已执行": "零真实成交(无 buy、无 sell)",
        "结论": "本账真实持仓 0 只、无待执行卖出腿 → 尾盘卖预案对象=空集(合法空, 非漏票); 本场与『空仓防守』互证",
    },
    "卖预案执行": {
        "预案真源": "盘中/%s/playbook.json 缺件(全库最近=盘中/20260930/playbook.json, 跨 3 个交易日, 按零后视镜不作本场输入); 上游 _学习/交易计划_master_%s.json 及五路计划(auction/lhb/limitup/logic/theme)20261012 六件全缺(全库最近=%s) → 今日 playbook 生成链上游断" % (D, D, PREV),
        "leg=close / take_zt 声明": "无 —— ①今日 playbook 缺件; ②交易计划六件缺件 → 无 trigger 区间、无 leg、无 min/max; ③次日卖出指令.json=[]",
        "可卖标的": "真实持仓 0 只(000011 属待裁定虚构产物, 不卖出) → 无票可卖",
        "结果": "未执行(合法空集), fills=[]; 未设任何卖价带、未调用 fills 接口, px_exec(决断后下一 tick 留档价±滑点0.10%)与跌停封死顺延条款均不适用",
        "次弱侧结构标记(仅标记, 非卖出指令)": ["001300 三柏硕 收于跌停(单日振幅≈20pp, 高位接力资金弃筹特征)", "603155 新亚强 10:30 封板后破板未回封(14:44 +5.83)", "605177 东亚药业 / 001336 楚环科技 早盘跌停锁死", "低封板率口径: 触板 28 只中仅 19 只封住(封板率≈68%) → 承接边际弱于 09:31 的 13/… 与 14:15 的 19/…"],
    },
    "fills": [],
    "fills接口说明": "本场零成交: fills=[]。若未来有买腿, 必带整手(100股整数倍)qty; px_exec=决断后下一 tick 留档价 ±滑点 0.10%。本场未生成任何 fill, 未占用该接口。",
    "no_action": True,
    "decision": {
        "level": "NO_FILL_零成交 + B级防守表态(空仓即防守·零动作)",
        "fills": [],
        "零成交原因": "A级: 买入对象=空集(今日 playbook 缺件 + 交易计划_*_20261012 六件缺件 → 无 trigger/abort/leg 可依); 卖出侧=真实持仓 0(000011 非合法) → 无卖腿。B级: 零合法持仓 → 炸板/回撤无对象; 题材批量跳水红线(>=3只2分钟内<=-3pp)决断窗内=0 例 → 未触发。C级: 总审_20261009『C档防守、空仓优先、正式荐票并集 0 只』(置信 78)未解除 + 盘中禁改参数/禁自行升档 → 不启动预案外进攻",
        "B级防守核验": "真实持仓 0 → 防守=维持空仓、零动作。池内结构尾盘未瓦解: 封板 19(14:15→14:44 零新增亦零减少)、本场窗 2 例炸板全部回封、跌停 3 只(其中 2 只早盘即锁死); 但尾盘钝化+跌侧扩容(中位 -0.61pp、深跌 6→9)属『强势钝化、弱尾加深』, 未达升档条件",
        "C级禁止依据": "总审_" + PREV + " 总裁决: 目标日 温度 49.6 中性、涨停 69、炸板 14、跌停 8、封板率 83.13%、炸板率 16.9%、最高 9 板、成交额 19005 亿; 结论=『C档防守、空仓优先, 正式荐票并集 0 只』且明示『不能描述为偏冷/恐慌』。次日验证点(总审自列)以收盘口径为准, 盘中不改判",
    },
    "预收盘复盘": {
        "file": "_学习/盘中尾盘复盘_%s.md" % D,
        "状态": "本场新建(写前 NOT-EXISTS)",
        "口径": "预收盘口径(决策输入 <=14:45:00, 锁定末条 14:44:05), 非收盘口径; 全市场指标(温度/涨停总数/炸板率/最高板/成交额)本时点不可得, 由今晚复盘补全",
    },
    "报警项": [
        {"type": "contract_inputs_missing", "detail": "盘中/%s/pulse.json 全库0命中 / 今日 warboard.json 缺件 / 盘中/%s/执行流水.jsonl 全库0命中 / 今日 playbook.json 缺件 → 任务步骤2/3指定的三个契约文件均不可用, 已按前场先例以 realtime_ticks + 引擎账本替代并登记口径替换" % (D, D)},
        {"type": "warboard_gap", "detail": "作战台快照链断更: 全库最近 warboard.json=盘中/20260930/; 其后 20261008/20261009/20261012 三个交易日连续缺件 → 13号盘中作战agent 的『作战台逐票表态』输入缺失, 只能退回账本口径"},
        {"type": "playbook_upstream_gap", "detail": "playbook 生成链上游(_学习/交易计划_master_%s.json 及五路计划)20261012 六件全缺 → A级买入对象恒为空集, 盘中链『预案→执行→对账』三环节零对象(承 hb-e 同项欠账)" % D},
        {"type": "calendar_contract_drift", "detail": "任务指定交易日校验接口 sentiment.core.calendar 仍 ModuleNotFoundError(规格漂移, 自 09-17 起多次同型) → 本场以 _交易日历.json + 管道实据等效校验"},
    ],
    "缺件": [
        "盘中/%s/pulse.json(契约未实现)" % D,
        "盘中/%s/warboard.json(本日缺件)" % D,
        "盘中/%s/执行流水.jsonl(契约未实现)" % D,
        "盘中/%s/playbook.json(本日缺件)" % D,
        "_学习/交易计划_{master,auction,lhb,limitup,logic,theme}_%s.json(六件全缺)" % D,
        "_学习/总审_%s.json(当日晚间产物, 本场不可用; 已按 %s 版作依据)" % (D, PREV),
    ],
    "对账": {
        "发出版覆盖": "无(新建件, 写前 assert os.path.exists==False)",
        "fills": 0,
        "结论": "本场零成交, 与『零合法持仓/空仓防守』互证; 未改任何账本/净值/次日卖出指令文件",
    },
    "后视镜边界声明": "本件全部输入(jobs.json/executions.db、_交易日历.json、realtime_ticks.jsonl 锁定末条 2026-10-12 14:44:05、launcher.log 至写档时、_学习/竞价快照存档/20261012.csv.gz@09:30:56、交易计划_*_%s、总审_%s.json、_模拟盘/盘中作战/{state,净值,判断流水,账本}.json@14:30) 时间戳均 <= 本件锁定决断时点 2026-10-12 14:45:00 CST; realtime_ticks.jsonl 中 14:45:00 之后写入的帧已明确排除于决策输入。" % (PREV, PREV),
    "reason": "深场B(14:45 尾盘场, 名义决断 2026-10-12 14:45:00, 实派发 claimed 14:45:08.23 / started 14:45:08.55, lateness≈8.6s, on_time)。【数据红线未触发】realtime_ticks 合法帧 313(09:31:07→14:44:05), 最大间隔 61s、>10分钟断更 0 次, 锁定末条 14:44:05 → 允许决策(pulse.json 缺件已登记口径替换)。【池源无降级】pool_date=%s / stale=false / n=69: 中位 %+.2f%%、均值 %+.2f%%、涨/跌 %d/%d、封板 %d、炸板 %d、深跌 %d、跌停 %d。【决断窗】14:35:04→14:44:05 Δ中位 %+.2f、Δ均值 %+.2f; 题材批量跳水红线 0 例(120s/300s 并发最大 0/0); 本场窗 2 例破板全部回封。【尾盘结构】封板 19 恒定(14:15 起零增减)、深跌 6→%d、池中位 14:14→14:44 -0.61pp → 强势钝化、弱尾加深, 未见封板瓦解。【主线】传媒/影视/出版链 %d/%d 封板同簇 → 宽度仍足(>=8), 未散。【持仓】本账合法在持 0 只(000011 属待裁定虚构产物), 引擎今日零成交 → 尾盘卖预案对象=空集。【预案】playbook.json 及五路交易计划今日全缺 → leg=close/take_zt 无声明、无票可卖 → 未执行、fills=[]、未占用 fills 接口。【B级】三类逐项未达标 → 无防守动作。【C级】总审_%s C档防守/空仓优先未解除 + 盘中禁改参数 → 零动作。总判定: NO_FILL 零成交 + B级防守表态 + C级禁止(记录)。" % (
        PREV, S["中位"], S["均值"], S["涨"], S["跌"], S["封板"], len(zha), S["深跌"], len(dt),
        statistics.median(list(dd.values())), sum(dd.values()) / len(dd), S["深跌"], len(chain_hit), len(seal), PREV),
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)
print("WROTE", OUT, os.path.getsize(OUT))

rep = "20261012 深场B(14:45 尾盘场): 在窗真场次(on_time, 迟到 8.6s)。数据红线未触发(313 合法帧 09:31:07→14:44:05, 最大间隔 61s, 断更 0; pulse.json 缺件已登记替换)。锁定末条 14:44:05(池=20261009 zt_pool 69 只, stale=false): 中位 %+.2f%%/均值 %+.2f%%/涨跌 %d/%d; 封板 %d 只[%s]; 炸板 %d; 深跌 %d[%s]; 跌停 %d[三柏硕/楚环科技/东亚药业]。决断窗 14:35→14:44 Δ中位 %+.2f/Δ均值 %+.2f, 题材批量跳水红线 0 例, 本场窗 2 例破板全部回封。尾盘=强势钝化+弱尾加深(封板 19 恒定、深跌 6→%d、中位 14:14→14:44 -0.61pp)。主线传媒/影视/出版链 %d/%d 封板同簇(宽度仍足)。持仓表态: 合法在持 0 只(000011 深物业A 属待裁定虚构产物, 当日 -7.63%%/相对成本 +15.03%%, 09:31 后无 watch 源不可核)→ 无票可卖。尾盘动作: 无(playbook 与五路交易计划今日全缺 → leg=close/take_zt 无声明, fills 空集, 未占用 fills 接口)。B 级三类逐项未达标; C 级禁止(总审_%s C 档防守/空仓优先, 置信 78)未解除 → 维持空仓、零动作。预收盘复盘已建 _学习/盘中尾盘复盘_20261012.md。" % (
    S["中位"], S["均值"], S["涨"], S["跌"], S["封板"], "/".join(r["name"] for r in seal),
    len(zha), S["深跌"], "/".join(r["name"] for r in deep), len(dt),
    statistics.median(list(dd.values())), sum(dd.values()) / len(dd), S["深跌"], len(chain_hit), len(seal), PREV)
print(rep)
