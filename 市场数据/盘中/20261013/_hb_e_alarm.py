# -*- coding: utf-8 -*-
import json, io, os
P = r"D:\股票数据\市场数据\盘中\20261013\报警_20261013.jsonl"
before = sum(1 for _ in io.open(P, encoding="utf-8"))
rec = {
 "ts": "2026-10-13 14:37",
 "session": "hb-e_1430",
 "level": "ALARM",
 "type": "preplan_exit_still_unexecuted_at_1430_rootcause_located",
 "scope": "intraday_chain",
 "detail": "【第5次登记·承09:53 hb-a / 10:33 hb-b / 11:03 hb-c / 13:36 hb-d】playbook sells[0] 000011深物业A(leg=open 防守性离场, ref_px=10.11)开盘触发已达成, 至 14:30(逾290分钟)仍: ①无任何 <=14:30 合法留档行情(realtime_ticks 299帧×46票 0 命中; 全库今日落档 json/jsonl/csv/txt 扫描仅 decision/state/报警类文本含该代码, 无行情条目; 池=前日涨停池46只不含该票) → px_exec 不可得, 不写 fill(零编造); ②盘中/20261013/执行流水.jsonl 仍不存在; ③第七账 state.json positions 仍含 000011(经 10:00 与 14:30 两次引擎回写后未离场) → 离场是否已执行不可核验。★本场新增根因定位(取代前四场『引擎漏执行』的隐含判断): (a)jobs.json『盘中回应引擎-每日收盘14:57』(script=intraday_engine_runner.py, cron '57 14 * * 1-5') enabled=False —— 而该场次是引擎内唯一生成『次日卖出指令』并做持仓断板/跌停检查的场次(盘中回应引擎.py L309-327: 仅 trig=='1457' 时检查持仓并写 次日卖出指令.json); (b)引擎卖出执行仅发生在 trig∈(0925,1000) 且按 次日卖出指令.json 逐条执行(L329-343), 而该文件当前恒为 [] → 账本引擎现阶段为『只买不卖』结构; (c)playbook.json 的 sells 字段无任何模块消费(全库检索无读取方), 引擎只读 LEDGER_DIR/次日卖出指令.json → 复盘预案层离场指令与盘中账本层之间通道缺失。→ 结论: 000011 在现行结构下无任何自动卖出通道, 属通道缺失而非漏执行。建议: ①启用『盘中回应引擎-每日收盘14:57』; ②为 playbook.sells 建通道(或写入 次日卖出指令.json); ③按可复现留档价补记 000011 成交并回写第七账; ④将在持票并入实时观测池(本场持仓级风控 B级① 因无行情留档而结构上不可判定)。本场无 fill 写入。"
}
assert os.path.exists(P)
with io.open(P, "a", encoding="utf-8") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
after = sum(1 for _ in io.open(P, encoding="utf-8"))
print("报警条数", before, "->", after)
# 回读校验末条
last = json.loads(list(io.open(P, encoding="utf-8"))[-1])
print("末条 session:", last["session"], "| type:", last["type"])
