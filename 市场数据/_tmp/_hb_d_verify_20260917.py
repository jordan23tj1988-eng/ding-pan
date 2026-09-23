# -*- coding: utf-8 -*-
"""hb-d(2026-09-17 13:30 午后延续段) 现场核验: 只读, 不写任何生产文件。"""
import json, os, glob, datetime, io, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BASE = r"D:\股票数据\市场数据"
D = "20260917"
INTRA = os.path.join(BASE, "盘中")
DD = os.path.join(INTRA, D)
# 决断时点=任务名义 13:30 (scheduler 本实例 in-window)
DEC = datetime.datetime(2026, 9, 17, 13, 30, 0)
now = datetime.datetime.now()
out = {}
out["now"] = now.strftime("%Y-%m-%d %H:%M:%S")
out["decision_ts_nominal"] = "2026-09-17 13:30"

# 1. 交易日校验
try:
    from sentiment.core.calendar import is_trading_day, today_str
    out["trading_day_check"] = {"module": "ok", "value": bool(is_trading_day(today_str()))}
except Exception as e:
    out["trading_day_check"] = {"module": "unavailable", "err": type(e).__name__ + ": " + str(e)}
alt = os.path.join(BASE, "trading_calendar.py")
out["trading_day_check"]["alt_module_exists"] = os.path.exists(alt)
cal = os.path.join(BASE, "_学习", "_交易日历.json")
if os.path.exists(cal):
    try:
        c = json.load(open(cal, encoding="utf-8"))
        days = c if isinstance(c, list) else c.get("days") or c.get("交易日") or []
        out["trading_day_check"]["calendar_cache_last"] = str(days[-1])[:10] if days else None
        out["trading_day_check"]["calendar_cache_len"] = len(days)
    except Exception as e:
        out["trading_day_check"]["calendar_cache_err"] = str(e)

# 2. 实时留档新鲜度 (只用 <= 决断时点已落档行判定)
tf = os.path.join(DD, "realtime_ticks.jsonl")
ticks = []
if os.path.exists(tf):
    with io.open(tf, encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                ticks.append(json.loads(ln))
            except Exception:
                pass
pre = [t for t in ticks if datetime.datetime.strptime(t["ts"], "%Y-%m-%d %H:%M:%S") <= DEC]
last_pre = pre[-1] if pre else None
last_all = ticks[-1] if ticks else None
out["realtime_ticks"] = {
    "path": "盘中/%s/realtime_ticks.jsonl" % D,
    "n_total": len(ticks),
    "n_at_or_before_decision": len(pre),
    "first_ts": ticks[0]["ts"] if ticks else None,
    "last_at_or_before_decision_ts": last_pre["ts"] if last_pre else None,
    "last_ts_any": last_all["ts"] if last_all else None,
    "gap_min_at_decision": round((DEC - datetime.datetime.strptime(last_pre["ts"], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60.0, 1) if last_pre else None,
    "src": last_all.get("src") if last_all else None,
    "pool_date": last_all.get("pool_date") if last_all else None,
    "pool_stale": last_all.get("pool_stale") if last_all else None,
    "n_rows": last_all.get("n") if last_all else None,
}

# 3. 契约三件套 + 执行流水
def exists(p):
    return {"path": p, "exists": os.path.exists(p)}
out["contract_artifacts"] = {
    "pulse": exists(os.path.join(DD, "pulse.json")),
    "warboard_today": exists(os.path.join(DD, "warboard.json")),
    "执行流水_today": exists(os.path.join(DD, "执行流水.jsonl")),
}
out["global_scan"] = {
    "pulse_any": sorted(glob.glob(os.path.join(INTRA, "*", "pulse.json"))),
    "warboard_all": sorted(glob.glob(os.path.join(INTRA, "*", "warboard.json"))),
    "执行流水_any": sorted(glob.glob(os.path.join(INTRA, "**", "执行流水*.jsonl"), recursive=True))[:10],
}

# 4. 预案真源 (playbook / 交易计划 / 总审)
pb = sorted(glob.glob(os.path.join(INTRA, "*", "playbook.json")))
out["playbook_max"] = pb[-1] if pb else None
plans = {}
for f in glob.glob(os.path.join(BASE, "_学习", "交易计划_*.json")):
    key = os.path.basename(f).replace("交易计划_", "").replace(".json", "")
    if key in ("master",) or "_" in key:
        pass
    parts = key.rsplit("_", 1)
    leg, d = (parts[0], parts[1]) if len(parts) == 2 else (key, "")
    if d.isdigit() and len(d) == 8:
        plans.setdefault(leg, []).append(d)
out["plan_max_by_leg"] = {k: sorted(v)[-1] for k, v in sorted(plans.items())}
out["plan_today_files"] = sorted(glob.glob(os.path.join(BASE, "_学习", "交易计划_*_%s.json" % D)))
zs = sorted(glob.glob(os.path.join(BASE, "_学习", "总审_*.json")))
out["总审_max"] = zs[-1] if zs else None
if zs:
    try:
        j = json.load(open(zs[-1], encoding="utf-8"))
        out["总审_max_brief"] = {k: j.get(k) for k in ("date", "档位", "档", "confidence", "置信度", "结论", "summary") if k in j}
    except Exception as e:
        out["总审_max_brief"] = {"err": str(e)}

# 5. 账本
for nm, p in [("盘中作战", os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "state.json")),
              ("master", os.path.join(BASE, "_学习", "_模拟盘", "master", "state.json"))]:
    try:
        j = json.load(open(p, encoding="utf-8"))
        out.setdefault("accounts", {})[nm] = {
            "cash": j.get("cash"), "n_pos": len(j.get("positions") or []),
            "positions": j.get("positions"), "nav": j.get("nav"), "mtime": datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        out.setdefault("accounts", {})[nm] = {"err": str(e)}
nd = os.path.join(BASE, "_学习", "_模拟盘", "盘中作战", "次日卖出指令.json")
try:
    out["次日卖出指令"] = json.load(open(nd, encoding="utf-8"))
except Exception as e:
    out["次日卖出指令"] = {"err": str(e)}

# 6. 报警/管道
al = os.path.join(DD, "pipeline_alarm.jsonl")
if os.path.exists(al):
    out["pipeline_alarm_tail"] = [json.loads(l) for l in io.open(al, encoding="utf-8", errors="replace") if l.strip()][-3:]
al2 = os.path.join(DD, "报警_%s.jsonl" % D)
if os.path.exists(al2):
    rows = [json.loads(l) for l in io.open(al2, encoding="utf-8", errors="replace") if l.strip()]
    out["报警_today"] = {"n": len(rows), "sessions": [r.get("session") for r in rows],
                         "last_ts": rows[-1].get("ts"), "last_type": rows[-1].get("type")}
lk = os.path.join(INTRA, "pipeline.lock")
if os.path.exists(lk):
    out["pipeline_lock"] = io.open(lk, encoding="utf-8").read().strip()
lg = os.path.join(INTRA, "launcher.log")
if os.path.exists(lg):
    lines = io.open(lg, encoding="utf-8", errors="replace").read().splitlines()
    out["launcher_tail"] = lines[-3:]
    out["launcher_firstline"] = lines[0] if lines else None
out["data_daily_max"] = sorted(glob.glob(os.path.join(BASE, "数据", "每日", "*")))[-1] if glob.glob(os.path.join(BASE, "数据", "每日", "*")) else None
out["盘中_dirs_max"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(INTRA, "2026*")))[-1]

print(json.dumps(out, ensure_ascii=False, indent=1))
