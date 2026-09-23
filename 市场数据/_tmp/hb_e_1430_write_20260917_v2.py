# -*- coding: utf-8 -*-
"""hb-e(hb-e 14:30尾盘前哨) 20260917 catch_up 实例留档 v2 —— 修正 v1 的两处客观字段错误:
 ①『指数』误用 f[4](昨收) 配 涨跌幅 → 应为 f[3](最新价); ②『端口』因 netstat 输出 GBK 解码失败写成空串。
 语义不变(ALARM_ONLY / 零 fills); 仅重写本实例(session=hb-e)的决策件与报警行, 不动他场留档。"""
import os, sys, json, datetime, subprocess

sys.stdout.reconfigure(encoding="utf-8")
B = r"D:\股票数据\市场数据"
TODAY = "20260917"
D = os.path.join(B, "盘中", TODAY)
now = datetime.datetime.now()
write_ts = now.strftime("%Y-%m-%d %H:%M:%S")
EXEC_ID = "314f3f10d81c4b259c94a00d909cb3a4"

dec_path = os.path.join(D, "临盘决断_%s_1430.json" % TODAY)
alarm_path = os.path.join(D, "报警_%s.jsonl" % TODAY)


def tail_ticks():
    p = os.path.join(D, "realtime_ticks.jsonl")
    lines = [l for l in open(p, encoding="utf-8") if l.strip()]
    first = json.loads(lines[0]); last = json.loads(lines[-1])
    rows = last.get("rows", [])
    up = sum(1 for x in rows if x["pct"] > 0); dn = sum(1 for x in rows if x["pct"] < 0)
    zt = sum(1 for x in rows if x["pct"] >= 9.8); dt = sum(1 for x in rows if x["pct"] <= -9.8)
    top = sorted(rows, key=lambda x: -x["pct"])[:4]; bot = sorted(rows, key=lambda x: x["pct"])[:3]
    return {"path": "盘中/%s/realtime_ticks.jsonl" % TODAY, "n_tick": len(lines),
            "首条": first["ts"], "末条": last["ts"], "src": last.get("src"), "n": last.get("n"),
            "pool_date": last.get("pool_date"), "pool_stale": last.get("pool_stale"),
            "池内涨跌": "涨%d/跌%d/涨幅>=9.8%%共%d/跌幅<=-9.8%%共%d" % (up, dn, zt, dt),
            "池内涨幅前4": ["%s %+.2f%%" % (x["name"], x["pct"]) for x in top],
            "池内跌幅前3": ["%s %+.2f%%" % (x["name"], x["pct"]) for x in bot]}


def idx_live():
    raw = subprocess.check_output(["curl", "-s", "--max-time", "12",
        "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688"], timeout=20)
    txt = raw.decode("gbk", "ignore")
    out = []
    for seg in txt.split(";"):
        f = seg.split("~")
        if len(f) < 34:
            continue
        out.append("%s %s(最新) %s(昨收) %+.2f%% 码戳%s" % (f[2], f[3], f[4], float(f[32]), f[30]))
    return out


def ports():
    r = subprocess.run('netstat -ano | findstr LISTENING | findstr ":8899 :8602 :8420"',
                       shell=True, capture_output=True)
    txt = (r.stdout or b"").decode("gbk", "replace").strip()
    return txt.replace("\n", " | ") if txt else "(8899/8602/8420 均无监听)"


ticks = tail_ticks(); indices = idx_live(); prt = ports()
nominal = datetime.datetime(2026, 9, 16, 14, 30, 0)
freeze = datetime.datetime(2026, 9, 11, 10, 0, 11)
stale_min = round((nominal - freeze).total_seconds() / 60.0, 1)
锁 = open(os.path.join(B, "盘中", "pipeline.lock"), encoding="utf-8").read().strip()
账本 = json.load(open(os.path.join(B, "_学习", "_模拟盘", "盘中作战账本.json"), encoding="utf-8"))
竞价 = json.load(open(os.path.join(B, "_学习", "竞价快照存档", "%s_meta.json" % TODAY), encoding="utf-8"))
总审 = json.load(open(os.path.join(B, "_学习", "总审_20260911.json"), encoding="utf-8"))
总决 = 总审.get("总裁决") or {}

半日实况 = {"指数": indices, "观察池40只(9/11旧池)": ticks, "端口": prt,
        "说明": "11:53–12:0x 本人实测, 仅台账记录, 严禁作决策或训练输入。"}

