# -*- coding: utf-8 -*-
"""hb-e(14:30尾盘前哨) 20260918 catch_up 实例留档: 本机整交易日停机 -> ALARM_ONLY, 零 fills。
纪律: 幂等/不覆盖(目标决断件已存在则 ABORT); 报警行只追加。"""
import os, sys, json, datetime, subprocess

sys.stdout.reconfigure(encoding="utf-8")
B = r"D:\股票数据\市场数据"
TODAY = "20260918"
D = os.path.join(B, "盘中", TODAY)
now = datetime.datetime.now()
write_ts = now.strftime("%Y-%m-%d %H:%M:%S")

dec_path = os.path.join(D, "临盘决断_%s_1430.json" % TODAY)
if os.path.exists(dec_path):
    print("ABORT: 目标已存在(发出版不可覆盖):", dec_path)
    sys.exit(2)

nominal = datetime.datetime(2026, 9, 18, 14, 30, 0)
last_archive = datetime.datetime(2026, 9, 17, 15, 4, 36)
stale_min = round((nominal - last_archive).total_seconds() / 60.0, 1)
claimed = datetime.datetime(2026, 9, 18, 17, 34, 1, 845682)
lateness_s = (claimed - nominal).total_seconds()
lateness = "%.1fs ≈ %.2fh" % (lateness_s, lateness_s / 3600.0)


def mtime_str(p):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def rd(p):
    try:
        return open(p, encoding="utf-8").read().strip()
    except Exception:
        return None


# ---- 场内/盘后实测(仅台账, 非决策输入) ----
def idx_live():
    try:
        raw = subprocess.check_output(
            ["curl", "-s", "--max-time", "12", "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688"], timeout=20)
        txt = raw.decode("gbk", "ignore")
        out = []
        for seg in txt.split(";"):
            if "~" not in seg:
                continue
            f = seg.split("~")
            if len(f) < 34:
                continue
            out.append("%s %s %+.2f%%(码戳%s)" % (f[2], f[3], float(f[32]), f[30]))
        return out
    except Exception as e:
        return ["采集失败: %s" % e]


lock = rd(os.path.join(B, "盘中", "pipeline.lock"))
launcher_tail = rd(os.path.join(B, "盘中", "launcher.log"))
launcher_tail = "\n".join((launcher_tail or "").splitlines()[-2:])
state = json.load(open(os.path.join(B, "_学习", "_模拟盘", "盘中作战", "state.json"), encoding="utf-8"))
nav = json.load(open(os.path.join(B, "_学习", "_模拟盘", "盘中作战", "净值.json"), encoding="utf-8"))
nextsell = json.load(open(os.path.join(B, "_学习", "_模拟盘", "盘中作战", "次日卖出指令.json"), encoding="utf-8"))
总审 = json.load(open(os.path.join(B, "_学习", "总审_20260911.json"), encoding="utf-8"))
竞价 = json.load(open(os.path.join(B, "_学习", "竞价快照存档", "%s_meta.json" % TODAY), encoding="utf-8"))
ticks_last = rd(os.path.join(B, "盘中", "20260917", "realtime_ticks.jsonl"))
ticks_last = json.loads(ticks_last.splitlines()[-1]) if (ticks_last and ticks_last.splitlines()) else {}
ports = subprocess.run("netstat -ano | grep -E 'LISTENING' | grep -E ':(8899|8602|8420) ' || echo '(8899/8602/8420 无监听)'",
                       shell=True, capture_output=True).stdout.decode("gbk", "ignore").strip()

台账 = {"指数(我实测 %s, 腾讯码戳 16:14)" % now.strftime("%H:%M"): idx_live(),
        "端口(我实测 %s)" % now.strftime("%H:%M"): ports,
        "9/17实时留档末条": "ts=%s / src=%s / n=%s / pool_date=%s / pool_stale=%s" % (
            ticks_last.get("ts"), ticks_last.get("src"), ticks_last.get("n"),
            ticks_last.get("pool_date"), ticks_last.get("pool_stale")),
        "说明": "盘后(收盘后)实测, 仅台账/诊断用途, 严禁作决策或训练输入。"}

