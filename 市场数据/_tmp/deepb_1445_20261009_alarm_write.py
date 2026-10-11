# -*- coding: utf-8 -*-
"""deepb 14:45 场 · 2026-10-09 catch_up(实跑时刻早于本职设计窗) → 只报警禁决策 ALARM 落档。
追加进 盘中/{今日}/报警_{今日}.jsonl(不覆盖, 发出版不可覆盖铁律)。"""
import json, os, datetime

BASE = r"D:\股票数据\市场数据"
D = "20261009"
alarm_p = os.path.join(BASE, "盘中", D, "报警_%s.jsonl" % D)
assert os.path.isdir(os.path.dirname(alarm_p)), "报警目录不存在: " + os.path.dirname(alarm_p)

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

detail = (
    "深场B(14:45 尾盘场)本场为 catch_up 补跑, 且实跑时刻早于本职设计窗 → 只报警禁决策, 无动作, fills=[]。"
    "①场次身份(读自 cron 真源, 非自报): job=sentiment-intraday-deepb(id=0509b31150e9, cron '45 14 * * 1-5'); "
    "executions.db 本场 id=96f764be74a44e668540ad16cf398bd2, claimed_at=2026-10-09 09:02:42; "
    "jobs.json last_dispatch={scheduled_at:2026-10-05 14:45:00, dispatched_at:2026-10-09 09:02:36, lateness≈325057s≈3天18小时18分, kind:catch_up}。"
    "②时窗合法性(本场核心纪律判定): 本场设计决断时刻=名义日 14:45(尾盘场); 实跑=2026-10-09 09:24"
    "(经网络校时 https://www.baidu.com/ Date: Fri, 09 Oct 2026 01:24:15 GMT) → 实跑时刻早于 14:45 设计窗约 5 小时 20 分, "
    "且名义排期日 10/05 为国庆假期(周一, 非交易日)。参照今日 09:21 竞价预读场判例(临盘决断_20261009_0921.json: catch_up 仅当『实跑时刻落在本职设计窗内』方可出件); "
    "本场实跑不在 14:45 窗内 → 依铁律②(零后视镜: 决断输入须 ≤ 决断时间戳, 且决策时点≈决断时点)不得产出尾盘预判/触发区间/条件价 → "
    "本场未写 临盘决断_20261009_1445.json(该发出版留待今日真 14:45 场次, next_run_at=2026-10-09T14:45:00)。"
    "③数据新鲜度红线(独立复验): a) 盘中/{今日}/pulse.json 全库 find 0 命中 = 契约项在现行库未实现, 无 ≤14:45 脉搏数据可判; "
    "b) 盘中/20261009/ 系本日 09:14:39 管道首启新建, 内容仅 auction_traj.jsonl(live 竞价段) + pipeline_alarm.jsonl + 临盘决断_20261009_0921.json, 无 warboard/playbook/执行流水; "
    "c) 盘中/{今日}/warboard.json 不存在 → 作战台持仓表态零对象; "
    "d) 执行流水.jsonl 全库 0 命中 → 『引擎已执行了什么』无独立对账源。"
    "④尾盘卖预案执行=无动作, fills=[]: 预案真源 盘中/20261009/playbook.json 缺件; 全库最近 playbook=盘中/20260930/playbook.json(date=20260930), "
    "其 buys=[]/sells=[]/cash_pct=100 → 无 leg=close / take_zt 声明, 触发判定零对象; 且该预案跨国庆长假, 按零后视镜不作本场输入。"
    "六路模拟盘(date=20260930)持仓全空 → 无票可卖(空仓自洽)。"
    "⑤持仓表态=[]: 本场无合法在持票。盘中作战 state.json(mtime 2026-10-09 09:03)载 000011 深物业A 5900股(buy_date=20261003) 系节假日误跑虚构产物"
    "(已由 _tmp/hb_b_1030_20261009_catchup_guard.json 09:08 登记, 待人工裁定), 非合法在持票 → 逐票『今日表现/浮盈/明日计划/持有或卖出理由』对象数=0(非漏写)。"
    "本场未改账本/state。"
    "⑥预收盘复盘(步骤5)=不产出: 14:45 场次之『当日第一手判断(情绪/主线/龙头/明日预案要点)』在 09:24 无 ≤14:45 盘中留档可依, 写出即编造(铁律①) → "
    "本场不写尾盘复盘判断, 留待今日真 14:45 场次。"
    "⑦机制报警(承 hb-b/hb-e 同批): a) 调度器『补跑风暴』(本日 09:02–09:05 集中补跑, 上一 durable 完成 2026-10-03T22:30 → 停摆≈5天10.5h); "
    "b) _学习/_交易日历.json 末条=20260930(10月未刷新) → 节后首日 20261009 会被误判非交易日; "
    "c) 契约命令 sentiment.core.calendar 缺包(ModuleNotFoundError, 规格漂移复现); "
    "d) 管道 pool_stale(目标日 20261008 池未落档, 降级用 20260930 池 52 只) + iFinD login rc=-2(无 Level1 盘口); "
    "e) 作战账节假日误跑持仓 000011 待人工裁定。"
    "⑧零后视镜边界: 本件全部输入(网络校时、executions.db/jobs.json、目录存在性与 mtime、pipeline_alarm/launcher.log、state.json/账本)时间戳均 ≤ 本场实跑时刻 2026-10-09 09:24; "
    "未取任何决断后数据作输入。"
)

rec = {
    "ts": ts,
    "date": D,
    "session": "deepb_1445",
    "level": "ALARM",
    "type": "catchup_executed_before_design_window + contract_inputs_missing(pulse/执行流水) + expired_playbook_cross_holiday + pending_human_review_holiday_misrun_holding",
    "scope": "intraday_chain",
    "run_kind": "catch_up",
    "scheduled_instant": "2026-10-05T14:45:00+08:00",
    "decision_file": None,
    "fills": [],
    "detail": detail,
}

n_before = sum(1 for _ in open(alarm_p, encoding="utf-8")) if os.path.exists(alarm_p) else 0
with open(alarm_p, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
n_after = sum(1 for _ in open(alarm_p, encoding="utf-8"))
print("ALARM appended:", alarm_p)
print("lines before/after =", n_before, "/", n_after)
print("ts =", ts)
