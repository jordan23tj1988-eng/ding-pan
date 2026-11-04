# -*- coding: utf-8 -*-
"""MA-20261030-05 ①: 医药族/AI应用族 线级 启动→* 逐笔(族口径合并), 零后视镜 <=20261102"""
import json, sys, importlib.util, os
sys.stdout.reconfigure(encoding='utf-8')
src = "D:/股票数据/市场数据/题材生命周期.py"
spec = importlib.util.spec_from_file_location("lc", src)
lc = importlib.util.module_from_spec(spec); spec.loader.exec_module(lc)

series, days = lc.load_series("20261102")
FAM = {
 "医药医疗": "医药医疗", "医药/创新药": "医药医疗", "医药生物": "医药医疗", "创新药": "医药医疗",
 "AI应用/传媒": "AI应用/传媒", "AI应用/软件": "AI应用/传媒", "AI应用": "AI应用/传媒",
}
# 合并族
merged = {}
for line, s in series.items():
    fam = FAM.get(line, line)
    for dt, row in s.items():
        tgt = merged.setdefault(fam, {}).setdefault(dt, {"w":0,"h":0,"sb":0,"el":0,"mom":None,"jj":None})
        tgt["w"] += row["w"]; tgt["h"] = max(tgt["h"], row["h"]); tgt["sb"] += row["sb"]; tgt["el"] += row["el"]
all_days = sorted(merged.get("医药医疗", {}).keys())
res = {}
for fam in ("医药医疗", "AI应用/传媒"):
    s = merged[fam]; dts = sorted(s)
    trans = {l:{} for l in [fam]}
    rows = []
    for i, dt in enumerate(dts):
        prev, prev_stage = lc._prev_of(s, dts, i)
        st, trap = lc.classify(s[dt], prev, prev_stage)
        rows.append((dt, st, trap, s[dt]["w"], s[dt]["h"], s[dt]["mom"], s[dt]["jj"], prev_stage))
    trans = {}
    for i in range(1, len(rows)):
        a, b = rows[i-1][1], rows[i][1]
        trans[(a,b)] = trans.get((a,b),0)+1
    out = {f"{a}->{b}": n for (a,b),n in trans.items() if a=="启动"}
    tot = sum(out.values())
    res[fam] = {"启动出度N": tot, "启动→*": dict(sorted(out.items(), key=lambda x:-x[1])), "全部转移": {f"{a}->{b}":n for (a,b),n in sorted(trans.items(), key=lambda x:-x[1])[:12]}}
    print("\n=== %s 启动出度N=%d ===" % (fam, tot))
    for k,v in sorted(out.items(), key=lambda x:-x[1]):
        print("  %s %d (%.1f%%)" % (k, v, 100*v/tot if tot else 0))
    print("  最近20日行:", [(r[0],r[1],r[3],r[4]) for r in rows[-6:]])
json.dump(res, open("D:/股票数据/市场数据/_学习/_tmp_医药AI应用启动逐笔_20261102.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n写入 _学习/_tmp_医药AI应用启动逐笔_20261102.json")