b1 = (f"①【本场身份=过期场次 catch_up·收盘后补跑】cron 真源 jobs.json: id=4deb15fee730 / name=sentiment-intraday-hb-e / expr='30 14 * * 1-5' / enabled=true; "
 f"executions.db 本次行 id=0a62b7556f45493ba638561efb02085e, scheduled_instant=2026-09-18T06:30:00+00:00(=2026-09-18 14:30 CST), "
 f"claimed_at=2026-09-18T17:34:01.845682+08:00, started_at=17:34:04.913374 → lateness={lateness}, 且实际执行已收盘(15:00 后 2h34m) → 尾盘窗口(≤14:57)已闭。"
 f"②【红线硬触发·数据断更】名义决断时点(09-18 14:30)之前, 本日盘中留档=零: 盘中/20260918 目录直至 17:49:57 才由本批 catch_up 建立(hb-a 17:51:08 首落档); "
 f"决断时点前最后一条盘中留档=盘中/20260917/realtime_ticks.jsonl 末条 ts=2026-09-17 15:04:36 → 断更 {stale_min} 分钟(≈23h25m, 远超 10 分钟红线) "
 f"→ 按铁律②只报警禁决策, 不写任何预判/触发区间/条件价(铁律①: 执行即编造)。")
b2 = (f"③【根因·宿主整交易日挂起】executions.db 全盘 2026-09-18 记录 claimed_at 集中在 17:33:59–17:34:21(宿主 process 16124 process_started_at=17:33:58): "
 f"此前最后一次成功执行为 hermes-cockpit-refresh / 2026-09-18T02:30+08:00 → 本机自 02:31 起挂起至 17:33, 完整覆盖 09:15–15:00 交易时段; "
 f"sentiment-intraday-pipeline('14 9 * * 1-5') 的 09:14 instant 亦为 catch_up(lateness≈8.33h) → 盘中管道今日零 tick。"
 f"旁证: 盘中/launcher.log mtime={mtime_str(os.path.join(B, '盘中', 'launcher.log'))}, 末两行=『{launcher_tail.replace(chr(10), ' / ')}』; pipeline.lock={lock}(pid 10076, 实测进程不存在) → 通道冻结于 9/17 收盘。")
b3 = (f"④【A级无对象】任务指定的 pulse.json 全盘 0 命中、执行流水.jsonl 全盘 0 命中(契约与实现漂移, 全盘 find 实测); warboard.json 最新=盘中/20260909(断供第7个交易日); "
 f"playbook.json 最新=盘中/20260907; 六路交易计划 max=20260911(20260914–20260918 全缺) → 无 leg 可触发票据, 条件决断=[] 属合法空(非漏写)。"
 f"⑤【B级防守无对象】第七账·盘中作战 state.json: 本金1000000 / cash=1000000.0 / positions=[] ; 净值.json date=20260918 nav=1000000.0 / pos_val=0.0 / n_pos=0; "
 f"次日卖出指令.json=[] → 空仓即防守(非漏执行); 『持仓炸板/大幅回撤/题材批量跳水』三类触发条件均无判定对象(观察池最新=20260911 zt_pool, 对当日零指向)。")
_zj = 总审.get("总裁决") or {}
b4 = (f"⑥【C级禁止】最新总审=_学习/总审_20260911.json: 档位={_zj.get('档位')} / 置信={_zj.get('置信度')} / 结论=『{(_zj.get('结论') or '')[:60]}』→ 防守框架未解除且未覆盖 09-18; 叠加盘中禁改参数、本场零时窗内验证 → 预案外进攻一律不做(铁律④)。"
 f"⑦【交易日判定】任务指定 `sentiment.core.calendar` 实测 FAIL(ModuleNotFoundError: No module named 'sentiment'; D:\\股票数据 与 site-packages 均无该包); 交易日历缓存 _学习/_交易日历.json 末条=20260911(源=_bars_cache); "
 f"改用两路替代判据: (a) 腾讯实时行情码戳=20260918 16:14(上证3911.87/+0.94%、深成13640.87/+1.72%、创业板3372.68/+2.25%、科创50 1652.63/+2.88%) → 09-18 为交易日且已收盘; "
 f"(b) 竞价快照存档/20260918_meta.json 采集成功(sina_spot, 5564 条) → 自标『污染:>09:30盘中累计,只留档不训练』(采集时点=17:36 盘后, 污染防护生效, 未污染训练集)。"
 f"⑧【对账一致】执行流水.jsonl 全盘 0 命中 ↔ 账本.jsonl 末笔=2026-08-13、净值 nav=1000000.0 未变 → 本系统今日零成交, 互证无异常。"
 f"⑨【同批互证】本批 catch_up 内, hb-a(09:40 段)已留档 盘中/20260918/临盘决断_20260918_0940.json、deepb(14:45 段)已留档 临盘决断_20260918_1445.json, 均 level=ALARM_ONLY / fills=[] → 三场结论一致、互不覆盖。")
