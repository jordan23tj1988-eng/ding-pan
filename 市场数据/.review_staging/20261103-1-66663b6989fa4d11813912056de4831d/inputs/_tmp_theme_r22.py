import json, os, sys, importlib.util
ROOT = r"D:/股票数据/市场数据"
spec = importlib.util.spec_from_file_location("tl", os.path.join(ROOT, "题材生命周期.py"))
tl = importlib.util.module_from_spec(spec); spec.loader.exec_module(tl)
d = "20261030"
series, days = tl.load_series(d)
trans = tl.build_trans(series, days)
print("启动 out-degree N =", tl.stage_out(trans, "启动"))
print("trans from 启动:", {f"{a}→{b}":c for (a,b),c in trans.items() if a=="启动"})

rows = []
for line in series:
    dts = [dt for dt in sorted(series[line].keys()) if dt in days]
    for i in range(1, len(dts)):
        prev, prev_stage = tl._prev_of(series[line], dts, i)
        stage, trap = tl.classify(series[line][dts[i]], prev, prev_stage)
        if prev_stage == "启动":
            rows.append({"线": line, "日": dts[i-1], "次日": dts[i], "前阶段": prev_stage,
                         "次日阶段": stage, "次日宽": series[line][dts[i]]["w"],
                         "次日高": series[line][dts[i]]["h"], "陷阱": trap})
print("逐笔总数", len(rows))
for r in sorted(rows, key=lambda x: (x["日"], x["线"])):
    print(f"{r['日']} {r['线']:<22} →{r['次日']} 次阶段={r['次日阶段']:<3} 宽{r['次日宽']} 高{r['次日高']} 陷阱={r['陷阱']}")
json.dump(rows, open(os.path.join(ROOT,"_学习/_tmp_商航启动逐笔.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