breason = (
 "①【本场身份=过期场次 catch_up】executions.db: job_id=4deb15fee730 / execution_id=%s, "
 "scheduled_instant=2026-09-16T06:30:00+00:00(= 2026-09-16 14:30 CST), claimed_at=2026-09-17T11:52:50+08:00, started_at=11:52:54 → "
 "lateness≈21.38h。即本实例名义场次=【9/16 尾盘前哨】, 而实际执行落在 9/17 午休段(11:5x)。" % EXEC_ID
 + "②【9/16 名义场次无输入】9/16 决断时点(14:30)之前: 全盘零实时留档(实时通道自 2026-09-11 10:00:11 冻结 → 断更 %.1f 分钟≈124.5h)、"
   "盘中/20260916 目录不存在、pulse/warboard/执行流水三缺、日链产物 9/14–9/17 全缺 → 执行即编造(铁律①), 禁决策。" % stale_min
 + "③【9/17 现代场次未到点】本机当前 %s, 下午尚未开盘, 今日 14:30 名义段尚有约 2h 余未到(jobs.json next_run_at=2026-09-17T14:30:00+08:00) → "
   "不得以『今日尾盘段』名义执行, 亦不预写今日决断(写即把 11:5x 数据冒充 14:30 决断=后视镜+编造双违反)。" % write_ts
 + "④【A级无对象】预案真源断供: playbook 最新=盘中/20260907/playbook.json; 交易计划全量 max=20260911(20260914–20260917 全缺) → 无 leg=close/take_zt 可触发票据, 条件决断=[] 属合法空。"
 + "⑤【B级无对象】盘中作战账本(11:53 回写): 本金100万 / 现金=1000000 / 持仓=[] / n_pos=0 → 空仓, 无持仓可逐票表态; "
   "『持仓炸板/大幅回撤/题材批量跳水』三类防守触发条件均无判定对象, 且今日观察池=9/11陈旧池(pool_stale=true)对当日零指向。"
 + "⑥【C级禁止】最新总审=_学习/总审_20260911.json(档位%s / 置信%s /『%s』)→ 防守框架未解除, 且无覆盖 9/16、9/17 的总审 → 预案外进攻一律不做(铁律④退潮防守)。" % (
   总决.get("档位"), 总决.get("置信度"), (总决.get("结论") or "")[:30])
 + "⑦【数据面区分·关键】当日(9/17)腾讯降级通道『新鲜』(管道 11:52:55 重启, PID %s, tick 每 60s 一条), 未触发当日断更红线; "
   "但『新鲜』不等于『可决断』—— 名义决断时点之前留档为零 + 无预案无持仓无总审覆盖, 三级仍全无动作对象。" % 锁.split()[-2]
 + "⑧【对账一致】执行流水.jsonl 全盘不存在(引擎零成交) ↔ 账本空仓, 互证无异常。")

为备料 = {
 "尾盘卖预案候选": "无 —— 账本空仓(positions=[] / n_pos=0), 无持仓可卖 → 尾盘卖预案无对象(非『漏写』, 是『无对象』)。",
 "明日(9/18)预案要点草稿": "无合法生成路径 —— 明日预案输入=本日收盘 fact/涨停池/龙虎榜/温度, 而日链三只计划任务实测『已禁用』"
   "(StockDailyChain 上次运行 2026/9/11 16:30、结果=1; 市场数据日目录 max=20260911) → 若收盘后日链仍不恢复, 9/18 预案同样断供。"
   "本场能交付的唯一『备料』=恢复清单(见收市后待批清单), 而非内容草案 —— 缺输入时编草案违反铁律①。",
 "深场B(14:45)可用输入边界": "仅『当日 realtime_ticks + 指数快照』这类台账级事实; 严禁用于 A/B/C 决断(无预案、无持仓、无覆盖 9/16–9/17 的总审); "
   "且该源为腾讯降级(无 Level1 盘口/无竞价轨迹, iFinD login rc=-2), 观察池为 9/11 陈旧池。",
}

收市后 = ("按改动确认纪律, 盘中(及本场)零改动, 收市后先出方案+判断依据待批。顺序建议: "
 "①【最高·链路级】日链三只计划任务『已禁用』根治(StockDailyChain / AStock-BLite-Daily-Update / AStock-BLite-Tushare-Extended, schtasks 实证已禁用) "
 "+ 决定 9/14–9/17 四日数据是否补拉(涨停池/炸板/跌停/龙虎榜/fact 全缺); "
 "②iFinD 登录 rc=-2 修复 + 盘中管道守护(当前仅腾讯降级源, 无 Level1/竞价轨迹); "
 "③catch_up 派发机制: 每 job 只认领一个错失 instant → 9/15、9/17 两次『catch_up 风暴』(9/17 11:52:47–11:52:57 并行派发 9 个盘中 job) 复发, 建议改『按交易日逐段补跑』; "
 "④契约与实现对齐: prompt 指定的 pulse.json / 执行流水.jsonl 两条路径全盘 0 命中(本系统脉搏实为 warboard 内嵌 fact 字段) → 二选一; "
 "⑤交易日历缓存补更: _学习/_交易日历.json 末条=20260911, 且任务指定的 sentiment.core.calendar 模块不存在(ModuleNotFoundError) → 交易日校验环节无可靠实现; "
 "⑥端口服务: 8899(盯盘台)/8602(iFinD)/8420(记忆库) 当前均无监听 → 页面与记忆链路待恢复。")