breason = b1 + b2 + b3 + b4

为备料 = {
 "尾盘卖预案候选": "无对象(非『未写』) —— 第七账空仓(positions=[] / n_pos=0 / cash=100万 / 次日卖出指令=[])且尾盘窗口(≤14:57)已闭; 双重无对象。",
 "明日(2026-09-21 周一)预案要点草稿": "无合法生成路径 —— 明日预案输入=09-18 收盘 fact/涨停池/炸板/龙虎榜/温度/五路建票, 而市场数据日目录 max=20260911(20260914–20260918 全缺)、"
   "总审 max=20260911、计划 max=20260911 → 缺输入编草案=违反铁律①。本场唯一可交付『备料』=恢复清单(见收市后待批清单)。",
 "深场B(14:45)可用输入边界": "本场名义 14:30 虽早于 14:45, 但实际执行 17:34(收盘后), 且 deepb 已于 17:52 独立落档 ALARM_ONLY → 本人不代其决断、不预写其内容; "
   "可用输入仅『当日台账级事实(指数/量能)+盘后旁证』, 严禁作 A/B/C 决断依据(无预案、无持仓、无覆盖今日的总审, 且 iFinD 通道不可用)。",
}

收市后 = ("按改动确认纪律: 本场零改动(未改参数、未覆盖发出版)。收市后待批清单(承接 9/17 台账, 叠加今日新增): "
 "①【最高·宿主级】本机 09-18 02:31–17:33 整段挂起, 覆盖整个交易时段 → 需查电源/休眠/系统日志根因并出防挂起方案(疑似机器而非软件); "
 "②【链路级】日链三任务停摆第 6 个交易日(日目录 max=20260911, 09-14~09-18 全缺): StockDailyChain / AStock-BLite-Daily-Update / AStock-BLite-Tushare-Extended 需恢复+决定补拉范围; "
 "③【派发机制】catch_up 风暴第 3 次复发(09-15、09-17、09-18; 本次 17:33:59–17:34:21 一次性补跑当日全部 23 条错失 instant, 含 8 个盘中 job) → 建议改『按交易日逐段补跑』并对『已收盘的盘中段』自动降级为 ALARM_ONLY(不得假扮时窗内决断); "
 "④【旁路污染】catch_up 原地重写 盘中/20260909/warboard.json(今日 17:34 mtime 失真)与 复盘/盯盘台/intraday.html(现内容日期=20260909) → mtime/页面新鲜度失真, 需加『盘后禁写历史会话目录』守卫; "
 "⑤【iFinD】保活体检 17:34 FAIL(login/取数失败, iFinDPy.pth 缺失) → 盘中仅腾讯降级源(无 Level1/竞价轨迹); "
 "⑥【契约对齐】pulse.json / 执行流水.jsonl 全盘 0 命中 + sentiment.core.calendar 缺失 + 交易日历缓存末条=20260911 → 规格与实现三处漂移, 待补实现或改契约; "
 "⑦【端口】8899(盯盘台)LISTENING(PID 1152); 8602(iFinD)/8420(TencentDB 记忆) 无监听 → 记忆链路待恢复。")

