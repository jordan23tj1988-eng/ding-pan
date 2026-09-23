# -*- coding: utf-8 -*-
"""hb-d 2026-09-18 13:30 名义段心跳(catch_up 迟到场次)落档脚本。
纪律:
- 发出版不可覆盖: 目标文件存在即中止, 不改写既有件。
- 零编造: 全程只落 "本日盘中留档=0" 这一事实与既有档案枚举; 无预判/无触发区间/无条件价/无 px_exec。
- 报警行以追加模式写入, 不覆盖同批 catch_up 实例已落档的行。
"""
import json, os, glob, hashlib, time, datetime

BASE = r"D:\股票数据\市场数据"
D = "20260918"
DD = os.path.join(BASE, "盘中", D)
OUT = os.path.join(DD, "临盘决断_%s_1330.json" % D)
ALARM = os.path.join(DD, "报警_%s.jsonl" % D)

if os.path.exists(OUT):
    raise SystemExit("ABORT: 发出版已存在, 依『不可覆盖』纪律拒写: " + OUT)
os.makedirs(DD, exist_ok=True)


def mt(p):
    return time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(p))) if os.path.exists(p) else None


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None


# ---------- 事实采集(全部现场读取, 不自报) ----------
legs = {}
for f in glob.glob(os.path.join(BASE, "_学习", "交易计划_*.json")):
    b = os.path.basename(f)
    leg = b.replace("交易计划_", "").replace(".json", "").rsplit("_", 1)
    legs[leg[0]] = leg[1]