后视镜 = ("本场决断时点(名义)=2026-09-16 14:30; 实际执行/写档 %s。全部决策输入均为名义决断时点之前已留档、或『不存在』这一事实本身: "
 "launcher.log 冻结于 2026-09-11 10:00:11、pipeline.lock 旧值 20260911 09:14:49、三账本(11:53 零数据自评回写)、playbook(9/07)、交易计划(max 9/11)、"
 "总审(9/11)、日目录与计划任务枚举。半日实况区(指数/tick/池内涨跌)为 11:53–12:0x 实测, 明示仅台账用途、不构成任何决策输入; 本场结论=禁决策、零 fills。"
 "本文件写入后, 2026-09-17 14:30 名义场次若在时窗内执行, 其独立结论另行留档, 本文件不代其决断。" % write_ts)

report = ("心跳hb-e无动作·仅报警: 本实例为 scheduler catch_up(名义 2026-09-16 14:30 尾盘前哨, 实际 9/17 11:52:54 执行, lateness≈21.4h) —— "
 "9/16 决断时点前零实时留档(通道自 9/11 10:00:11 冻结, 断更 %.1f 分钟)、今日 14:30 场次尚未到点, 且预案(playbook max 9/07 / 计划 max 9/11)、"
 "持仓(空仓)、总审(9/11 档位C防守)三级全无动作对象 → ALARM_ONLY, 零 fills 零预判; 当日腾讯降级通道每 60s 续写虽新鲜, 仅够台账不够决断; "
 "根因=日链三任务『已禁用』, 收市后待批。" % stale_min)

