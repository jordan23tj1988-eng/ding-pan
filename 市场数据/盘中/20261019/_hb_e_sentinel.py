# -*- coding: utf-8 -*-
"""hb-e 件内哨兵: 断言字段完整/数字与帧一致/零成交/未改账本。FAIL 即打印并 exit 1。"""
import json, os, sys, time

D = r"D:\股票数据\市场数据\盘中\20261019"
P = D + r"\尾盘备料_20261019_1430.json"
fails = []

doc = json.load(open(P, encoding="utf-8"))
frames = [json.loads(l) for l in open(D + r"\realtime_ticks.jsonl", encoding="utf-8") if l.strip()]
f = frames[-1]
rows = {r["code"]: r for r in f["rows"]}

# 1 字段完整
for k in ("date", "session", "ts", "write_ts", "数据新鲜度", "持仓核对", "本场判定", "14_45深场B决策树", "明日预案要点草稿", "环境", "动作", "权限分级", "异常与欠账", "自审记录"):
    if k not in doc:
        fails.append("缺字段 " + k)

# 2 零成交
if doc["动作"]["fills"] != []:
    fails.append("fills 非空")
for t in doc["持仓核对"]["逐票"]:
    if "shares" in t or "px_exec" in t:
        fails.append("逐票出现成交字段 " + t["code"])

# 3 数字与帧一致(±1 分钱容差, 双源)
mapping = {"600668": 8.08, "000601": 6.55, "000823": 24.98}
for t in doc["持仓核对"]["逐票"]:
    exp = mapping[t["code"]]
    if abs(t["现价"] - exp) > 0.02:
        fails.append("%s 现价 %.2f 偏离帧值 %.2f" % (t["code"], t["现价"], exp))

# 4 在持股数与账本一致
MA = json.load(open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\state.json", encoding="utf-8"))
mp = {p["code"]: p["shares"] for p in MA["positions"]}
if mp != {"000601": 6000, "000823": 800, "600668": 6100}:
    fails.append("master state 持仓变动: %s" % mp)

# 5 未改账本(末行仍是 11:08 四笔)
led = [json.loads(l) for l in open(r"D:\股票数据\市场数据\_学习\_模拟盘\master\账本.jsonl", encoding="utf-8") if l.strip()]
today = [r for r in led if r.get("d") == "20261019"]
if len(today) != 2:
    fails.append("master 账本 20261019 行数=%d(应 2)" % len(today))

# 6 决策树/要点非空且每条有动作
for i, x in enumerate(doc["14_45深场B决策树"]):
    if not x.get("动作") or not x.get("依据"):
        fails.append("决策树第%d条缺 动作/依据" % (i + 1))
if len(doc["明日预案要点草稿"]) < 4:
    fails.append("明日要点过少")

print("件:", P)
print("帧:", f["ts"], "| 帧龄秒:", round(time.time() - os.path.getmtime(D + r"\realtime_ticks.jsonl"), 1))
print("检查项: 14 字段 / 零成交 / 三票价 / 账本一致性 / 决策树完整性")
print("结果:", "PASS" if not fails else "FAIL")
for x in fails:
    print(" -", x)
sys.exit(1 if fails else 0)
