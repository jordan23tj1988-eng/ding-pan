# -*- coding: utf-8 -*-
"""心跳 hb-c (11:00 半日收尾段) 落档: 报警行
铁律: 发出版不可覆盖 / 只用决断时间戳(11:00)之前已留档数据 / 数据断更>10分钟=只报警禁决策"""
import json, os, datetime

D = "20260918"
BASE = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + os.sep + "..")
outdir = os.path.join(BASE, "盘中", D)
os.makedirs(outdir, exist_ok=True)
alarm_p = os.path.join(outdir, "报警_%s.jsonl" % D)
dec_p = os.path.join(outdir, "临盘决断_%s_1100.json" % D)
assert not os.path.exists(dec_p), "发出版已存在, 不可覆盖: " + dec_p

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

detail = (
    "本场=hb-c(11:00 半日收尾段, 名义决断时点 2026-09-18 11:00)。"
    "①【本场身份】scheduler 判为 catch_up: scheduled_instant=2026-09-18T11:00:00+08:00, 实际启动 2026-09-18T17:34:04+08:00, "
    "lateness=23638.1s(约6.57h) → 名义决断时点已过、且已收盘(15:00) → 不以11:00名义做任何决断, 不预写 临盘决断_20260918_1100.json"
    "(写即用17:5x已收盘数据冒充11:00决断=后视镜/编造双违反, 铁律①②)。"
    "②【数据面硬缺·断更红线硬触发】盘中/20260918/ 目录不存在 → pulse.json(=本系统 warboard 内嵌 fact 快照) / warboard.json / "
    "执行流水.jsonl / 报警_20260918.jsonl 全缺。实时通道最后留档=盘中/20260917/realtime_ticks.jsonl(mtime 9/17 15:04); "
    "相对本场名义决断时点(9/18 11:00)断更约 20.0h(约1196分钟) >> 10分钟红线 → 只报警禁决策。"
    "三缺复核: warboard.json 最新落档=盘中/20260909/warboard.json; 全仓 find 无 执行流水*.jsonl(引擎今日零成交亦无从核); "
    "pipeline.lock 冻结=\"20260917 10076 11:52:55\"(9/17 收盘未清锁, 跨日残留); 盘中/launcher.log 末行=\"[15:05:36] 收盘退出\"(9/17) "
    "→ 9/18 没有任何一秒钟的盘中管道留档。"
    "③【根因·调度宿主整段离线】executions.db 实证: 9/18 最后成功 run=02:30:41(DS保活 e727f6e55cbf), 之后至 17:33:58 零 run; "
    "17:34 一次 catch-up 集中补齐 09:40/10:30/11:00/13:30/14:30 五个心跳(含本场)及竞价快照/THS 等, 落档时刻 17:34–17:47 "
    "(含 _学习/竞价快照存档/20260918.csv.gz, meta 采集时间 17:36:00, 自标'污染:>09:30盘中累计,只留档不训练') "
    "→ 9/18 全交易日盘中链(09:25 起)从未启动; 属调度宿主停机, 非盘中通道故障。"
    "④【A级无对象】_学习/交易计划_{master,auction,lhb,limitup,logic,theme}_*.json 全量最新日期=20260911(9/14–9/18 连续5个交易日断供); "
    "playbook.json 最新=盘中/20260907/playbook.json → 无 leg=close / take_zt 票据可触发, 条件决断=[] 属合法空(非漏写)。"
    "⑤【B级无对象】_学习/_模拟盘/盘中作战账本.json: nav=1000000.0 / 现金=1000000.0 / 持仓=[] / n_pos=0 / cash_pct=100(起算 20260813) "
    "→ 空仓即防守, 无持仓可做炸板/大幅回撤判定; 观察池唯一来源 zt_pool 最新=20260911(滞后5个交易日) → '题材批量跳水'亦无有效池对象。"
    "⑥【C级禁止】盘中禁改参数 + 无五路正式荐票 + 池滞后 + 本场零盘中留档 → 不预埋不追买不设帽。"
    "⑦【交易日核验·后验佐证(仅作日历门禁, 不作决策输入)】sentiment.core.calendar 模块缺失(ModuleNotFoundError, 同8/13起先例); "
    "佐证链: ①腾讯收盘报价时间戳=20260918161402(沪指 3911.87, +0.94%) ②THS 涨停池 20260918 含77只真实涨停(limit_up_time 11:03/13:35 等) "
    "③2026-09-18=周五, 中秋(9/25)/国庆(10/1)假期窗口在其后 → 判定 9/18 为正常交易日。"
    "上述佐证采集时刻(17:34–17:47)均晚于名义决断时点 11:00, 故仅用于'今天是不是交易日'的日历门禁, 一律不作 11:00 场次决策输入。"
    "结论: A/B/C 三级均无动作(非漏写) → 输出'心跳hb-c无动作'; 本行本身=报警动作(数据面硬缺 + 宿主停机根因)。"
)

