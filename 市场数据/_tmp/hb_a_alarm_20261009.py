# -*- coding: utf-8 -*-
"""hb-a(09:40) 心跳场次 · 2026-10-09 catch_up 早跑 —— 只报警禁决策, 不出 发版 文件。
   落点: (1) 追加 盘中/20261009/报警_20261009.jsonl ; (2) _tmp/hb_a_0940_20261009_catchup_guard.json 审计留痕。
   不写 盘中/20261009/临盘决断_20261009_0940.json(该发版须由本日真 09:40 场次出具, next_run_at=2026-10-09T09:40:00+08:00)。"""
import json, os, datetime, statistics

BASE = "D:/股票数据/市场数据"
D = "20261009"
dd = BASE + "/盘中/" + D
now = datetime.datetime.now()
ts = now.strftime("%Y-%m-%d %H:%M:%S")

# ---- 竞价留档事实(截至写档) ----
recs = [json.loads(l) for l in open(dd + "/auction_traj.jsonl", encoding="utf-8").read().strip().split("\n")]
last = recs[-1]
pcts = [r.get("pct") for r in last["rows"] if isinstance(r.get("pct"), (int, float))]
pool = {r["code"]: r for r in last["rows"]}
o = pool.get("000011", {})

detail = (
 "本场为 hb-a(09:40 开盘博弈段)的调度器 catch_up 补跑, 且实跑时刻早于本职设计窗 → 只报警禁决策, 无动作, fills=[]。"
 "①场次身份(读自 cron 真源, 非自报): job=sentiment-intraday-hb-a(id=ca64a4e51d42, cron '40 9 * * 1-5', enabled=true); "
 "executions.db 本场 id=b4fd935e22874c3c9f234582117fb382, scheduled_instant=2026-10-05T01:40:00+00:00(=2026-10-05 09:40 CST, 该日为国庆假期周一·休市), "
 "claimed_at=2026-10-09T09:02:42.61+08:00, started_at=09:02:43.51; jobs.json last_dispatch={scheduled_at:2026-10-05T09:40:00+08:00, "
 "dispatched_at:2026-10-09T09:02:36.57, lateness_seconds:343356.6, kind:catch_up} → 迟到≈3天23小时22分。属调度器国庆停摆(约5天+)后 09:02–09:05 一次性补跑风暴之一"
 "(同批 = preread/hb-a/hb-b/hb-c/hb-d/hb-e 六个盘中 job 的 10/05 排期一并重放), 非单场故障。"
 "②时窗合法性(本场核心纪律判定): 本场设计决断时刻=09:40(开盘博弈段); 实跑 2026-10-09 09:0x–09:2x(写档 " + ts + "), 开市前(09:30 前), 实跑时刻早于 09:40 设计窗 ≈15 分钟。"
 "参照本日既定判例(临盘决断_20261009_0921.json 竞价预读场『catch_up 仅当实跑时刻落在本职设计窗内方可出件』; _tmp/deepb_1445_20261009_catchup_guard.json 同规则) → "
 "本场实跑不在 09:40 窗内, 依铁律②(零后视镜)与『只报警禁决策』不得产出本场决断/触发区间/条件价 → 本场未写 临盘决断_20261009_0940.json"
 "(该发版须由本日真 09:40 场次出具, jobs.json next_run_at=2026-10-09T09:40:00+08:00; 本场提前占位会触发『发版不可覆盖』致真场次无法出件)。"
 "③数据新鲜度(独立复验): a) 盘中/{今日}/pulse.json 全库 0 命中 = 契约项在现行库本就未实现, 无脉搏数据可判; "
 "b) 盘中/20261009/ 系本日 09:14:39 管道首启新建, 内容仅 auction_traj.jsonl(live 竞价段 09:15:01→" + last["ts"][11:] + ", src=腾讯, n=52, 间隔 20-21s) + pipeline_alarm.jsonl + 临盘决断_20261009_0921.json, "
 "无 warboard/playbook/执行流水; c) 全库无 执行流水.jsonl → 『引擎已执行了什么』无独立对账源; d) 09:30 连续段(realtime_ticks.jsonl)与 09:25 竞价终值均不存在 → 『开盘后』实时价/炸板/承接量 全 null。"
 "④预案: 盘中/20261009/playbook.json 缺件; 全库最近 playbook=盘中/20260930/playbook.json(date=20260930, mtime 2026-10-01 12:28, buys=[]/sells=[]/cash_pct=100/五路 route_plans buys_count 全=0), "
 "跨国庆长假, 按零后视镜不作本场输入 → A级在册对象=空集。"
 "⑤B级持仓表态=无合法对象: 唯一在册票 000011 深物业A(盘中作战 state.json: 5900股@10.11, buy_date=20261003) 已由同批 hb-b 场(09:08, _tmp/hb_b_1030_20261009_catchup_guard.json) 首报判定为"
 "『节假日误跑虚构产物(待人工裁定)』—— 依据: buy_date=20261003 为周六+假期休市不可能成交、10/03 两场临盘决断均载『非交易日·零 fills』、playbook buys=[] 且深物业A 仅在 watch 观察项(无 plan 授权); "
 "本场承接该判定, 不重复论证、不擅自改账; 故 B级『持仓炸板/大幅回撤』零合法对象。"
 "(旁证: 000011 竞价 09:15:21–09:21:26 连续 7 tick 恒 latest=10.91/-9.98(前收参考 12.12), 09:21:46 起撬板回升 -9.90→-8.17→-8.00 —— 与 9/29-9/30 两连板后断板一致; "
 "因持仓非法定, 该读数仅列诊断, 不构成 B级 卖出依据, 亦不代人工裁定。) "
 "⑥C级=无: 开市前无行情; 依『盘中禁改参数/无数据不追买』及 20261003 总审『维持空仓防守』, 不下单。"
 "⑦机制报警(承同批, 增量登记): a) 调度器『补跑风暴』(09:02–09:05 集中补跑, 上一 durable 完成约 2026-10-03T22:30 → 停摆≈5天10.5h); "
 "b) _学习/_交易日历.json 末条=20260930(10月未刷新) → 节后首日 20261009 会被朴素日历误判非交易日; c) 契约命令 sentiment.core.calendar 缺包(ModuleNotFoundError, 规格漂移复现, 续记第 8+ 次); "
 "d) 管道 pool_stale(目标日 20261008 池未落档, 降级用 20260930 池 52 只) + iFinD login rc=-2(无 Level1 盘口); e) 作战账节假日误跑持仓 000011 待人工裁定。"
 "⑧零后视镜边界: 本件全部输入(executions.db/jobs.json、目录存在性与 mtime、auction_traj.jsonl ≤" + last["ts"] + "、pipeline_alarm/launcher.log、state.json/账本/净值)时间戳均 ≤ 本件写档时刻 " + ts + "; "
 "未使用任何决断后信息; 本场零 fills、零价位、零区间 → 后视镜风险=零。"
)

