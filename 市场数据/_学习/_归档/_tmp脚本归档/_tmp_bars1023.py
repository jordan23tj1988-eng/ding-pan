# -*- coding: utf-8 -*-
import os, csv, json, statistics
L = r"D:/股票数据/市场数据/_学习"; BC = os.path.join(L,"_bars_cache")
def load(code):
    p = os.path.join(BC, code+".csv")
    if not os.path.exists(p): return None
    return {r["date"].replace("-",""): r for r in csv.DictReader(open(p, encoding="utf-8-sig"))}
out=[]
for code in ("002724","603278","003021","300561","002242","603370","601091","002812"):
    b = load(code)
    if not b: out.append(code+" no bars"); continue
    ds = sorted(b)
    for d in ("20261021","20261022","20261023","20261026"):
        if d in b:
            r = b[d]; o,h,l,c = float(r["open"]),float(r["high"]),float(r["low"]),float(r["close"])
            i = ds.index(d); pc = float(b[ds[i-1]]["close"]) if i>0 else None
            gap = (o/pc-1)*100 if pc else None
            e1 = (c/o-1)*100
            t1 = (c/pc-1)*100 if pc else None
            out.append("%s %s O%.2f H%.2f L%.2f C%.2f prevC%.2f gap%+.2f%% 执1(收/开)%+.2f%% T1(收/昨收)%+.2f%%" % (
                code, d, o,h,l,c,(pc or 0),(gap or 0),e1,(t1 or 0)))
out.append("")
# 昨池 33 只 执1 均值（可成交 & 全池）
rows22 = list(csv.DictReader(open(r"D:/股票数据/市场数据/20261022/zt_pool.csv", encoding="utf-8-sig")))
vals=[]; miss=[]
for r in rows22:
    b = load(r["代码"])
    if not b or "20261023" not in b: miss.append(r["代码"]); continue
    o,c = float(b["20261023"]["open"]), float(b["20261023"]["close"])
    vals.append((c/o-1)*100)
out.append("昨池33只 20261023 执1: n=%d 均%+.3f%% 中位%+.3f%% 胜率%.1f%% 缺bar%d" % (
    len(vals), sum(vals)/len(vals), statistics.median(vals), 100*sum(1 for v in vals if v>0)/len(vals), len(miss)))
# 002242 20261023
b = load("002242")
if b and "20261023" in b:
    r = b["20261023"]; ds=sorted(b); i=ds.index("20261023"); pc=float(b[ds[i-1]]["close"])
    out.append("002242 20261023: prevC%.2f O%.2f C%.2f gap%+.2f%% 执1%+.2f%% ; 20261026 O%.2f C%.2f" % (
        pc, float(r["open"]), float(r["close"]), (float(r["open"])/pc-1)*100, (float(r["close"])/float(r["open"])-1)*100,
        float(b["20261026"]["open"]), float(b["20261026"]["close"])))
open(os.path.join(L,"_tmp_out3_1023.txt"),"w",encoding="utf-8").write("\n".join(out))
print("ok")
