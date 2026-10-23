# -*- coding: utf-8 -*-
"""全窗口(20260615~20261022)可成交口径数据集 + 修复日/中性环境桶表"""
import os, csv, json
B = r"D:/股票数据/市场数据"; L = os.path.join(B,"_学习"); BC = os.path.join(L,"_bars_cache")
temp = json.load(open(os.path.join(L,"_市场温度表.json"), encoding="utf-8"))
dirs = sorted([d for d in os.listdir(B) if d.isdigit() and len(d)==8 and "20260615" <= d <= "20261022"])
cache = {}
def bars(code):
    if code in cache: return cache[code]
    p = os.path.join(BC, code+".csv")
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig"))) if os.path.exists(p) else []
    cache[code] = {b["date"].replace("-",""): b for b in rows}
    return cache[code]

def limit_pct(code):
    if code[:3] in ("300","301","688"): return 20.0
    if code[:2] in ("92","83","87","43"): return 30.0
    return 10.0

recs = []
for d in dirs:
    t = temp.get(d, {}).get("温度")
    if t is None: continue
    rows = list(csv.DictReader(open(os.path.join(B,d,"zt_pool.csv"), encoding="utf-8-sig")))
    nxt = None
    for r in rows:
        code = r["代码"]
        try:
            amt=float(r["封板资金"]); cmv=float(r["流通市值"]); to=float(r["换手率"])
            ft=str(r["首次封板时间"]).zfill(6); zb=int(float(r["炸板次数"])); lb=int(float(r["连板数"]))
        except Exception: continue
        if cmv <= 0: continue
        idx = bars(code)
        ds = sorted(idx.keys())
        if d not in idx: continue
        i = ds.index(d)
        if i+1 >= len(ds): continue
        b0,b1 = idx[ds[i]], idx[ds[i+1]]
        b2 = idx[ds[i+2]] if i+2 < len(ds) else None
        c0=float(b0["close"]); o1=float(b1["open"]); h1=float(b1["high"]); l1=float(b1["low"]); c1=float(b1["close"])
        if o1<=0 or c0<=0: continue
        gap=(o1/c0-1)*100; e1=(c1/o1-1)*100
        e2=(float(b2["close"])/o1-1)*100 if b2 else None
        yizi = abs(h1-l1)<1e-9 and abs(o1-h1)<1e-9
        lp = limit_pct(code)
        open_seal = (gap >= lp*0.95) and abs(o1-h1)<1e-9 and abs(c1-h1)<1e-9
        recs.append(dict(d=d, code=code, name=r["名称"], seal=amt/cmv*100, to=to, ft=ft, zb=zb, lb=lb,
                         gap=gap, e1=e1, e2=e2, yizi=yizi, open_seal=open_seal,
                         tradeable=not(yizi or open_seal), ind=r.get("所属行业",""),
                         temp=t, lp=lp))
print("全窗样本:", len(recs), "天数:", len(set(r['d'] for r in recs)))
json.dump(recs, open(os.path.join(L,"_tmp_all_recs.json"),"w",encoding="utf-8"), ensure_ascii=False)

# 环境切分
days = sorted(set(r["d"] for r in recs))
tdesc = {d: temp[d]["温度"] for d in days}
prev = {}
prevday = {}
dl = sorted([x for x in temp.keys()])
for d in days:
    idx = dl.index(d)
    prev[d] = temp[dl[idx-1]]["温度"] if idx>0 else None

fix = [d for d in days if prev[d] is not None and prev[d] < 25 and tdesc[d] >= 45]
print("\n修复日(T-1<25 ∧ T≥45):", len(fix), fix)
print("样本数:", sum(1 for r in recs if r["d"] in fix), "平均涨停数 %.1f" % (sum(1 for r in recs if r["d"] in fix)/max(1,len(fix))))
for d in fix:
    print("  %s 温度%.1f 涨停%d 次日温度%.1f" % (d, tdesc[d], sum(1 for r in recs if r['d']==d), tdesc.get(dl[dl.index(d)+1], -1) if dl.index(d)+1 < len(dl) else -1))
json.dump({"fix":fix,"prev":prev,"tdesc":tdesc}, open(os.path.join(L,"_tmp_env.json"),"w",encoding="utf-8"), ensure_ascii=False)
