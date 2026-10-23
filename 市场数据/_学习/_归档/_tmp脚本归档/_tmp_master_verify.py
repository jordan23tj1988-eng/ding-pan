import json, io, os, re, csv, glob
B = r"D:\股票数据\市场数据\_学习"
D = r"D:\股票数据\市场数据"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

print("=" * 20, "1) 一进二率 定义追溯(各路原文)")
for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    s = json.dumps(L(os.path.join(B, f"{r}判断_20260826.json")), ensure_ascii=False)
    for m in re.finditer(r".{60}一进二.{90}", s):
        print(f"[{r}]", m.group(0).replace("\\n", " "))
print()
print("=" * 20, "2) 独立复算 一进二率 候选口径")
T = L(os.path.join(B, "_市场温度表.json"))
t26, t25 = T["20260826"], T["20260825"]
g26, g25 = t26["梯队"], t25["梯队"]
print("0826梯队", g26, "0825梯队", g25)
print("口径a 今日2板/昨日1板 =", g26.get("2"), "/", g25.get("1"), "=", round(100*g26["2"]/g25["1"], 1), "%")
print("口径b 今日二板加/昨日1板 =", t26["二板加"], "/", g25.get("1"), "=", round(100*t26["二板加"]/g25["1"], 1), "%")
print("口径c 今日2板/(昨涨停-昨二板加) =", g26.get("2"), "/", t25["涨停数"]-t25["二板加"], "=", round(100*g26["2"]/(t25["涨停数"]-t25["二板加"]), 1), "%")
print()
print("=" * 20, "3) 资金温度(lhb单源判据 3分位)")
p = os.path.join(B, "_资金温度.json")
if os.path.exists(p):
    z = L(p)
    rows = z if isinstance(z, list) else z.get("明细") or z.get("序列") or z
    if isinstance(rows, list):
        for r in rows[-3:]:
            print(json.dumps(r, ensure_ascii=False)[:400])
    else:
        print(json.dumps(z, ensure_ascii=False)[:600])
else:
    print("缺失", p)
print()
print("=" * 20, "4) limitup 执1max 独立复算(涨停质量荐票_20260826)")
p = os.path.join(B, "涨停质量荐票_20260826.json")
if os.path.exists(p):
    q = L(p)
    det = q.get("明细") or q.get("全池") or []
    print("明细只数", len(det), "键", list(det[0].keys())[:20] if det else "")
    vals = [(d.get("预测执1胜率"), d.get("预测执1均涨"), d.get("名称"), d.get("命中数")) for d in det if isinstance(d.get("预测执1胜率"), (int, float))]
    vals.sort(reverse=True)
    print("执1胜率Top5:", vals[:5])
    import statistics
    print("执1胜率 max=", vals[0][0], " 中位=", round(statistics.median([v[0] for v in vals]), 2), " 均=", round(statistics.mean([v[0] for v in vals]), 2))
    print("执1均涨 max=", max(v[1] for v in vals), " 均=", round(statistics.mean([v[1] for v in vals]), 3))
    print("命中数≥3只数=", sum(1 for v in vals if (v[3] or 0) >= 3), " 命中≥1只数=", sum(1 for v in vals if (v[3] or 0) >= 1))
    print("执1胜率>50%只数=", sum(1 for v in vals if v[0] > 50))
else:
    print("缺失", p, "→ 目录候选:", [os.path.basename(x) for x in glob.glob(os.path.join(B, "*质量*20260826*"))])
