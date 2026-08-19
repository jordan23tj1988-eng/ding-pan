# -*- coding: utf-8 -*-
"""hb-c 11:00 心跳哨兵·核验脚本 (2026-08-18)"""
import os, json, sys, glob

BASE = r"D:/股票数据/市场数据"

# 1) 交易日校验(替代 sentiment.core.calendar): 走留档日历
sys.path.insert(0, BASE)
try:
    import trading_calendar as tc
    cal = tc.load_trading_calendar()
    in_cal = "20260818" in cal if cal else None
    print("CAL_CHECK: 20260818 in trading_calendar =", in_cal, "| cal_size =", len(cal) if cal else None)
    if cal:
        print("CAL_TAIL:", cal[-5:])
except Exception as e:
    print("CAL_CHECK: trading_calendar fallback FAILED:", repr(e))

# 2) pipeline.lock
try:
    print("LOCK:", open(os.path.join(BASE, "盘中", "pipeline.lock"), encoding="utf-8", errors="replace").read().strip())
except Exception as e:
    print("LOCK FAIL:", repr(e))

# 3) 盘中/20260818/ 目录内容
ddir = os.path.join(BASE, "盘中", "20260818")
print("TODAY_DIR:", sorted(os.listdir(ddir)) if os.path.isdir(ddir) else "MISSING")
for f in sorted(os.listdir(ddir)):
    fp = os.path.join(ddir, f)
    print("  FILE:", f, "| mtime:", __import__("time").strftime("%H:%M:%S", __import__("time").localtime(os.path.getmtime(fp))), "| size:", os.path.getsize(fp))

# 4) 关键文件存在性
for name in ["pulse.json", "warboard.json", "执行流水.jsonl", "realtime_ticks.jsonl", "临盘决断_20260818_1100.json"]:
    hit = glob.glob(os.path.join(BASE, "盘中", "**", name), recursive=True)
    print("EXIST:", name, "->", hit if hit else "MISSING")

# 5) warboard 现状(含错位目录)
wbf = os.path.join(BASE, "盘中", "20260817", "warboard.json")
if os.path.isfile(wbf):
    print("WB: mtime =", __import__("time").strftime("%Y-%m-%d %H:%M:%S", __import__("time").localtime(os.path.getmtime(wbf))))
    d = json.load(open(wbf, encoding="utf-8"))
    print("WB TOP KEYS:", list(d.keys())[:25])
    for k in ("date", "judgment", "stage", "n_pos", "cash", "account", "summary"):
        if k in d:
            v = d[k]
            print("WB.", k, "=", json.dumps(v, ensure_ascii=False)[:400])
    # 递归找 positions / responses
    def walk(o, prefix=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("positions", "n_pos", "cash", "judgment", "responses", "优先成交", "trigger_hits", "triggers"):
                    print("WB.", prefix + k, "=", json.dumps(v, ensure_ascii=False)[:500])
                walk(v, prefix + k + ".")
        elif isinstance(o, list):
            for i, v in enumerate(o[:5]):
                walk(v, prefix + "[%d]." % i)
    walk(d)
else:
    print("WB: 20260817/warboard.json MISSING")

# 6) launcher.log 尾部
lf = os.path.join(BASE, "盘中", "launcher.log")
if os.path.isfile(lf):
    lines = open(lf, encoding="utf-8", errors="replace").read().splitlines()
    print("LOG_TAIL:")
    for ln in lines[-6:]:
        print("  ", ln)

# 7) 报警 jsonl
af = os.path.join(BASE, "盘中", "报警_20260818.jsonl")
if os.path.isfile(af):
    rows = [json.loads(x) for x in open(af, encoding="utf-8").read().splitlines() if x.strip()]
    print("ALARM_ROWS:", len(rows))
    for r in rows:
        print("  ", r.get("ts"), "|", r.get("session"), "|", r.get("type"), "|", r.get("detail", "")[:120])