后视镜 = ("本场名义决断时点=2026-09-18 14:30 CST; 实际执行/写档=%s(收盘后 2h5x)。全部结论输入均为『名义时点之前已留档』或『该时点前不存在这一事实本身』: "
 "launcher.log 冻结于 09-17 15:05:36、pipeline.lock=20260917、pulse/warboard/执行流水三缺、playbook(09-07)、计划(09-11)、总审(09-11)、账本(08-13 起算空仓)、"
 "executions.db 派发元数据(17:33:59 起 catch_up)。盘中实时域(09-18 09:30–15:00)本日零留档且不可复现, 不得以盘后数据回填。"
 "另: 台账区指数/端口为 %s 本人盘后实测, 明示仅诊断用途, 不构成本场任何决策输入; 本场结论=ALARM_ONLY, fills=[], 零预判。" % (write_ts, write_ts))

report = ("心跳hb-e无动作·仅报警: 本实例为 scheduler catch_up(名义 2026-09-18 14:30 尾盘前哨; 认领 17:34:01.8 / 启动 17:34:04.9, lateness=%s, 已收盘) —— "
 "根因=本机 02:31–17:33 整段挂起, 覆盖整个交易时段, 盘中/20260918 目录直到 17:49:57 才由 catch_up 建立, 决断时点前断更 %.1f 分钟(>10 分钟红线) → 只报警禁决策; "
 "A级(预案/计划 max=09-11, playbook 09-07 全断)、B级(账户空仓 cash=100万/positions=[])、C级(总审 09-11 档位C 防守未解除)三级全无动作对象 → ALARM_ONLY, 零 fills; "
 "14:45 深场B 备料=无对象(空仓+窗口已闭+日链断供, 缺输入即不得编草案), 仅交付恢复清单收市后待批。" % (lateness, stale_min))

