# -*- coding: utf-8 -*-
"""hb-d 13:30 心跳探针: 只读取, 不写入任何生产文件。"""
import json, os, glob, datetime as dt

ROOT = r"D:\股票数据\市场数据"
TODAY = "20260921"
D = os.path.join(ROOT, "盘中", TODAY)
NOW = dt.datetime(2026, 9, 21, 13, 30, 0)  # 名义决断时点

def p(*a): print(*a)

p("=== 1. 目录清单 ===")
for f in sorted(os.listdir(D)):
    fp = os.path.join(D, f)
    p("  %-46s %10d  %s" % (f, os.path.getsize(fp), dt.datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%H:%M:%S")))

p("\n=== 2. tick 新鲜度 / 连续性 ===")
rows = [json.loads(l) for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding="utf-8") if l.strip()]
ts = [dt.datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S") for r in rows]
p("  条数=%d  首=%s  末=%s" % (len(rows), ts[0], ts[-1]))
before = [t for t in ts if t <= NOW]
p("  <=13:30:00 的最后一条 = %s" % (before[-1] if before else None))
if before:
    gap = (NOW - before[-1]).total_seconds()
    p("  断更(相对名义13:30) = %.1fs = %.2f分钟  -> %s" % (gap, gap / 60.0, "红线内" if gap <= 600 else "超10分钟红线"))
gaps = [(ts[i + 1] - ts[i]).total_seconds() for i in range(len(ts) - 1)]
big = [(ts[i].strftime("%H:%M:%S"), ts[i + 1].strftime("%H:%M:%S"), int(gaps[i])) for i in range(len(gaps)) if gaps[i] > 90]
p("  间隔>90s 的段: %s" % (big if big else "无"))
p("  13:00 后条数 = %d" % len([t for t in ts if t.hour >= 13]))
p("  pool_date=%s pool_stale=%s pool_kind=%s" % (rows[-1]["pool_date"], rows[-1]["pool_stale"], rows[-1]["pool_kind"]))

p("\n=== 3. 预案/真源新鲜度 ===")
def newest(pat, key="date"):
    hits = sorted(glob.glob(pat))
    return hits[-1] if hits else None
checks = {
    "playbook(预案)": [os.path.join(ROOT, "..", "_学习", "playbook.json"), os.path.join(ROOT, "_学习", "playbook.json")],
    "warboard(作战台)": sorted(glob.glob(os.path.join(ROOT, "盘中", "*", "warboard.json")))[-1:],
    "总审": sorted(glob.glob(os.path.join(ROOT, "_学习", "总审_*.json")))[-1:],
    "pulse.json": glob.glob(os.path.join(ROOT, "**", "pulse.json"), recursive=True)[:3],
    "执行流水.jsonl": glob.glob(os.path.join(ROOT, "**", "执行流水.jsonl"), recursive=True)[:3],
}
for k, v in checks.items():
    p("  %-18s -> %s" % (k, v if v else "0 命中"))

p("\n=== 4. 账户状态 ===")
for name, path in [("盘中作战第七账", os.path.join(ROOT, "..", "_学习", "_模拟盘", "盘中作战", "state.json")),
                   ("盘中作战账本", os.path.join(ROOT, "..", "_学习", "_模拟盘", "盘中作战", "账本.jsonl"))]:
    if os.path.exists(path):
        if path.endswith(".json"):
            s = json.load(open(path, encoding="utf-8"))
            p("  %s: cash=%s positions=%s n=%s keys=%s" % (name, s.get("cash"), len(s.get("positions") or []), len(s.get("positions") or []), list(s.keys())[:12]))
        else:
            ls = [l for l in open(path, encoding="utf-8") if l.strip()]
            p("  %s: %d 笔, 末笔=%s" % (name, len(ls), ls[-1][:200] if ls else None))
    else:
        p("  %s: 不存在" % name)

p("\n=== 5. 今日报警已有条目 ===")
ap = os.path.join(D, "报警_%s.jsonl" % TODAY)
if os.path.exists(ap):
    for l in open(ap, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            p("  %s | %s | level=%s | fills=%s | file=%s" % (r.get("ts"), r.get("session"), r.get("level"), r.get("fills"), os.path.basename(str(r.get("decision_file")))))
else:
    p("  无")
