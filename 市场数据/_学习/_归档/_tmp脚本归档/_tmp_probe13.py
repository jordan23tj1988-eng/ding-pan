# -*- coding: utf-8 -*-
import os, json, csv
B = r"D:/股票数据/市场数据"; L = os.path.join(B,"_学习"); BC = os.path.join(L,"_bars_cache")
rows = list(csv.DictReader(open(os.path.join(B,"20261023","zt_pool.csv"), encoding="utf-8-sig")))
def bars(code):
    p = os.path.join(BC, code+".csv")
    if not os.path.exists(p): return {}
    return {b["date"].replace("-",""): b for b in csv.DictReader(open(p, encoding="utf-8-sig"))}

print("=== 连板≥2 明细 ===")
for r in rows:
    lb = int(float(r["连板数"]))
    if lb >= 2:
        seal = float(r["封板资金"])/float(r["流通市值"])*100
        print("  %s %s %d板 首封%s 炸%d 封单%.3f%% 换手%.2f%% 流通%.1f亿 成交%.2f亿 %s" % (
            r["代码"], r["名称"], lb, str(r["首次封板时间"]).zfill(6), int(float(r["炸板次数"])), seal,
            float(r["换手率"]), float(r["流通市值"])/1e8, float(r["成交额"])/1e8, r["所属行业"]))

print("\n=== 昨日荐票/持仓 今日执行 ===")
for code, nm, px22 in [("603370","华新精科",None), ("003021","兆威机电",None), ("601091","沈鼓集团",None), ("002242","九阳股份",22.02)]:
    b = bars(code)
    d0 = b.get("20261022"); d1 = b.get("20261023"); d2 = b.get("20261026")
    if not (d0 and d1):
        print(code, nm, "缺bar"); continue
    c0=float(d0["close"]); o1=float(d1["open"]); c1=float(d1["close"]); h1=float(d1["high"]); l1=float(d1["low"])
    gap=(o1/c0-1)*100; e1=(c1/o1-1)*100
    yz = abs(h1-l1)<1e-9 and abs(o1-h1)<1e-9
    print("  %s %s 昨收%.2f 今开%.2f gap%+.2f%% 今收%.2f 高%.2f 低%.2f 执1%+.2f%% 一字=%s" % (code,nm,c0,o1,gap,c1,h1,l1,e1,yz))
    if code=="002242":
        print("     持仓买入价%.2f → 开盘卖出收益%+.2f%%（若按开盘）" % (px22, (o1/px22-1)*100))

print("\n=== 今日 换手/封单 分档件数 ===")
import statistics as st
seals=[float(r["封板资金"])/float(r["流通市值"])*100 for r in rows]
tos=[float(r["换手率"]) for r in rows]
print("封单比 均值%.3f%% 中位%.3f%% | 0.5-1%%:%d 1-2%%:%d 2-4%%:%d" % (sum(seals)/len(seals), st.median(seals),
      sum(1 for s in seals if 0.5<=s<1), sum(1 for s in seals if 1<=s<2), sum(1 for s in seals if 2<=s<4)))
print("20cm只数:", sum(1 for r in rows if r["代码"][:3] in ("300","301","688")))
print("北交所:", sum(1 for r in rows if r["代码"][:2] in ("92","83","87","43")))
print("成交额合计%.1f亿 中位%.2f亿" % (sum(float(r["成交额"]) for r in rows)/1e8, st.median([float(r["成交额"])/1e8 for r in rows])))