daydirs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(BASE, "20??????")) if os.path.isdir(p))
EXEC_ID = "eb15496cf5dc4e7e9b68c06a82a1caa3"   # 读自 executions.db: job_id=c415a7792216, scheduled_instant=2026-09-18T05:30:00Z
shen = json.load(open(os.path.join(BASE, "_学习", "总审_20260911.json"), encoding="utf-8"))
ledger = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战账本.json"), encoding="utf-8"))
state = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "state.json"), encoding="utf-8"))
master = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "master", "state.json"), encoding="utf-8"))
sells = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "次日卖出指令.json"), encoding="utf-8"))
pf = open(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "判断流水.jsonl"), encoding="utf-8").read().strip().splitlines()
lhb_ticks = [l for l in open(os.path.join(BASE, "盘中", "20260917", "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
last_tick_ts = json.loads(lhb_ticks[-1]).get("ts") or json.loads(lhb_ticks[-1]).get("time")
n_today_ticks = os.path.exists(os.path.join(DD, "realtime_ticks.jsonl"))
launcher = open(os.path.join(BASE, "盘中", "launcher.log"), encoding="utf-8", errors="ignore").read().strip().splitlines()

write_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
nominal = "2026-09-18 13:30"
# 断更: 上一笔盘中留档(9/17 15:04:36) -> 名义决断时点
gap_h = (datetime.datetime(2026, 9, 18, 13, 30) - datetime.datetime(2026, 9, 17, 15, 4, 36)).total_seconds() / 3600.0
lateness_claim = (datetime.datetime(2026, 9, 18, 17, 45, 6) - datetime.datetime(2026, 9, 18, 13, 30)).total_seconds()

records = []

rec = {
    "date": D,
    "session": "hb-d",
    "ts": "13:30",
    "decision_ts_nominal": "%s (cron c415a7792216 '30 13 * * 1-5' 名义段; 本场=catch_up 迟到补跑, last_dispatch.dispatched_at=2026-09-18T17:33:58, lateness=14638.1s)" % nominal,
    "write_ts": write_ts,
    "level": "ALARM_ONLY",
    "动作级别": "无动作(零 fills / 零预判 / 零条件价 / 零 px_exec)",
    "场次说明": (
        "13:30午后延续段心跳 hb-d。★本场为 catch_up 迟到场次: 名义决断时点=2026-09-18 13:30, 实际执行/写档=%s(claim 17:34:01.425, 写档时点迟到≈%.2fh)。"
        "时窗合法性硬判: 盘中分钟级场次的零后视镜前提是『执行时刻≈决断时刻』; 本场执行时点已在收盘(15:00)之后、尾盘可操作窗(≤14:57)亦已闭, "
        "且决断时点(13:30)之前本日【零盘中留档】 -> 依铁律②(盘中域=禁不可复现)+任务步骤2红线(断更>10分钟→只报警禁决策)判为『迟到+黑障双重失效场次』, 不写任何决断/条件价(铁律①)。"
        "★并发声明: 同批 catch_up 另有 hb-a(09:40, 17:51:08 落档) 与 deepb(14:45, 17:54 落档) 已就本日分别落档, 三者各代其名义段, 互不代决断; 本文件不覆盖任何既有件。" % (write_ts, lateness_claim / 3600.0)
    ),
    "条件决断": [],
    "fills": [],
    "data_freshness": {
        "交易日校验": {
            "任务指定": "python -c \"from sentiment.core.calendar import is_trading_day,today_str\" -> ModuleNotFoundError: No module named 'sentiment'(本场实测复现, 全盘无该模块/包) -> 指定校验环节不可用。",
            "可用替代": "市场数据/trading_calendar.py(仅有 load_trading_calendar/next_trading_day, 无 is_trading_day); _学习/_交易日历.json 末条=20260911(缓存由日链日线派生, 随日链同停) -> 本地日历不可判今日。",
            "本场判定依据": "腾讯行情日K sh000001 返回 2026-09-18 完整日线(开3891.960 高3919.670 低3888.500 收3911.870 量485712507), 且 9/14–9/17 逐日有 bar -> 当日为交易日(实据)。★该日线为本场写档时点已收盘数据, 仅作『当日是否交易日』的日历级校验, 不作任何决策输入。"
        },
        "盘中留档(决断时点前)": {
            "盘中/%s/realtime_ticks.jsonl" % D: "不存在(本日实时链路零留档)" if not n_today_ticks else "存在",
            "上一笔盘中留档": "盘中/20260917/realtime_ticks.jsonl 末条 ts=%s (mtime %s)" % (last_tick_ts, mt(os.path.join(BASE, "盘中", "20260917", "realtime_ticks.jsonl"))),
            "决断时点前断更": "≈%.1fh(%.0f分钟) >> 10分钟红线 -> 硬触发, 禁决策" % (gap_h, gap_h * 60),
            "launcher.log": "末行=%s (mtime %s) -> 实时管道 9/17 15:05 收盘退出后未再启动" % (launcher[-1][:40], mt(os.path.join(BASE, "盘中", "launcher.log"))),
            "pipeline.lock": "mtime=%s(冻结于 9/17 重启时刻)" % mt(os.path.join(BASE, "盘中", "pipeline.lock")),
            "结论": "★决断时点前无任何可复现输入 -> 一切结论只能取『数据不存在』这一事实本身, 执行即编造。"
        },
        "pulse": {"path": "盘中/%s/pulse.json" % D, "exists": False, "note": "全盘 glob 0 命中(该路径未实现, 本系统脉搏=warboard 内嵌 fact 快照) -> 任务步骤2 新鲜度核验: 无对象。"},
        "warboard": {
            "path": "盘中/%s/warboard.json" % D,
            "exists": False,
            "fallback": "最新=盘中/20260909/warboard.json(date=20260909, mtime=2026-09-18 17:34 由同批 catch_up 重写但内容日期仍为 9/09) -> 对今日零指向, 无 fact 快照/无优先成交序。"
        },
        "执行流水": {"path": "盘中/%s/执行流水.jsonl" % D, "exists": False, "note": "全盘 glob 执行流水*.jsonl 0 命中 -> 无成交可对账。"},
        "报警档": {"path": "盘中/%s/报警_%s.jsonl" % (D, D), "note": "本场执行时已含同批实例 17:51:08(hb-a)/17:54(deepb) 两条, 本场以追加模式落第 3 条, 未覆盖。"},
        "预案真源": {
            "playbook_max": "盘中/20260907/playbook.json (mtime %s)" % mt(os.path.join(BASE, "盘中", "20260907", "playbook.json")),
            "交易计划_max_by_leg": legs,
            "今日预案文件": [],
            "note": "playbook 9/08 起断供(本日为断供第 9 个交易日); 六路交易计划全部停在 20260911 -> 今日无 leg=close/take_zt 可触发票据 -> A级条件决断合法为空。"
        },
        "总审": {
            "path": "_学习/总审_20260911.json",
            "档位": shen.get("档位") or shen.get("level"),
            "置信度": shen.get("置信度") or shen.get("confidence"),
            "结论": str(shen.get("结论") or shen.get("report"))[:120],
            "note": "无覆盖 9/14–9/18 的总审 -> 防守框架在册未解除。"
        },
        "账本": {"cash": ledger.get("现金"), "nav": ledger.get("nav"), "n_pos": ledger.get("n_pos"), "positions": ledger.get("持仓"), "mtime": mt(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战账本.json")), "state_mtime": mt(os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "state.json"))},
        "账本_master": {"cash": master.get("cash"), "n_pos": len(master.get("positions") or []), "mtime": mt(os.path.join(BASE, "_学习", "_模拟盘", "master", "state.json"))},
        "次日卖出指令": sells,
        "判断流水": {"n": len(pf), "末条": pf[-1][:80] if pf else None},
        "日链": {"市场数据日目录_max": daydirs[-1] if daydirs else None, "缺": "20260914–20260918 (五个交易日)", "note": "日链停摆第 5 个交易日: 涨停池/炸板/跌停/龙虎榜/fact 全缺 -> 观察池与情绪 fact 无可核对象。"},
        "写档时点旁证(非决策输入)": {
            "THS涨停池": "_tmp/ths_pool_20260918_mem.json mtime=%s (17:28 采集, 晚于 13:30 决断时点 -> 只记录, 不作输入)" % mt(os.path.join(BASE, "_tmp", "ths_pool_20260918_mem.json")),
            "竞价快照存档": "_学习/竞价快照存档/20260918.csv.gz mtime=%s, meta 自标『污染:>09:30盘中累计, 只留档不训练』" % mt(os.path.join(BASE, "_学习", "竞价快照存档", "20260918.csv.gz")),
            "executions.db": "本日 23 条执行记录中, 全部盘中 instant(09:14/09:21/09:24/09:40/10:00…/13:30/14:30/14:45) 的 claimed_at 集中在 17:33:59–17:34:05, 宿主 pid=16124 process_started_at≈17:33:58 -> 本机整个交易日停机, 盘中链路从未启动(非仅本场迟到)。"
        }
    },
    "三级判定": {
        "A级_预案内": {"对象": "无", "依据": "今日 playbook 缺(最新 20260907)、六路交易计划缺(最新 20260911)、warboard 今日缺 -> 无 trigger 可核, 条件决断=[]。"},
        "B级_预案外防守": {"对象": "无", "依据": "三账本全程空仓: 盘中作战 cash=%s/positions=[]/n_pos=%s, master cash=%s/positions=[], 次日卖出指令=%s, 六路 state.json mtime=9/14 -> 无持仓可逐票表态; 观察池为 9/11 陈旧池且今日零 tick -> 炸板/大幅回撤/题材批量跳水三类均无合法判定对象。" % (ledger.get("现金"), ledger.get("n_pos"), master.get("cash"), sells)},
        "C级_预案外进攻": {"对象": "无(禁)", "依据": "总审 20260911 档位 C/置信 0.82『冰点防守, 仅保留观察, 不形成进攻仓位』未解除, 其可证伪条件因 9/12 起日链+fact 断供无法验证; 叠加 ①盘中禁改参数 ②零有效票池 ③时窗已闭 -> 预案外进攻一律不做, 仅记录。"}
    },
    "报警项": [
        "①【红线】决断时点前断更≈%.1fh(%.0f分钟, 远超10分钟): 本日盘中链路零 tick(盘中/%s/realtime_ticks.jsonl 不存在), 上一笔留档=2026-09-17 15:04:36 -> 只报警禁决策;" % (gap_h, gap_h * 60, D),
        "②【根因·整机停机】executions.db 本日 23 条执行全部于 17:33:59–17:34:05 被宿主 pid=16124(启动≈17:33:58) 补发, 含 09:14 盘中管道 b8e2f1f39fd3 与其 30 分钟看门狗 -> 本机整个交易日关机/掉线, 盘中管道从未启动, launcher.log 停于 9/17 15:05:36『收盘退出』;",
        "③【契约三缺】pulse.json 全盘 0 命中 / warboard.json 今日缺(最新 9/09 且内容日期仍 9/09) / 执行流水.jsonl 全盘 0 命中;",
        "④【预案真源断供】playbook max=20260907(断供第 9 个交易日), 六路交易计划 max=20260911;",
        "⑤【日链停摆第 5 日】市场数据日目录 max=20260911, 9/14–9/18 五日全缺(涨停池/炸板/跌停/龙虎榜/fact 全缺);",
        "⑥【场次履约】本日为 hb-d 名义段『执行时刻 ≫ 决断时刻』失效场次(迟到≈%.2fh), 盘中域不可复现 -> 该段收益/风险敞口无从结算, 属系统级欠账, 待收市后整体处置(是否补拉数据、心跳是否按交易日逐段补跑)待用户拍板;" % (lateness_claim / 3600.0),
        "⑦【规格缺陷】任务步骤1 指定校验命令引用不存在的模块 sentiment.core.calendar -> 每个心跳场次都需人工替换证据链, 建议改指向可用接口(待批)。"
    ],
    "对账": {
        "引擎已执行": "无(执行流水.jsonl 全盘不存在; 判断流水末条=08-18)",
        "账本": "全账户空仓(盘中作战 cash=1000000.0/n_pos=0/持仓=[]; master cash=1009012.5/n_pos=0; 六路 mtime 9/14 16:08)",
        "结论": "一致, 无异常; 无成交、无持仓、无卖单 -> 本日无敞口被漏记。"
    },
    "后视镜边界声明": (
        "决断时点=2026-09-18 13:30(名义/计划时点), 实际写档=%s。本场结论的全部决策输入限定为该时点之前已留档的数据, 或『该数据不存在』这一事实本身; "
        "而本日该时点之前【不存在任何盘中留档】(整机停机, 零 tick) -> 决策输入集合为空 -> 本场零 fills、零预判、零触发区间、零条件价、零 px_exec, 不构成编造(铁律①)。"
        "写档时点之后的实测(收盘日线/THS 17:28 涨停池/竞价快照 17:36/executions.db 补发记录/同批实例 17:51+17:54 落档)仅用于交易日校验与停机根因描述, 一律不作决策输入。"
    ) % write_ts,
    "report": (
        "心跳hb-d无动作·仅报警: 2026-09-18 13:30 段(catch_up 迟到≈%.2fh) —— 本机整个交易日停机(executions.db 本日 23 条执行全部于 17:33:59–17:34:05 由 pid 16124 补发), 盘中链路从未启动, "
        "决断时点前本日零留档、断更≈22.4h(远超 10 分钟红线) -> 只报警禁决策; A级无对象(playbook max 20260907、六路交易计划 max 20260911、warboard 今日缺)、"
        "B级无对象(三账本全程空仓, 无持仓可表态, 观察池 9/11 陈旧)、C级禁(总审 20260911 C档 0.82 未解除) -> ALARM_ONLY, 零 fills 零条件价; "
        "另报 pulse/执行流水全盘 0 命中 + 日链停摆第 5 个交易日(日目录 max=20260911, 9/14–9/18 全缺) + 步骤1 校验命令引用不存在模块(待批)。"
    ) % (lateness_claim / 3600.0),
}
records.append(rec)

# ---------- 落档 ----------
payload = json.dumps(rec, ensure_ascii=False, indent=1)
with open(OUT, "x", encoding="utf-8") as f:   # x = 独占创建, 已存在则抛错(双保险)
    f.write(payload)

alarm = {
    "ts": write_ts, "date": D, "session": "hb-d",
    "job_id": "c415a7792216", "execution_id": EXEC_ID,
    "scheduled_instant": "2026-09-18T05:30:00+00:00 (= 2026-09-18 13:30 CST)",
    "actual_start": write_ts, "kind": "catch_up", "exec_kind": "expired",
    "lateness": "≈%.2fh (名义 2026-09-18 13:30 -> 实际写档 %s; 窗口/收盘均已过)" % (lateness_claim / 3600.0, write_ts),
    "nominal_decision_ts": nominal,
    "type": "expired_session_catchup_plus_machine_down_all_day_data_blackout",
    "level": "ALARM_ONLY",
    "decision_file": "盘中/%s/临盘决断_%s_1330.json" % (D, D),
    "fills": [], "持仓表态": [],
    "detail": rec["report"],
    "依据": "盘中/%s/临盘决断_%s_1330.json; 数据留档=盘中/20260917/realtime_ticks.jsonl 末条 %s; 停机根因=executions.db 本日 23 条 claimed_at 17:33:59–17:34:05 (pid 16124); 账本=_学习/_模拟盘/盘中作战账本.json(cash=1000000.0/n_pos=0)+master(cash=1009012.5/n_pos=0)+次日卖出指令=[]。" % (D, D, last_tick_ts),
}
with open(ALARM, "a", encoding="utf-8") as f:
    f.write(json.dumps(alarm, ensure_ascii=False) + "\n")

print("OK wrote:", OUT, os.path.getsize(OUT), "sha256", sha(OUT))
print("alarm lines now:", sum(1 for _ in open(ALARM, encoding="utf-8")))
print("alarm last:", open(ALARM, encoding="utf-8").read().strip().splitlines()[-1][:200])
print("legs:", legs)
print("shen:", shen.get("档位") or shen.get("level"), shen.get("置信度") or shen.get("confidence"))
