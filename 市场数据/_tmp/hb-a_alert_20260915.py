# -*- coding: utf-8 -*-
"""hb-a(09:40) catch_up 场次报警落档: 过期场次 + 盘中实时通道黑障。只报警禁决策。"""
import json, os, datetime

BASE = r"D:\股票数据\市场数据"
P = os.path.join(BASE, "盘中", "20260915", "报警_20260915.jsonl")
os.makedirs(os.path.dirname(P), exist_ok=True)

detail = (
    "【本场身份】心跳hb-a(09:40开盘博弈段)为catch_up补跑: jobs.json(id=ca64a4e51d42, "
    "sentiment-intraday-hb-a, cron='40 9 * * 1-5') last_dispatch.scheduled_at=2026-09-14T09:40:00+08:00, "
    "dispatched_at=2026-09-15T18:52:12.438316+08:00, lateness_seconds=119532.4(≈33.2小时), kind=catch_up "
    "-> 名义决断时间戳=2026-09-14 09:40, 实际执行=2026-09-15 19:10(决断时刻≈执行时刻的前提已不成立)。"
    "①时窗合法性硬判: 名义场次(09-14 09:40)已逾期33.2小时, 且09-14全天零盘中留档 -> 依铁律②(零后视镜)判为「过期无效场次」, 只报警禁决策。"
    "②红线硬触发(断更远超10分钟): 盘中/launcher.log mtime冻结=2026-09-11 10:00:11, 末三行「iFinD 实时 errorcode=-1010 / 取数失败 streak=30 / 连续30分钟全源失败, 报警退出」; "
    "盘中/pipeline.lock 冻结=20260911 09:14:49 -> 自09-11 09:31至本场执行(09-15 19:10)连续约4.4天(≈6340分钟)零盘中实时留档, 盘中数据通道报废状态未恢复。"
    "③输入三缺复核(全部实测): pulse.json 全仓不存在(该路径未实现, 盘中回应引擎读的是 warboard.pulse 内嵌fact字段); "
    "warboard.json 最新日期目录=盘中/20260909/warboard.json(09-15 18:52被同批catch_up重建), 无0914/0915; 执行流水.jsonl 全仓不存在(无成交流水可核); "
    "报警_20260915.jsonl 为本批catch_up(19:01)新建, 本场追加。"
    "④A级(预案内)无合法对象: 盘中/{d}/playbook.json 最新=盘中/20260907/playbook.json(断供); "
    "_学习/交易计划_*.json 全量max日期=20260911(theme: buys=[]/sells=[]) -> 无09-14专属预案, 条件决断=[]属合法空(非漏写)。"
    "⑤B级(防守)无对象: 盘中作战/state.json(09-15 18:52回写) 本金1000000/cash=1000000.0/positions=[]、净值.json(date=20260915, nav=1000000.0, n_pos=0)、"
    "次日卖出指令.json=[] -> 空仓即防守, 无炸板/大幅回撤可守; 观察池三级链断: 市场数据日目录max=20260911(zt_pool.csv max=20260911), 无0914/0915涨停池 "
    "-> 「持仓炸板/关注池题材批量跳水(≥3只2分钟内-3%)」无判定对象。"
    "⑥C级(预案外进攻)禁止: 最新总审=总审_20260911.json(总裁决结论「冰点防守, 五路一致偏谨慎; 仅保留观察, 不形成进攻仓位」) -> 防守框架未解除 + 盘中禁改参数 + 零有效票池 -> 不预埋不追买不设帽。"
    "⑦交易日校验不可执行(如实标注): 指定模块 sentiment.core.calendar 缺失(ModuleNotFoundError, 同8/13起先例); 备用 trading_calendar.load_trading_calendar() 源=_bars_cache日线并集, "
    "覆盖止于20260911, 对09-14/09-15不可判定 -> 不以猜测代校验。"
    "⑧执行日样本隔离(非本场输入): _学习/竞价快照存档/20260915.csv.gz+20260915_meta.json 采集时间=18:54:06, 来源ifind_rt, 5505条, 自标可信度「污染:>09:30盘中累计,只留档不训练」"
    " -> 收市后样本, 对名义决断时点(09-14 09:40)非合法输入, 本场零使用。"
    "⑨【机制发现·非决策】本机09-15 18:52一次catch_up风暴同时派发 hb-a/hb-b/hb-c/hb-d/hb-e/deepb 六个盘中场次(名义时刻均已逾期1-2个交易日); "
    "盘中心跳的零后视镜前提=执行时刻≈决断时刻, 补跑执行时必须做时窗合法性判定(超当日时窗=只报警不决策), 否则将污染事后样本。"
    "⑩本场结论: 无动作, fills=[]; 未写 临盘决断_20260915_0940.json(黑障+逾期下写 px/px_exec 即编造, 铁律①)。"
)

rec = {
    "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "session": "hb-a_0940",
    "level": "ALARM",
    "type": "expired_session_catchup_plus_realtime_channel_dead_data_blackout",
    "scope": "intraday_chain",
    "nominal_decision_ts": "2026-09-14 09:40",
    "exec_ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "lateness_hours": 33.2,
    "dispatch_kind": "catch_up",
    "detail": detail,
    "decision_file": None,
    "fills": [],
}

with open(P, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print("OK appended ->", P)
print("lines now =", sum(1 for _ in open(P, encoding="utf-8")))