dec = {
 "date": TODAY,
 "session": "hb-e",
 "ts": "14:30",
 "role": "13号盘中作战agent心跳哨兵·尾盘前哨",
 "decision_ts_nominal": "2026-09-18 14:30 CST",
 "exec_kind": "catch_up_out_of_window_after_close",
 "lateness": lateness,
 "write_ts": write_ts,
 "level": "ALARM_ONLY",
 "动作级别": "无动作(禁决策)",
 "场次说明": ("14:30尾盘前哨心跳 hb-e。本实例由 scheduler 判为 catch_up: job_id=4deb15fee730(cron '30 14 * * 1-5', enabled=true), "
   "execution_id=0a62b7556f45493ba638561efb02085e, scheduled_instant=2026-09-18T06:30:00+00:00(=14:30 CST), "
   "claimed_at=2026-09-18T17:34:01.845682+08:00, started_at=17:34:04.913374 → 名义时点已过 %s 且已收盘, 尾盘窗口(≤14:57)闭合。"
   "结论: ALARM_ONLY, fills=[], 不写预判/触发区间/条件价, 不代 14:45 深场B 决断。" % lateness),
 "条件决断": [],
 "fills": [],
 "持仓表态": [],
 "持仓表态_说明": "合法空 —— 第七账·盘中作战 state.json positions=[] / cash=1000000.0; 净值.json n_pos=0 / pos_val=0.0; 次日卖出指令=[]。零持仓即三类防守条件(炸板/大幅回撤/题材批量跳水)无判定对象。",
 "data_freshness": {
   "交易日校验": {
     "任务指定": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" → ModuleNotFoundError: No module named 'sentiment'(D:\\股票数据 与 site-packages 均无该包) → 指定校验环节不可用(契约漂移)。",
     "可用替代": "D:\\股票数据\\市场数据\\trading_calendar.py(load_trading_calendar; 无 is_trading_day 接口)",
     "日历缓存": "_学习/_交易日历.json 末条=20260911(源=_bars_cache 并集) → 不含 09-18, 缓存侧不可判今日。",
     "实测判据": "腾讯实时行情码戳=20260918161402/161427/161442/161414(上证3911.87 +0.94% / 深成13640.87 +1.72% / 创业板3372.68 +2.25% / 科创50 1652.63 +2.88%) → 09-18 为交易日、已收盘(此为盘后旁证)。",
   },
   "pulse": {"path": "盘中/%s/pulse.json" % TODAY, "exists": False,
     "note": "全盘 find 0 命中 → 无脉冲对象可核, 等同断更; 该契约路径在实现中不存在(本系统脉搏实为 warboard 内嵌 fact 字段)。"},
   "realtime_ticks": {"path": "盘中/%s/realtime_ticks.jsonl" % TODAY, "exists": False,
     "last_available": "盘中/20260917/realtime_ticks.jsonl 末条 ts=2026-09-17 15:04:36(src=%s, n=%s, pool_date=%s, pool_stale=%s)" % (
        ticks_last.get("src"), ticks_last.get("n"), ticks_last.get("pool_date"), ticks_last.get("pool_stale")),
     "判定": "★当日(09-18)零条: 盘中/20260918 目录于 17:49:57 才由 catch_up 建立, 未含任何 ticks 文件 → 无『新鲜度』可测, 直接判断更。"},
   "pipeline": {"path": "盘中/pipeline.lock", "content": lock,
     "note": "仍为 20260917(pid 10076 实测已不存在) → 09-18 管道从未上锁/从未启动; launcher.log mtime=%s 末行=[15:05:36] 收盘退出(09-17)。" % mtime_str(os.path.join(B, "盘中", "launcher.log"))},
   "warboard": {"path": "盘中/%s/warboard.json" % TODAY, "exists": False,
     "fallback": "最新=盘中/20260909/warboard.json → 作战台断供第 7 个交易日; 且该文件 mtime 被本批 catch_up 重写为今日 17:34(内容仍=20260909) → mtime 失真已记入待批清单。"},
   "执行流水": {"path": "盘中/%s/执行流水.jsonl" % TODAY, "exists": False,
     "note": "全盘 0 命中(任何日期均不存在) → 无成交流水; 与账本末笔 2026-08-13 互证今日零成交。"},
   "预案真源": {"playbook": "最新=盘中/20260907/playbook.json(全盘仅 3 份) → 对 09-18 零指向",
     "计划文件": "_学习/交易计划_*.json max=20260911(20260912–20260918 全缺) → 无 leg=close/take_zt 可触发票据",
     "总审": "最新=_学习/总审_20260911.json(档位=%s / 置信=%s / 结论『%s』) → 防守未解除且未覆盖今日" % (
        (总审.get("总裁决") or {}).get("档位"), (总审.get("总裁决") or {}).get("置信度"), ((总审.get("总裁决") or {}).get("结论") or "")[:40]),
     "note": "条件决断=[] 属合法空(无预案即无触发器, 非漏写)。"},
   "第七账": {"state": "本金=1000000 / cash=1000000.0 / positions=[] / 起算=20260813", "净值": "date=20260918 nav=1000000.0 / cash=1000000.0 / pos_val=0.0 / n_pos=0",
     "账本.jsonl": "末笔=2026-08-13(起算清仓 2 笔), 之后零成交", "次日卖出指令": "[]"},
   "竞价快照": {"path": "_学习/竞价快照存档/%s_meta.json" % TODAY, "content": 竞价,
     "note": "本日采集时点=17:36(盘后 catch_up 触发), 采集器自标『污染:>09:30盘中累计,只留档不训练』→ 防护生效, A 档竞价样本本日不存在。"},
   "日链": {"状态": "市场数据根目录日目录 max=20260911(20260914–20260918 全缺) → 涨停池/炸板/跌停/龙虎榜/fact 连续断供第 6 个交易日"},
   "stale_min": "%.1f 分钟(名义决断时点 2026-09-18 14:30 − 该时点前最后一条盘中留档 2026-09-17 15:04:36) → 远超 10 分钟红线" % stale_min,
   "诊断证据(非决策输入)": 台账,
 },
 "decision": {"level": "ALARM_ONLY", "fills": [], "reason": breason,
   "为14:45深场B备料": 为备料,
   "note": "①本文件为 hb-e 名义 14:30 段的留档(决策件), 与 报警_%s.jsonl(报警件)同源, 均为只读追加语义, 不覆盖他场发出版; "
     "②同批 hb-a(09:40)/deepb(14:45) 已各自留档同型 ALARM_ONLY, 本文件不代其决断; "
     "③本场未改任何参数、未写任何 fills。" % TODAY},
 "收市后待批清单": 收市后,
 "后视镜边界声明": 后视镜,
 "report": report,
}