alarm = {
 "ts": ts, "date": D, "session": "hb-a_0940", "level": "ALARM",
 "type": ("catchup_executed_before_design_window + contract_inputs_missing(pulse/执行流水) + expired_playbook_cross_holiday + "
          "pool_stale + ifind_rc-2_no_L1 + spec_drift_calendar + pending_human_review_holiday_misrun_holding"),
 "scope": "intraday_chain", "run_kind": "catch_up",
 "scheduled_instant": "2026-10-05T09:40:00+08:00",
 "decision_file": None, "fills": [],
 "本场动作": "无 A/B/C 级动作(fills=[]) → 依 cron 真源 prompt step4 未建决断文件(盘中/20261009/临盘决断_20261009_0940.json 不存在, 亦未创建, 留待本日真 09:40 场次); 本行属链路实证增量+异常留档, 非数据红线报警。",
 "detail": detail,
}
p_alarm = dd + "/报警_" + D + ".jsonl"
with open(p_alarm, "a", encoding="utf-8") as f:
    f.write(json.dumps(alarm, ensure_ascii=False) + "\n")
print("APPENDED", p_alarm, os.path.getsize(p_alarm))

guard = {
 "date": D, "session": "hb-a_0940", "run_kind": "catch_up",
 "scheduled_instant": "2026-10-05T09:40:00+08:00",
 "execution_ts": ts + " (北京时间; 同日 09:08 已由同批 hb-b 场网络校时佐证)",
 "lateness": "≈3天23小时22分 (排期 10/05 09:40 → 实跑 10/09 09:02:42 认领 / 本件 " + ts + "); jobs.json last_dispatch.lateness_seconds=343356.6, kind=catch_up",
 "性质": "★心跳留档·非决策输入·非发出版 —— 本场实跑早于 09:40 设计窗且开市前无行情, 无动作, 未写任何 临盘决断_20261009_0940.json; 发版留待本日真 09:40 场次。本件仅为审计留痕。",
 "交易时段状态": "开市前 (" + ts + " < 09:30), 无当日连续段行情(仅集合竞价段 auction_traj.jsonl)",
 "步骤1_交易日判定": {
   "契约指定命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str;...\" → ModuleNotFoundError: No module named 'sentiment'",
   "本机等效真源": "D:/股票数据/市场数据/trading_calendar.py + _学习/_交易日历.json(5409 交易日, 末条=20260930) → 日历未刷至10月, 不能反证",
   "判定": "2026-10-09 = 周五, 国庆(10/01-10/08)后首个交易日; 本日管道实活(pipeline.lock='20261009 22676 09:14:39' + 52票真实竞价 tick), 复盘链健康巡检 target=20261009 → 判定为交易日"
 },
 "步骤2_数据核验": {
   "auction_traj.jsonl": "存在, live 竞价段 09:15:01→" + last["ts"][11:] + ", src=腾讯, n=52, 间隔 20-21s",
   "pulse.json": "全库 0 命中(契约项现行库未实现)",
   "warboard.json(今日目录)": "不存在(最新=盘中/20260930/warboard.json, mtime 今日 09:03:35, 但 date 字段=20260930, 为旧交易日重渲染)",
   "playbook.json(今日目录)": "不存在(最近=盘中/20260930/playbook.json, buys=[]/cash_pct=100, 跨长假不作输入)",
   "执行流水.jsonl": "全库 0 命中",
   "realtime_ticks.jsonl": "不存在(09:30 连续段未启)",
   "结论": "无脉冲/预案/引擎流水/连续段 → 无法建立 A/B/C 级决断"
 },
 "步骤3_判断": {
   "A级(预案内trigger)": "无输入; 本日 playbook 缺件, 节前 9/30 版 buys=[] → 零对象",
   "B级(预案外防守)": "唯一在册票 000011 深物业A 已由同批 hb-b 场(09:08)判定为『节假日误跑虚构产物(待人工裁定)』→ 非合法在持票 → 零合法对象(不借该票出卖出指令, 避免跨日账实污染)",
   "C级(预案外进攻)": "开市前无行情 + 盘中禁改参数 → 不下单",
   "动作": "无", "fills": []
 },
 "★异常报警(承接 hb-b 09:08 首报, 不重复/不擅改)": "作战账节假日误跑持仓 000011 深物业A(shares 5900, buy_px 10.11, buy_date 20261003) 待人工裁定; 本场未改 state.json/账本, 仅转述并要求收市后统一处置。",
 "竞价段读数(诊断, 非决策输入)": "锁定末条 " + last["ts"] + "(src=腾讯, n=52): 中位 " + ("%.2f" % statistics.median(pcts)) + "% / 均值 " + ("%.2f" % statistics.mean(pcts)) + "% / 涨停(≥9.8) " + str(sum(1 for x in pcts if x >= 9.8)) + " / 跌停(≤-9.8) " + str(sum(1 for x in pcts if x <= -9.8)) + " / 跌≤-5% " + str(sum(1 for x in pcts if x <= -5)) + "; 000011 " + str(o.get("latest")) + "/" + str(o.get("pct")) + "%。",
 "零后视镜边界": "全部输入时间戳 ≤ " + ts + "; 零 fills/零价位/零区间 → 无后视污染。",
 "动作汇总": "无动作(fills=[]) —— 只报警禁决策。",
}
p_guard = BASE + "/_tmp/hb_a_0940_20261009_catchup_guard.json"
assert not os.path.exists(p_guard), "已存在: " + p_guard
with open(p_guard, "w", encoding="utf-8") as f:
    json.dump(guard, f, ensure_ascii=False, indent=1)
print("WROTE", p_guard, os.path.getsize(p_guard))
print("FINAL_NOW", ts)
