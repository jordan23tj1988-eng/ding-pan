# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
recs = json.load(open(os.path.join(L,"_tmp_all_recs.json"), encoding="utf-8"))

def stats(rs):
    if not rs: return None
    m = sum(r["e1"] for r in rs)/len(rs)
    return (len(rs), m, 100*sum(1 for r in rs if r["e1"]>0)/len(rs))

def table(tag, rs):
    full = stats(rs)
    print("\n%s  全池 n=%d 均%+.3f%% 胜率%.1f%%" % (tag, full[0], full[1], full[2]))
    for nm, cond in [("M-04原口径(gap>=9.5&open==high)", lambda r: not (r["yizi"] or (r["gap"]>=9.5 and abs(r["gap"])>=0) ))]:
        pass
    # 两种口径直接按字段区分
    def loose_ok(r):
        return not (r["yizi"] or (r["gap"] >= 9.5 and r["code"] and _oh(r)))
    # 需要未定义的 helper; 改为读取保存的两个标记: open_seal(严格) 与原口径无法复原 → 用 gap>=9.5 and 非yizi 近似?
    return full

print("注意: 严格标记=open_seal(open==high==close & gap>=0.95*limit); 原口径 M-04=gap>=9.5 & open==high")
# 重建原口径标记: 需要 high==open 但未保存; 用 open_seal 与 yizi 之外无法判断 → 直接重算
import csv
B = r"D:/股票数据/市场数据"; BC = os.path.join(L,"_bars_cache")
cache={}
def bars(code):
    if code in cache: return cache[code]
    p=os.path.join(BC, code+".csv")
    cache[code] = {b["date"].replace("-",""): b for b in csv.DictReader(open(p, encoding="utf-8-sig"))} if os.path.exists(p) else {}
    return cache[code]
for r in recs:
    b = bars(r["code"]); ds = sorted(b.keys())
    if r["d"] not in b: continue
    i = ds.index(r["d"]); b1 = b[ds[i+1]]
    o,h,l,c = float(b1["open"]),float(b1["high"]),float(b1["low"]),float(b1["close"])
    r["loose_seal"] = (r["gap"] >= 9.5 and abs(o-h) < 1e-9)
    r["tr_loose"] = not (r["yizi"] or r["loose_seal"])

def show(tag, rs):
    if not rs: print(tag, "empty"); return
    f = stats(rs); tl = [r for r in rs if r["tr_loose"]]; ts = [r for r in rs if r["tradeable"]]
    sl = stats(tl); ss = stats(ts)
    print("  %-22s 全池n=%3d 均%+.3f%% 胜%4.1f%% | 原口径剔%2d n=%3d 均%+.3f%% 胜%4.1f%% | 严格剔%2d n=%3d 均%+.3f%% 胜%4.1f%%" % (
        tag, f[0], f[1], f[2], len(rs)-len(tl), sl[0], sl[1], sl[2], len(rs)-len(ts), ss[0], ss[1], ss[2]))

print("\n=== 全窗(4747) ===")
show("强封>=4%", [r for r in recs if r["seal"]>=4])
show("强封>=4%×炸0", [r for r in recs if r["seal"]>=4 and r["zb"]==0])
show("薄封<0.5%", [r for r in recs if r["seal"]<0.5])
print("\n=== 冰点(825) ===")
cold=[r for r in recs if r["temp"]<25]
show("强封>=4%", [r for r in cold if r["seal"]>=4])
show("强封>=4%×炸0", [r for r in cold if r["seal"]>=4 and r["zb"]==0])
show("强封>=4%×炸>=1", [r for r in cold if r["seal"]>=4 and r["zb"]>=1])
show("薄封<0.5%×换手3-10%", [r for r in cold if r["seal"]<0.5 and 3<=r["to"]<=10])
show("首封>14:30×首板", [r for r in cold if r["ft"]>"143000" and r["lb"]==1])
