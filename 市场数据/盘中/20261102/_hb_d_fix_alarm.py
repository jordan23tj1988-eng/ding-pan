# -*- coding: utf-8 -*-
# 修正 报警_20261102.jsonl 最后一行：市场快照锚定 13:32:53 之前最后一帧，与 决断 文件口径一致
import json, os
os.chdir(r"D:\股票数据\市场数据")
fr = [json.loads(l) for l in open("盘中/20261102/realtime_ticks.jsonl", encoding="utf-8")]
anchor = [d for d in fr if d["ts"] <= "2026-11-02 13:32:53"][-1]
rows = {r["code"]: r for r in anchor["rows"]}
p = [r["pct"] for r in rows.values()]
snap = dict(ts="13:32", 池内红=sum(1 for x in p if x > 0), 池内绿=sum(1 for x in p if x < 0), 池内总数=len(rows),
            池内涨幅9_7=sum(1 for x in p if x >= 9.7), 池内跌3=sum(1 for x in p if x <= -3),
            pool_avg=round(sum(p) / len(p), 2), frame=anchor["ts"])
lines = open("盘中/20261102/报警_20261102.jsonl", encoding="utf-8").read().strip().split("\n")
last = json.loads(lines[-1])
assert last["session"] == "hb-d", last.get("session")
m = last["market_snapshot_intraday"]
m["ts"] = "13:32"
m["池内红"] = snap["池内红"]
m["池内绿"] = snap["池内绿"]
m["池内总数"] = snap["池内总数"]
m["池内涨幅≥9.7%"] = snap["池内涨幅9_7"]
m["池内跌≥3%"] = snap["池内跌3"]
m["池内均涨"] = snap["pool_avg"]
m["池内帧"] = anchor["ts"]
lines[-1] = json.dumps(last, ensure_ascii=False)
open("盘中/20261102/报警_20261102.jsonl", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("FIXED last line:", json.dumps(m, ensure_ascii=False))
print("lines", len(lines))
# 校验 决断 文件可解析 + 关键字段
d = json.load(open("盘中/20261102/临盘决断_20261102_1330.json", encoding="utf-8"))
print("决断", d["session"], d["ts"], d["决断"]["等级"], "fills", d["fills"], "未平差额", d["持仓快照"]["未平差额合计元"])
print("池内读数", d["池内读数"]["13:00 → 13:30"])
print("跳水", d["跳水阈值核验"]["13:00~13:32"])
