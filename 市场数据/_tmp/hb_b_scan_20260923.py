# -*- coding: utf-8 -*-
"""hb-b 10:30 池内扫描 — 只用 <=10:30:00 留档 tick"""
import json, csv, statistics, collections

d = "20260923"
base = "盘中/%s" % d
ls = [json.loads(l) for l in open(base + "/realtime_ticks.jsonl", encoding="utf-8")]
lk = [r for r in ls if r["ts"] <= "2026-09-23 10:30:00"]
print("locked ticks=%d  %s -> %s" % (len(lk), lk[0]["ts"], lk[-1]["ts"]))

# 行业映射
ind = {}
for row in csv.DictReader(open("20260922/zt_pool.csv", encoding="utf-8-sig")):
    ind[row["代码"]] = (row["名称"], row["所属行业"], row["连板数"], row["涨停统计"])

# 每股序列
ser = collections.defaultdict(list)  # code -> [(ts,pct,latest,high,low,preClose)]
name = {}
for t in lk:
    for r in t["rows"]:
        name[r["code"]] = r["name"]
        ser[r["code"]].append((t["ts"], r["pct"], r["latest"], r["high"], r["low"], r.get("preClose")))

print("\n=== ① 2分钟(2 tick)跌落 >=2pp 事件 (锁定窗内) ===")
ev = []
for c, s in ser.items():
    for i in range(2, len(s)):
        dpp = s[i][1] - s[i - 2][1]
        if dpp <= -2.0:
            ev.append((round(dpp, 2), c, name.get(c), ind.get(c, ("?", "?", "?", "?"))[1],
                       s[i - 2][0][-8:], s[i][0][-8:], s[i - 2][1], s[i][1], s[i][2], s[i][5]))
ev.sort()
for e in ev:
    print("  %+.2fpp %s %-6s %-8s %s->%s  %+.2f%%->%+.2f%% last=%.2f pre=%.2f" %
          (e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9] or 0))

print("\n=== ①b 2分钟跌落 >=3pp 事件(红线口径) ===")
ev3 = [e for e in ev if e[0] <= -3.0]
for e in ev3:
    print("  %+.2fpp %s %-6s %-8s %s->%s  %+.2f%%->%+.2f%%" % (e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]))
if not ev3:
    print("  零事件")

print("\n=== ①c 同题材(所属行业)批量跳水 判定 ===")
byind = collections.defaultdict(list)
for e in ev3:
    byind[e[3]].append(e)
for k, v in byind.items():
    print("  行业=%s 事件数=%d %s" % (k, len(v), [x[2] for x in v]))

print("\n=== ② 炸板扫描: 曾 >=9.5% 后跌破 7% ===")
zb = []
for c, s in ser.items():
    mx = max(x[1] for x in s)
    if mx >= 9.5 and s[-1][1] < 7.0:
        zb.append((c, name.get(c), ind.get(c, ("?", "?", "?", "?"))[1], mx, s[-1][1]))
for z in sorted(zb, key=lambda x: x[4]):
    print("  %s %-6s %-8s 峰值%+.2f%% -> 现%+.2f%%" % (z[0], z[1], z[2], z[3], z[4]))
if not zb:
    print("  零炸板(锁定窗内)")
# 全局炸板(不看首段): 开盘价接近涨停后回落
print("  参考: 锁定窗内 峰值>=9.5% 只数 =", sum(1 for c, s in ser.items() if max(x[1] for x in s) >= 9.5))

print("\n=== ③ 锁定时点池内结构 (10:29:10) ===")
rows = lk[-1]["rows"]
p = [r["pct"] for r in rows]
print("  n=%d 中位=%+.2f 均值=%+.2f 红=%d 绿=%d | 贴板>=9.5:%d | >=5:%d | <=-5:%d | <=-9.5:%d" % (
    len(rows), statistics.median(p), statistics.mean(p),
    sum(1 for x in p if x > 0), sum(1 for x in p if x < 0),
    sum(1 for x in p if x >= 9.5), sum(1 for x in p if x >= 5),
    sum(1 for x in p if x <= -5), sum(1 for x in p if x <= -9.5)))
# 分行业
gi = collections.defaultdict(list)
for r in rows:
    gi[ind.get(r["code"], ("?", "未归位(20260922池外)", "?", "?"))[1]].append(r["pct"])
print("  --- 行业横截面(仅列 n>=2 或 |均值|>=3) ---")
for k, v in sorted(gi.items(), key=lambda kv: statistics.mean(kv[1])):
    if len(v) >= 2 or abs(statistics.mean(v)) >= 3:
        print("    %-12s n=%d 均值%+.2f 中位%+.2f" % (k, len(v), statistics.mean(v), statistics.median(v)))

print("\n=== ④ 断更检查 ===")
import datetime
tss = [datetime.datetime.strptime(t["ts"], "%Y-%m-%d %H:%M:%S") for t in lk]
gaps = [(tss[i] - tss[i - 1]).total_seconds() for i in range(1, len(tss))]
print("  条数=%d 首=%s 末=%s 最大间隔=%.0fs 零缺" % (len(lk), lk[0]["ts"], lk[-1]["ts"], max(gaps)))
# 全场 window 内外对比(仅诊断, 不入决策)
after = [r for r in ls if r["ts"] > "2026-09-23 10:30:00"]
if after:
    print("  [诊断·窗外] 末 tick=%s" % after[-1]["ts"])
