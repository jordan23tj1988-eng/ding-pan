# -*- coding: utf-8 -*-
r"""验证iFind切源.py — 阶段B切源三连验证(仅宿主运行,零正式产物, 2026-07-18 #011)
①混市场快照含北交所 ②混市场日K含北交所 ③概念全清单(取20260717历史日验HQ路)。
报告: _学习/ifind_验证切源_{d}.json"""
import os, sys, json, datetime
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
import ifind_source as ifs

rep = {"start": str(datetime.datetime.now())}
ok_all = True

# ① 混市场快照(修复前会丢920305)
q = ifs.spot(["000002", "600519", "920305"])
got = sorted(set(str(x)[:6] for x in q["thscode"])) if q is not None else []
ok1 = got == ["000002", "600519", "920305"]
rep["1_混市场快照"] = {"ok": ok1, "got": got}
print(("[√] " if ok1 else "[X] ") + "混市场快照含北交所 " + str(got))

# ② 混市场日K
day = datetime.date.today()
b = ifs.daily_bars(["000002", "920305"], (day - datetime.timedelta(days=9)).strftime("%Y-%m-%d"), day.strftime("%Y-%m-%d"))
gotb = sorted(set(str(x)[:6] for x in b["thscode"])) if b is not None else []
ok2 = gotb == ["000002", "920305"]
rep["2_混市场日K"] = {"ok": ok2, "got": gotb, "rows": 0 if b is None else len(b)}
print(("[√] " if ok2 else "[X] ") + "混市场日K含北交所 " + str(gotb))

# ③ 概念全清单(历史日=0717, 走HQ路; 不写任何csv)
import importlib.util
spec = importlib.util.spec_from_file_location("gnpm", os.path.join(BASE, "概念排名.py"))
gn = importlib.util.module_from_spec(spec); spec.loader.exec_module(gn)
rows = gn.fetch_ifind_concepts("20260717")
ok3 = bool(rows) and len(rows) >= 300
rep["3_概念全清单0717"] = {"ok": ok3, "count": len(rows) if rows else 0,
                          "top5": sorted(rows, key=lambda x: x["涨幅"] if x["涨幅"] is not None else -999, reverse=True)[:5] if rows else []}
print(("[√] " if ok3 else "[X] ") + "概念全清单0717 count=%s" % (len(rows) if rows else 0))
if rows:
    for r in rep["3_概念全清单0717"]["top5"]:
        print("   ", r["名称"], r["涨幅"])

ok_all = ok1 and ok2 and ok3
rep["end"] = str(datetime.datetime.now()); rep["ok_all"] = ok_all
outp = os.path.join(BASE, "_学习", "ifind_验证切源_%s.json" % day.strftime("%Y%m%d"))
with open(outp, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print(("[√√] 三连全过, iFind主源就绪" if ok_all else "[X] 有未过项,沙箱读报告修") + "  报告: " + outp)
ifs.logout()