dec = {
 "date": TODAY, "session": "hb-e", "ts": "14:30", "write_ts": write_ts,
 "版本": "v2(修正 v1: 指数字段取值/端口解码; 语义与结论不变, 仍 ALARM_ONLY 零 fills)",
 "场次说明": ("14:30尾盘前哨心跳 hb-e, 本实例为 catch_up: scheduled_instant=2026-09-16T06:30:00+00:00(=2026-09-16 14:30 CST), "
   "claimed_at=2026-09-17T11:52:50+08:00, started_at=11:52:54 → 名义决断时点已过 21.38h, 且 9/16 盘中面全缺; "
   "今日(9/17)14:30 名义段未到点(jobs.json next_run_at=2026-09-17T14:30:00+08:00), 本文件不代其决断、不预写。结论: ALARM_ONLY, fills=[], 不写预判/触发区间/条件价。"),
 "条件决断": [],
 "data_freshness": {
   "交易日校验": {
     "任务指定": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → ModuleNotFoundError: No module named 'sentiment' → 指定校验环节不可用。",
     "可用替代": "D:\\股票数据\\市场数据\\trading_calendar.py(load_trading_calendar/next_trading_day, 无 is_trading_day)",
     "日历缓存": "_学习/_交易日历.json 末条=20260911(源=_bars_cache 并集) → 未含 9/14–9/17 → 缓存侧同样不可判今日。",
     "实测替代判据": "腾讯实时行情带本机码戳 2026-09-17 12:0x(指数 20260917120300/120339/120354, 个股 20260917120218)+ 管道每 60s 续写 → 判定 2026-09-17 为交易日、当前处午休段。"},
   "realtime_ticks": {"path": ticks["path"],
     "实测": "%s(首) → %s(末), 共 %d 条, 每 60s, src=%s, n=%s, pool_date=%s, pool_stale=%s" % (
        ticks["首条"], ticks["末条"], ticks["n_tick"], ticks["src"], ticks["n"], ticks["pool_date"], ticks["pool_stale"]),
     "判定": "★当日通道新鲜(间距 60s < 10 分钟, 当日红线未触发; 与 9/14、9/15 全黑不同); 但①源=腾讯降级(iFinD 不可用), 无 Level1 盘口; ②观察池=20260911 陈旧池(pool_stale=true) → 池对当日零指向; ③恢复时点(11:52:55)在两个名义决断时点之后 → 不能救过期场次。"},
   "pipeline": {"path": "盘中/pipeline.lock", "content": 锁,
     "note": "内容=『20260917 10076 11:52:55』=今日 11:52:55 重启(PID 10076); 此前上锁值=20260911 09:14:49 → 直证 9/14–9/17 上午零取数。"},
   "pulse": {"path": "盘中/%s/pulse.json" % TODAY, "exists": False,
     "note": "不存在 → 无脉冲可核, 等同断更(该契约路径在实现中不存在: 全盘 find 0 命中; 本系统脉搏实为 warboard 内嵌 fact 快照字段, warboard_build.py 产出)。"},
   "warboard": {"path": "盘中/%s/warboard.json" % TODAY, "exists": False,
     "fallback": "最新=盘中/20260909/warboard.json → 作战台自 9/10 起断供, 对 9/16、9/17 零指向。"},
   "执行流水": {"path": "盘中/%s/执行流水.jsonl" % TODAY, "exists": False,
     "note": "全盘不存在任何 执行流水.jsonl → 无成交流水; 与账本空仓互证(引擎今日零成交)。"},
   "预案真源": {"playbook": "最新=盘中/20260907/playbook.json(对 9/16、9/17 零指向)",
     "计划文件": "_学习/交易计划_*.json max=20260911(20260914–20260917 全缺), 无可触发票据",
     "总审": "最新=_学习/总审_20260911.json(日期=20260911, 档位=%s, 置信=%s, 结论『%s』) → 防守未解除且未覆盖今日" % (
       总决.get("档位"), 总决.get("置信度"), (总决.get("结论") or "")[:40]),
     "note": "条件决断=[] 属合法空(无预案即无触发器, 非漏写)。"},
   "三账本": {"盘中作战": "本金=%s / nav=%s / 现金=%s / 持仓=%s / n_pos=%s / 起算=%s(今日 11:53 零数据自评回写)" % (
       None, 账本.get("nav"), 账本.get("现金"), 账本.get("持仓"), 账本.get("n_pos"), 账本.get("起算")),
     "口径": "盘中作战独立账本(本金100万, 起算20260813), 不共用 master 账; 当前空仓 100% 现金。"},
   "竞价快照": {"path": "_学习/竞价快照存档/%s_meta.json" % TODAY, "content": 竞价,
     "note": "本日 A 档竞价样本不存在: 采集器自标『失败 / em、sina 均不可达,不造数』(符合铁律①), 且采集时点 11:57:36 已在盘中 → 即便成功亦污染。"},
   "日链": {"状态": "市场数据根目录日目录 max=20260911(9/14、9/16、9/17 全缺) → 涨停池/炸板/跌停/龙虎榜/fact 连续断供; 管道已报警『目标日 20260916 涨停池未落档, 降级用 20260911(40只)』",
     "根因实证": "schtasks 实测三只计划任务『已禁用』: StockDailyChain(上次运行 2026/9/11 16:30, 上次结果=1) / AStock-BLite-Daily-Update(2026/7/2) / AStock-BLite-Tushare-Extended(2026/7/2) → 日链停摆第 4 个交易日。"},
   "stale_min": "相对名义决断时点(2026-09-16 14:30): 该时点前最后一条盘中留档=2026-09-11 10:00:11(launcher.log 冻结) → 断更 %.1f 分钟(≈124.5h), 远超 10 分钟红线 → 只报警禁决策; 相对当日(9/17)则通道新鲜(此反差即本期机制问题: 恢复晚于名义时点)。" % stale_min,
   "诊断证据(非决策输入)": 半日实况},
 "decision": {"level": "ALARM_ONLY", "fills": [], "reason": breason, "为14:45深场B备料": 为备料,
   "note": "本场新增/复核要点: ①【正向】实时通道 11:52:55 重启恢复(腾讯降级源, tick 每 60s 续写), 结束自 9/11 起的零留档; 但池滞后(pool_stale=true)未解、无 Level1; "
     "②【负向】catch_up 风暴第 2 次复发(9/17 11:52:47–11:52:57 并行派发 9 个盘中 job), 同批 hb-b 于 12:04:19、deepb 于 11:58:40 已各自留档同型 ALARM_ONLY —— 三份留档结论一致、互不覆盖; "
     "③本文件与 报警_20260917.jsonl 同源留档(决策件+报警件), 只读追加语义, 不覆盖他场发出版。"},
 "半日实况(仅台账/非决策输入)": 半日实况,
 "收市后待批清单": 收市后,
 "后视镜边界声明": 后视镜,
 "report": report,
}
json.dump(dec, open(dec_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

alarm = {
 "ts": write_ts, "date": TODAY, "session": "hb-e", "job_id": "4deb15fee730", "execution_id": EXEC_ID,
 "scheduled_instant": "2026-09-16T06:30:00+00:00 (= 2026-09-16 14:30 CST)",
 "actual_start": "2026-09-17T11:52:54+08:00", "kind": "catch_up",
 "lateness": "≈21.38h (名义决断时点 2026-09-16 14:30 → 实际执行 2026-09-17 11:52:54)",
 "type": "expired_session_catchup_plus_decision_window_not_reached",
 "level": "ALARM_ONLY", "fills": [],
 "decision_file": "盘中/%s/临盘决断_%s_1430.json" % (TODAY, TODAY), "持仓表态": [],
 "reason": breason,
 "data_freshness": {
   "realtime_ticks": "%s 实测 %s→%s 共 %d 条/每60s/src=%s/n=%s/pool=%s(stale=%s) → 当日新鲜(未触发当日红线); 但名义时点(9/16 14:30)前留档为零(断更 %.1f 分钟)" % (
     ticks["path"], ticks["首条"], ticks["末条"], ticks["n_tick"], ticks["src"], ticks["n"], ticks["pool_date"], ticks["pool_stale"], stale_min),
   "pulse": "exists=False(契约路径未实现) → 无脉冲对象可核",
   "warboard": "exists=False, 最新=20260909 → 对 9/16、9/17 零指向",
   "执行流水": "全盘不存在 → 无成交可对账",
   "预案真源": "playbook max=20260907; 交易计划 max=20260911(9/14–9/17 全缺); 总审 max=20260911(档位C/防守, 置信0.82)",
   "三账本": "盘中作战: 现金=1000000 / 持仓=[] / n_pos=0 / 起算20260813 → 空仓",
   "日链": "日目录 max=20260911; schtasks 实证三任务『已禁用』(StockDailyChain 上次运行 2026/9/11 16:30 结果=1)",
   "stale_min": "%.1f 分钟(相对 9/16 14:30 名义时点; 最后留档=2026-09-11 10:00:11)" % stale_min},
 "对账": {"引擎已执行": "无(执行流水.jsonl 全盘不存在, 零成交)", "账本": "空仓(cash=1000000, positions=[], n_pos=0)", "结论": "一致, 无异常"},
 "半日实况(仅台账/非决策输入)": 半日实况,
 "机制发现": [
   "①catch_up 风暴第 2 次复发: 9/17 11:52:47–11:52:57 scheduler 并行派发今日执行 21 条(含 9 个盘中 job: hb-a/b/c/d/e + preread + deepb + pipeline + watch), scheduled_instant 多为 9/15–9/16 各整点 → 『每 job 只认领一个错失 instant』缺陷复发(同 9/15 台账)。",
   "②日链停摆第 4 个交易日未修: 市场数据日目录停在 20260911, 9/14–9/17 全缺; 根因=三只计划任务状态『已禁用』。",
   "③iFinD 实时通道仍不可用: 今日 11:53:01 签名 login rc=-2(cron 5d8760e7a962 保活体检 exit=1 ALARM) → 仅腾讯降级源(无 Level1 盘口/无竞价轨迹; 竞价快照 11:57:36 自标失败不造数)。",
   "④契约与实现不一致: prompt 指定的 pulse.json / 执行流水.jsonl 全盘 0 命中(脉搏实为 warboard 内嵌 fact 字段) → 待二选一。",
   "⑤交易日校验环节无可靠实现: sentiment.core.calendar 模块缺失 + 交易日历缓存末条=20260911, 两路皆不可判今日。",
 ],
 "收市后待批清单": 收市后, "后视镜边界声明": 后视镜, "report": report,
}

# 重写本实例(session=hb-e)的报警行, 保留他场既有行(不覆盖他场发出版)
old = [l for l in open(alarm_path, encoding="utf-8") if l.strip()]
kept = [l for l in old if (json.loads(l).get("session") != "hb-e")]
with open(alarm_path, "w", encoding="utf-8") as f:
    for l in kept:
        f.write(l if l.endswith("\n") else l + "\n")
    f.write(json.dumps(alarm, ensure_ascii=False) + "\n")

print("OK decision:", dec_path, os.path.getsize(dec_path))
print("OK alarm   :", alarm_path, os.path.getsize(alarm_path), "保留他场行数=", len(kept))
print("指数:", indices)
print("端口:", prt)