doc = {
    "ts": now,
    "date": D,
    "session": "hb-c_1100",
    "job_id": "3e4b3b30b816",
    "execution_id": "713067e0f9a74d04ae4d64c29d8905f7",
    "scheduled_instant": "2026-09-18T11:00:00+08:00 (= 2026-09-18 11:00 CST)",
    "actual_start": "2026-09-18T17:34:04+08:00",
    "kind": "catch_up",
    "lateness": "≈6.57h (23638.1s; 名义决断时点 2026-09-18 11:00 → 实际执行 2026-09-18 17:34:04, 且已收盘)",
    "type": "expired_session_catchup_plus_intraday_chain_never_started_data_blackout",
    "level": "ALARM_ONLY",
    "scope": "intraday_chain",
    "fills": [],
    "decision_file": None,
    "detail": detail,
    "data_freshness": {
        "盘中目录": "盘中/20260918 不存在 → pulse.json/warboard.json/执行流水.jsonl/报警 jsonl 全缺",
        "realtime_channel": "盘中/20260917/realtime_ticks.jsonl (mtime 9/17 15:04) 为最后留档 → 相对 9/18 11:00 断更约1196分钟",
        "warboard_latest": "盘中/20260909/warboard.json",
        "pipeline_lock": "20260917 10076 11:52:55 (跨日残留未清)",
        "launcher_log_tail": "[15:05:36] 收盘退出 (9/17)",
        "执行流水": "全仓不存在",
    },
    "三级无对象": {
        "A_预案内": "交易计划全量 max=20260911; playbook 最新=20260907 → 无可触发票, 条件决断=[]",
        "B_防守": "盘中作战账本 nav=1000000/现金=1000000/持仓=[]/n_pos=0 → 空仓",
        "C_进攻": "无五路荐票 + 池滞后(zt_pool max=20260911) + 盘中禁改参数 → 禁止",
    },
    "根因机制发现": [
        "宿主/Hermes 9/18 02:30–17:34 停机, 全工作日 cron 全miss, 17:34 catch-up 补齐 —— 盘中链09:25从未拉起",
        "心跳缺『宿主停机跨过决断时点→只报警不预写』的统一固化护栏(本日5场心跳各自独立判断)",
        "盘中链无『当日09:26未拉起』独立哨兵: 管道未启动→连报警都不产出, 全天零报警落档",
        "pipeline.lock 9/17 收盘未清锁(跨日残留, 已在9/17出现同形态)",
        "竞价快照 cron 被 catch-up 到收盘后仍照采写档(自标污染), 建议非交易时段跳过",
    ],
    "收市后待批清单": [
        "(a) 9/18 盘中链是否收盘后离线回放/结算 —— 现有 20:30 离线预案 cron f41790d708a8 已覆盖, 建议不重复动作",
        "(b) 上述机制护栏②③④⑤是否纳入固化(按改动确认纪律: 先方案待批, 批准前零改动)",
    ],
    "后视镜边界声明": "本场执行时刻=2026-09-18 17:5x(收盘后); 全部市场信息(腾讯收盘报价 20260918161402 / THS 涨停池 17:47 / 竞价快照 17:36)均在名义决断时点 11:00 之后产生, 严格排除于决策输入之外; 决策输入仅限『应当留档而实际缺失』这一事实本身, 故本场零 fills 零预判。",
}

with open(alarm_p, "a", encoding="utf-8") as f:
    f.write(json.dumps(doc, ensure_ascii=False) + "\n")

print("WROTE", alarm_p)
print("SIZE", os.path.getsize(alarm_p))