with open(dec_path, "w", encoding="utf-8") as f:
    json.dump(dec, f, ensure_ascii=False, indent=1)

alarm = {
 "ts": write_ts, "date": TODAY, "session": "hb-e_1430", "job_id": "4deb15fee730",
 "execution_id": "0a62b7556f45493ba638561efb02085e",
 "scheduled_instant": "2026-09-18T06:30:00+00:00 (= 2026-09-18 14:30 CST)",
 "actual_start": "2026-09-18T17:34:04.913374+08:00",
 "kind": "catch_up", "exec_kind": "catch_up_out_of_window_after_close",
 "lateness": "%s (名义 14:30 → 认领 17:34:01.8)" % lateness,
 "type": "machine_suspended_whole_session_plus_expired_window_catchup",
 "level": "ALARM_ONLY", "fills": [], "持仓表态": [],
 "decision_file": "盘中/%s/临盘决断_%s_1430.json" % (TODAY, TODAY),
 "reason": breason,
 "data_freshness": {
   "pulse": "exists=False(全盘 0 命中) → 无对象可核",
   "realtime_ticks": "当日零条; 最后留档=2026-09-17 15:04:36 → 断更 %.1f 分钟" % stale_min,
   "warboard": "exists=False; 最新=20260909(断供第7日)",
   "执行流水": "全盘不存在 → 零成交",
   "预案真源": "playbook max=20260907; 计划 max=20260911; 总审 max=20260911(档位C/置信0.82)",
   "第七账": "cash=1000000.0 / positions=[] / n_pos=0 / nav=1000000.0 → 空仓",
   "日链": "日目录 max=20260911(09-14~09-18 全缺)",
   "stale_min": "%.1f 分钟(相对名义 14:30)" % stale_min,
   "交易日": "是(腾讯码戳 20260918161402; 指定模块 sentiment.core.calendar 不可用)",
 },
 "对账": {"引擎已执行": "无(执行流水.jsonl 全盘 0 命中)", "账本": "空仓(账本末笔 2026-08-13)", "结论": "一致, 无异常"},
 "盘后旁证(仅台账/非决策输入)": 台账,
 "机制发现": [
   "①宿主整交易日挂起: 09-18 02:31–17:33 无任何执行记录, 17:33:58 宿主进程 16124 启动 → 一次性 catch_up 23 条; 覆盖 09:15–15:00 全时段, 盘中管道零 tick。",
   "②catch_up 风暴第 3 次(09-15 / 09-17 / 09-18): 每 job 只认领一个错失 instant, 已收盘的盘中段仍被补跑 → 建议按交易日逐段补跑 + 收盘后自动降级 ALARM_ONLY。",
   "③catch_up 写历史会话目录导致 mtime 失真: 盘中/20260909/warboard.json 今日 17:34 被重写、复盘/盯盘台/intraday.html 现内容日期=20260909 → 页面新鲜度误导风险。",
   "④日链停摆第 6 个交易日(日目录停在 20260911): 09-14~09-18 涨停池/炸板/龙虎榜/fact 全缺。",
   "⑤iFinD 保活体检 17:34 FAIL(login 失败) → 仅腾讯降级源。",
   "⑥契约对齐三处漂移: pulse.json / 执行流水.jsonl 全盘 0 命中、sentiment.core.calendar 缺失、交易日历缓存末条=20260911。",
 ],
 "收市后待批清单": 收市后,
 "后视镜边界声明": 后视镜,
 "report": report,
}

alarm_path = os.path.join(D, "报警_%s.jsonl" % TODAY)
with open(alarm_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(alarm, ensure_ascii=False) + "\n")

print("OK decision:", dec_path, os.path.getsize(dec_path))
print("OK alarm   :", alarm_path, os.path.getsize(alarm_path), "lines=", sum(1 for _ in open(alarm_path, encoding="utf-8")))
print("report:", report)
