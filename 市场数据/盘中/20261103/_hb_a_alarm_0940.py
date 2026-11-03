# -*- coding: utf-8 -*-
import json, os, time
D = r"D:\股票数据\市场数据\盘中\20261103"
p = os.path.join(D, "报警_20261103.jsonl")
rec = {
 "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
 "session": "hb-a",
 "date": "20261103",
 "level": "ALARM",
 "type": "execution_chain_zero_receipt_and_0921_open_window_missed",
 "scope": "09:21 场 A 腿 600299 2.0%/600259 1.0%（09:25 落门内、窗口错过、0 敞口）＋ 09:44 场 3 笔执1逾期清出卖腿（601188×4200/002365×1500/001287×400，名义 40,244 元）",
 "detail": "①09:21 场 cron 09:22:33 迟启、09:31 落盘，错过 09:25 执行窗；09:25 机械终值 600299 gap +1.36%、600259 gap +3.85% 均在门内（应买 2.0%/1.0%），但盘中/20261103 无 pulse.json、无 warboard.json、无 执行流水.jsonl → 引擎 0 行回执，两腿实际 0 敞口；截至 09:44 按开盘价计的机会成本约 +483 元（600299 +1.71%、600259 +2.44%），未计入净值。②账本 _学习/_模拟盘/master/state.json（mtime 11-02 21:16）仍持 3 只执1 逾期腿：601188（buy_date 20261030，执1 应 10/30 收盘了结，逾期 2 日）、002365/001287（buy_date 20261102，state.reason 原文『当日收盘平（执 1）』，逾期 1 日），合计名义 40,244 元＝估算净值 4.09%；其中 601188 的 open 卖腿已在 11/2 09:44 发过、引擎 0 承接，002365/001287 因『夜版 playbook 19:48 生成 / 账本 21:16 入账』时序错位而根本没有卖腿。09:44 hb-a 对三只补发 fill_sell（601188@3.33 / 002365@12.19 / 001287@19.93，决断价均不低于各自今日开盘价）。",
 "root_cause": "盘中成交回执链路缺失（pulse/warboard/执行流水 自 20261020 起长期不产出）＋ 夜版计划生成早于当日入账导致新建仓无次日卖腿 ＋ 09:21 cron 迟启错过开盘执行窗；心跳无写引擎回执权限，只能报警与交接。",
 "evidence": [
  "盘中/20261103/临盘决断_20261103_0921.json#落盘说明（09:22:33 迟启、错过 09:25 窗）",
  "盘中/20261103/临盘决断_20261103_0940.json#fills(3)/#预案A腿核销",
  "盘中/20261103/_hb_a_frameA.json（px 帧 20261103094412）",
  "盘中/20261103/_hb_a_frameB.json（px_exec 帧 20261103094518）",
  "盘中/20261103/realtime_ticks.jsonl 末帧 2026-11-03 09:44:07（14 帧）",
  "_学习/_模拟盘/master/state.json mtime 2026-11-02 21:16 positions=3",
  "_学习/_模拟盘/master/账本.jsonl 末 8 行（11-02 21:16 仅 buy 002365/001287，无 sell）",
  "盘中/20261102/playbook.json#sells[2]（601188 open 卖腿原文）"
 ],
 "market_snapshot_intraday": {
  "ts": "09:44",
  "池内红": 84, "池内绿": 39, "池内总数": 125, "池内涨幅>=9.7%": 16, "池内跌<=-3%": 8, "池内均涨": 2.49,
  "近三窗2分钟跳水达标(>=3pp)": [0, 0, 1],
  "涨停": 27, "跌停": 3, "涨停池炸板": "9/27=33.3%", "连板分布": {"1": 13, "2": 11, "3": 1, "4": 2},
  "否决门": "跌停>=70 且 涨停<60 → 未触发"
 },
 "positions": [
  {"code": "601188", "name": "龙江交通", "shares": 4200, "last": 3.34, "pct": -0.60, "px_exec": 3.33, "cost": 3.47, "ret_pct": -3.79, "overdue_days": 2},
  {"code": "002365", "name": "永安药业", "shares": 1500, "last": 12.16, "pct": -2.09, "px_exec": 12.19, "cost": 12.61, "ret_pct": -3.62, "overdue_days": 1},
  {"code": "001287", "name": "中电港", "shares": 400, "last": 19.94, "pct": -1.09, "px_exec": 19.93, "cost": 20.25, "ret_pct": -1.58, "overdue_days": 1}
 ]
}
with open(p, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("APPENDED", p)
for i, l in enumerate(open(p, encoding="utf-8"), 1):
    d = json.loads(l)
    print(i, d["ts"], d["session"], d["type"], "OK")
