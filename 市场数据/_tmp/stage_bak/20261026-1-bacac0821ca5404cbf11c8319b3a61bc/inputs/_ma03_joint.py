# -*- coding: utf-8 -*-
"""联合格：炸板次数 × 净买占比桶 → 执1（20260615~20261023 本地日目录 lhb.csv∩zt_pool.csv）。"""
import json, os, csv, glob
BASE = os.path.dirname(os.path.abspath(__file__)); L = os.path.join(BASE, "_学习"); BC = os.path.join(L, "_bars_cache")

def lp(code):
    if code[:3] in ("300", "301", "688", "689"): return 20.0
    if code[0] in ("4", "8") or code.startswith("92"): return 30.0
    return 10.0
cache = {}
def bars(code):
    if code in cache: return cache[code]
    p = os.path.join(BC, code + ".csv"); out = []
    if os.path.isfile(p):
        with open(p, encoding="utf-8-sig") as f:
            for x in csv.DictReader(f):
                try: out.append((x["date"].replace("-", ""), float(x["open"]), float(x["close"])))
                except Exception: pass
    cache[code] = out; return out

def is_interval(t): return any(k in t for k in ("连续", "累计", "区间", "严重异常"))
cell = {}
def add(k, ret):
    c = cell.setdefault(k, {"n":0,"w":0,"s":0.0}); c["n"]+=1; c["s"]+=ret
    if ret>0: c["w"]+=1

ndays=0; nrec=0
for d in sorted(os.listdir(BASE)):
    if not (d.isdigit() and len(d)==8 and d>="20260615"): continue
    pl, ll = os.path.join(BASE,d,"zt_pool.csv"), os.path.join(BASE,d,"lhb.csv")
    if not (os.path.isfile(pl) and os.path.isfile(ll)): continue
    ndays+=1
    try:
        zt = {r["代码"]: r for r in csv.DictReader(open(pl, encoding="utf-8-sig"))}
        lh = {r["代码"]: r for r in csv.DictReader(open(ll, encoding="utf-8-sig")) if not is_interval(r["上榜原因"])}
    except Exception: continue
    for code, z in zt.items():
        if code not in lh: continue
        op = z["炸板次数"]
        try: fz = 0 if op in ("", None) else int(op)
        except Exception: continue
        fzb = fz if fz <= 1 else 2
        try: pct = float(lh[code]["净买额占总成交比"])
        except Exception: continue
        pb = "≤0" if pct<=0 else ("0-10" if pct<10 else ("10-20" if pct<=20 else ">20"))
        bb = bars(code)
        if not bb: continue
        i = next((i for i,(dt,o,c) in enumerate(bb) if dt==d), None)
        if i is None or i+1 >= len(bb): continue
        nxt = bb[i+1]
        if nxt[1] <= 0 or nxt[2] <= 0: continue
        nrec += 1
        add((fzb,pb), (nxt[2]/nxt[1]-1)*100)
        add(("ALL",pb), (nxt[2]/nxt[1]-1)*100)
        add((fzb,"ALL"), (nxt[2]/nxt[1]-1)*100)

print("天数=%d 记录=%d" % (ndays, nrec))
for k in sorted(cell, key=lambda x: (str(x[0]), str(x[1]))):
    c = cell[k]
    print(k, "n=%d 胜率=%.1f%% 均收=%.2f" % (c["n"], 100*c["w"]/c["n"], c["s"]/c["n"]))
json.dump({"天数":ndays,"记录":nrec,"格":{"%s|%s"%k:{"n":v["n"],"胜率":round(100*v["w"]/v["n"],1),"均收":round(v["s"]/v["n"],2)} for k,v in cell.items()}},
          open(os.path.join(L,"_ma03_joint.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
