# -*- coding: utf-8 -*-
"""MA-20261023-03 v2：炸板次数 × 执1/执2 + 机制(次日开盘gap) + 连板分层。"""
import json, os, csv
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
BC = os.path.join(L, "_bars_cache")
pool = json.load(open(os.path.join(L, "_ths_zt_pool.json"), encoding="utf-8"))
days = sorted(pool.keys())

def limit_pct(code):
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
                try: out.append((x["date"], float(x["open"]), float(x["close"])))
                except Exception: pass
    cache[code] = out; return out

def newstat(): return {"n":0,"win":0,"sum":0.0,"kn":0,"kwin":0,"ksum":0.0,"miss":0,"gap":0.0,
                       "n2":0,"win2":0,"sum2":0.0}

B = [0,1,2,3,4,5,6]
stat = {b: newstat() for b in B}
strat = {"首板": {b: newstat() for b in B}, "≥2板": {b: newstat() for b in B}}
tot = newstat()
cnt = {"all":0,"fwd":0}

def add(s, ret, ret2, gap, tradeable):
    s["n"] += 1; s["sum"] += ret; s["gap"] += gap
    if ret > 0: s["win"] += 1
    if tradeable:
        s["kn"] += 1; s["ksum"] += ret
        if ret > 0: s["kwin"] += 1
    else:
        s["miss"] += 1
    if ret2 is not None:
        s["n2"] += 1; s["sum2"] += ret2
        if ret2 > 0: s["win2"] += 1

for d in days:
    for r in pool[d]:
        cnt["all"] += 1
        code = str(r["code"]).zfill(6)
        op = r.get("open_num")
        b = 0 if op is None else (6 if int(op) >= 6 else int(op))
        bb = bars(code)
        if not bb: continue
        idx = next((i for i,(dt,o,c) in enumerate(bb) if dt.replace("-","") == d), None)
        if idx is None or idx + 1 >= len(bb): continue
        d1,o1,c1 = bb[idx+1]
        ret2 = None
        if idx + 2 < len(bb): ret2 = (bb[idx+2][2]/o1 - 1)*100.0
        prev_c = bb[idx][2]
        if o1 <= 0 or c1 <= 0 or prev_c <= 0: continue
        cnt["fwd"] += 1
        ret = (c1/o1 - 1)*100.0
        gap = (o1/prev_c - 1)*100.0
        tradeable = gap < limit_pct(code) - 0.1
        add(stat[b], ret, ret2, gap, tradeable); add(tot, ret, ret2, gap, tradeable)
        s = "首板" if (r.get("high_days") in ("首板", None) or "天" not in str(r.get("high_days",""))) else "≥2板"
        add(strat[s][b], ret, ret2, gap, tradeable)

P=lambda a,b: round(100.0*a/b,1) if b else None
A=lambda s,n: round(s/n,2) if n else None

print("样本: 全池%d, 有前向%d (%.1f%%)" % (cnt["all"], cnt["fwd"], 100.*cnt["fwd"]/cnt["all"]))
print("基准: n=%d 执1 %s%%/%s | 执2 n=%d %s%%/%s | 均gap %s" % (
    tot["n"], P(tot["win"],tot["n"]), A(tot["sum"],tot["n"]), tot["n2"], P(tot["win2"],tot["n2"]),
    A(tot["sum2"],tot["n2"]), A(tot["gap"],tot["n"])))
tbl=[]
print("\n炸档 n | 执1胜率 执1均收 | 均gap | 可成交n 胜率 均收 | 一字% | 执2n 胜率 均收")
for b in B:
    s=stat[b]
    row={"炸板次数":("≥6" if b==6 else b),"n":s["n"],"执1胜率":P(s["win"],s["n"]),"执1均收":A(s["sum"],s["n"]),
         "均gap":A(s["gap"],s["n"]),"可成交子集n":s["kn"],"可成交胜率":P(s["kwin"],s["kn"]),
         "可成交均收":A(s["ksum"],s["kn"]),"一字不可成交n":s["miss"],
         "一字占比":round(100.*s["miss"]/s["n"],1) if s["n"] else None,
         "执2n":s["n2"],"执2胜率":P(s["win2"],s["n2"]),"执2均收":A(s["sum2"],s["n2"])}
    tbl.append(row); print(row)

print("\n== 连板分层 ==")
for k in ["首板","≥2板"]:
    print(k)
    for b in B:
        s=strat[k][b]
        if s["n"]<1: continue
        print(" 炸%s n=%d 执1 %s%%/%s 可成交n=%d %s%%/%s 执2n=%d %s%%/%s" % (
            ("≥6" if b==6 else b), s["n"], P(s["win"],s["n"]), A(s["sum"],s["n"]),
            s["kn"], P(s["kwin"],s["kn"]), A(s["ksum"],s["kn"]), s["n2"], P(s["win2"],s["n2"]), A(s["sum2"],s["n2"])))

def merge(dd, bs):
    o=newstat()
    for b in bs:
        for k,v in dd[b].items(): o[k]+=v if not isinstance(v,float) else v
    return {"n":o["n"],"胜率":P(o["win"],o["n"]),"均收":A(o["sum"],o["n"]),"均gap":A(o["gap"],o["n"]),
            "可成交n":o["kn"],"可成交胜率":P(o["kwin"],o["kn"]),"可成交均收":A(o["ksum"],o["kn"]),
            "执2n":o["n2"],"执2胜率":P(o["win2"],o["n2"]),"执2均收":A(o["sum2"],o["n2"])}
print("\n炸≤3(封板质量门):", merge(stat,[0,1,2,3]))
print("炸≥4:", merge(stat,[4,5,6]))
print("炸≥5(可成交正桶):", merge(stat,[5,6]))
print("首板∧炸≥4:", merge(strat["首板"],[4,5,6]))
print("≥2板∧炸≥4:", merge(strat["≥2板"],[4,5,6]))
print("≥2板∧炸≤3:", merge(strat["≥2板"],[0,1,2,3]))

json.dump({"窗口":[days[0],days[-1]],"样本":{"全池":cnt["all"],"有前向":cnt["fwd"]},
  "基准":{"n":tot["n"],"执1胜率":P(tot["win"],tot["n"]),"执1均收":A(tot["sum"],tot["n"]),
          "执2胜率":P(tot["win2"],tot["n2"]),"执2均收":A(tot["sum2"],tot["n2"]),"均gap":A(tot["gap"],tot["n"])},
  "table":tbl,
  "合并":{"炸≤3":merge(stat,[0,1,2,3]),"炸≥4":merge(stat,[4,5,6]),"炸≥5":merge(stat,[5,6]),
          "首板∧炸≥4":merge(strat["首板"],[4,5,6]),"≥2板∧炸≥4":merge(strat["≥2板"],[4,5,6]),
          "≥2板∧炸≤3":merge(strat["≥2板"],[0,1,2,3])}},
  open(os.path.join(L,"_ma03_v2.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("\nWROTE _ma03_v2.json")
