# -*- coding: utf-8 -*-
"""心跳 hb-b (10:30趋势确认段) catch_up补跑 落档: 仅报警行(追加), 不写临盘决断。
铁律: 零后视镜(名义决断时间戳=2026-09-14 10:30, 实际执行=2026-09-15 19:xx) /
      数据断更>10分钟=只报警禁决策 / 发出版不可覆盖(追加不覆盖) / 黑障下写条件价即编造"""
import json, os, datetime

D_EXEC = "20260915"          # 执行日(文件归属日, 与同批 hb-c 落档一致)
NOMINAL = "2026-09-14 10:30"  # 名义决断时间戳(jobs.json last_dispatch.scheduled_at)
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
alarm_p = os.path.join(BASE, "盘中", D_EXEC, "报警_%s.jsonl" % D_EXEC)
dec_p = os.path.join(BASE, "盘中", D_EXEC, "临盘决断_%s_1030.json" % D_EXEC)

assert os.path.isdir(os.path.dirname(alarm_p)), "报警目录不存在: " + os.path.dirname(alarm_p)
assert not os.path.exists(dec_p), "发出版已存在, 不可覆盖: " + dec_p

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
n_before = sum(1 for _ in open(alarm_p, encoding="utf-8")) if os.path.exists(alarm_p) else 0

detail = (
    "【本场身份】心跳hb-b(10:30趋势确认段)为 catch_up补跑: jobs.json last_dispatch.scheduled_at=2026-09-14T10:30:00, "
    "dispatched_at=2026-09-15T18:52:12, lateness_seconds=116532.4(≈32.4小时), kind=catch_up, fire_claim.at=2026-09-15T19:00:24 -> "
    "名义决断时间戳=%s, 实际执行=%s。"
    "①时窗合法性硬判: 名义场次时窗已逾期32.4小时(9/14 10:30 -> 9/15 19时), 且9/14全天零盘中留档 -> 依铁律②(零后视镜)判定为"
    "「过期无效场次」, 只报警禁决策; 不生成任何 fills(黑障+逾期下写 px_exec 即编造, 铁律①)。"
    "②链路断更(远>10分钟红线): 盘中/launcher.log mtime冻结=2026-09-11 10:00:11(末行「连续30分钟全源失败, 报警退出」, "
    "9/11 09:31:00起 iFinD实时 errorcode=-1010 streak=1..30); 盘中/pipeline.lock 冻结=20260911 09:14:49 -> 自9/11 09:31至本场执行 "
    "连续约4.4天零实时留档, 盘中数据通道报废状态未恢复。"
    "③三缺复核: 盘中/20260914 目录不存在; 盘中/20260915 于本场前不存在(19:01 由同批 catch_up 的 hb-c 场次新建); "
    "pulse.json 全仓无此文件(该路径未实现, 本系统脉搏=warboard 内嵌 fact 快照字段, warboard_build.py 产出) -> 无脉冲新鲜度可核, 等同断更; "
    "warboard.json 无0914/0915(最新内容=盘中/20260909/warboard.json, 18:52 被另一补跑重建); 执行流水.jsonl 全仓不存在 -> 无成交流水可核。"
    "④A级无合法对象: 盘中/{d}/playbook.json 最新=盘中/20260907/playbook.json(连续断供); _学习/交易计划_*.json 全量 max日期=20260911; "
    "无9/14专属预案 -> 条件决断=[] 属合法空(非漏写)。"
    "⑤B级防守无对象: 盘中作战 state.json(20260915 18:52 回写) 本金1000000/cash=1000000.0/positions=[]、净值.json(date=20260915, nav=1000000.0, n_pos=0)、"
    "次日卖出指令.json=[]、master/state.json positions=[] cash=1009012.5 -> 空仓即防守, 无炸板/大幅回撤可守; "
    "观察池链: 市场数据日目录最后=20260911(zt_pool.csv max=20260911), 无9/14/9/15涨停池 -> 「持仓炸板/题材批量跳水(≥3只2分钟内-3%)」条件无判定对象。"
    "⑥C级预案外进攻禁止: 最新总审=总审_20260911.json(未解除防守框架) + 盘中禁改参数 + 零有效票池 -> 不预埋不追买不设帽。"
    "⑦执行日样本隔离(非本场输入): _学习/竞价快照存档/20260915_meta.json 采集时间=18:54:06, ifind_rt 5505条, 自标「污染:>09:30盘中累计,只留档不训练」"
    " -> 收市后样本, 对名义决断时点(9/14 10:30)非合法输入, 本场零使用。"
    "⑧交易日校验: 指定模块 sentiment.core.calendar 缺失(ModuleNotFoundError, 同8/13起先例, 默认python与项目venv均无 sentiment 包); 佐证链: "
    "2026-09-14=周一、2026-09-15=周二, 中秋(9/25)/国庆(10/1)假期窗口在其后 -> 9/14为正常交易日, 但当日数据链全断(市场数据日目录、盘中目录、计划文件均无9/14)。"
    "⑨【机制发现·非决策】本机 18:52 一次 catch_up 风暴同时派发 hb-a/hb-b/hb-c/hb-d/hb-e/deepb 六个盘中场次(名义时刻已逾期1-2个交易日); "
    "盘中心跳的零后视镜前提是「执行时刻≈决断时刻」, 补跑执行必须对盘中场次做时窗合法性判定(超出当日时窗=只报警不决策), 否则事后补写即样本污染; "
    "本场处理与同批 hb-c(19:01 落档 盘中/20260915/报警_20260915.jsonl, 未写临盘决断)一致。"
    "⑩后视镜边界声明: 本场不产生任何市场判断, 全部陈述均为9/15 19时对「9/14 10:30 场次已逾期且通道黑障」的事件留档; "
    "本行非决策输出, 不构成任何买卖依据。"
    "本场结论: 无动作, fills=[], 仅报警; 未写 临盘决断_20260915_1030.json(时窗逾期32.4h + 连续4.4天黑障, 写即编造, 铁律①)。"
    "收市后待批清单(盘中禁改, 按改动确认纪律先出方案): ①catch_up 时窗闸门(盘中场次逾期>当日时窗即自动降级为 ALARM_ONLY, 建议硬编码) "
    "> ②iFinD实时-1010根因(自9/4起同型, 通道连续报废) > ③每日数据链 StockDailyChain/下载落盘断更(9/12起无新数据日) "
    "> ④playbook 生成器断供 > ⑤sentiment.core.calendar 交易日校验模块缺失 > ⑥pulse.json 路径未实现(名义存在实则无) "
    "> ⑦引擎判断流水 ts 月前缀错标/跨日串卡。"
)

doc = {
    "ts": now,
    "session": "hb-b_1030",
    "level": "ALARM",
    "type": "expired_session_catchup_plus_realtime_channel_dead_data_blackout",
    "scope": "intraday_chain",
    "nominal_decision_ts": NOMINAL,
    "exec_ts": now,
    "lateness_hours": 32.4,
    "dispatch_kind": "catch_up",
    "detail": detail,
    "decision_file": None,
    "fills": [],
}

with open(alarm_p, "a", encoding="utf-8") as f:
    f.write(json.dumps(doc, ensure_ascii=False) + "\n")

n_after = sum(1 for _ in open(alarm_p, encoding="utf-8"))
print("OK alarm appended: %s" % alarm_p)
print("lines %d -> %d" % (n_before, n_after))
print("decision NOT written: %s (exists=%s)" % (dec_p, os.path.exists(dec_p)))
print("ts=%s" % now)
