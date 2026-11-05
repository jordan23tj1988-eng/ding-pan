# -*- coding: utf-8 -*-
"""荐票格统计: 3板/首板 × 温度/封单/首封 的执1与闸门触发率 → 可兑现期望"""
import os, io, json, glob, re, csv
BASE="D:/股票数据/市场数据"; L=os.path.join(BASE,"_学习"); CDIR=os.path.join(L,"_bars_cache")
def load(p):
    for enc in ("utf-8","utf-8-sig","gbk","gb18030"):
        try:
            with io.open(p,encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
def fnum(v):
    try:
        x=float(v); return x if x==x else None
    except Exception: return None
temp=load(os.path.join(L,"_市场温度表.json")) or {}
ths=load(os.path.join(L,"_ths_zt_pool.json")) or {}
bc={}
def bars(c):
    if c in bc: return bc[c]
    p=os.path.join(CDIR,c+".csv"); rows=None
    if os.path.isfile(p):
        rows=[]
        with io.open(p,encoding="utf-8") as f:
            h=f.readline().strip().split(","); idx={k:i for i,k in enumerate(h)}
            for line in f:
                s=line.rstrip("\n").split(",")
                if len(s)<len(h): continue
                rows.append((s[idx["date"]].replace("-",""),fnum(s[idx["open"]]),fnum(s[idx["close"]])))
    bc[c]=rows; return rows
def feats(c,d):
    b=bars(c)
    if not b: return {}
    for i,r in enumerate(b):
        if r[0]==d:
            out={}
            if i+1<len(b):
                o1,c1=b[i+1][1],b[i+1][2]
                if o1 and c1:
                    out["执1"]=c1/o1-1
                    if r[2]: out["gap"]=o1/r[2]-1
                if i+2<len(b):
                    o2,c2=b[i+2][1],b[i+2][2]
                    if o1 and c2: out["执2"]=c2/o1-1
            return out
    return {}
rows=[]; seen=set()
def add(d,c,nm,lb,fj,mv,hs,fb,kai,ind):
    if not ("20250701"<=d<="20261030") or not lb or "退" in (nm or ""): return
    if (d,c) in seen: return
    seen.add((d,c))
    fbr=fj/mv*100 if (fj and mv and mv>0) else None
    f=feats(c,d)
    rows.append(dict(日=d,代码=c,名称=nm,连板=lb,封单比=round(fbr,3) if fbr is not None else None,
                     换手=hs,首封=fb,炸板=kai,行业=ind,温度=(temp.get(d) or {}).get("温度"),
                     执1=f.get("执1"),gap=f.get("gap"),执2=f.get("执2")))
for x in sorted(os.path.basename(os.path.normpath(p)) for p in glob.glob(os.path.join(BASE,"2026*"))
                if os.path.isdir(p) and os.path.isfile(os.path.join(p,"zt_pool.csv"))):
    d=x
    if not ("20250701"<=d<="20261030"): continue
    with io.open(os.path.join(BASE,d,"zt_pool.csv"),encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            lb=fnum(r.get("连板数")); fb=(r.get("首次封板时间") or "").strip().zfill(6)
            add(d,r["代码"].strip().zfill(6),r["名称"],int(lb) if lb else None,
                fnum(r.get("封板资金")),fnum(r.get("流通市值")),fnum(r.get("换手率")),fb,
                int(fnum(r.get("炸板次数")) or 0),r.get("所属行业"))
for d in sorted(ths):
    if not ("20250701"<=d<="20261030"): continue
    for x in ths[d]:
        m=re.search(r"(\d+)板",str(x.get("high_days") or ""))
        add(d,str(x.get("code") or "").zfill(6),str(x.get("name") or ""),int(m.group(1)) if m else 1,
            fnum(x.get("order_amount")),None,None,None,int(fnum(x.get("open_num")) or 0),None)
# 行业家数
from collections import Counter
indc=Counter()
for r in rows:
    if r["行业"]: indc[(r["日"],r["行业"])]+=1
def stat(rs,lo=-3,hi=3):
    v=[r["执1"] for r in rs if r["执1"] is not None]
    if not v: return dict(n=0)
    g=[r["gap"] for r in rs if r.get("gap") is not None]
    tr=round(100*sum(1 for x in g if lo/100<=x<=hi/100)/len(g),1) if g else None
    m=round(100*sum(v)/len(v),2)
    v2=[r["执2"] for r in rs if r.get("执2") is not None]
    return dict(n=len(v),胜率=round(100*sum(1 for x in v if x>0)/len(v),1),执1均收=m,
                闸门触发率=tr,可兑现期望=round(m*tr/100,2) if tr is not None else None,
                执2均收=round(100*sum(v2)/len(v2),2) if v2 else None)
ok=[r for r in rows if r["执1"] is not None]
B={
 "连板3_全": [r for r in ok if r["连板"]==3],
 "连板3_温度40_60": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60],
 "连板3_封单≥3": [r for r in ok if r["连板"]==3 and (r["封单比"] or 0)>=3],
 "连板3_封单2_4": [r for r in ok if r["连板"]==3 and 2<=(r["封单比"] or 0)<4],
 "连板3_首封≤0930": [r for r in ok if r["连板"]==3 and r["首封"] and r["首封"]<="0930"],
 "连板3_温度40_60_封单≥2": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60 and (r["封单比"] or 0)>=2],
 "连板3_行业家数≥3": [r for r in ok if r["连板"]==3 and indc.get((r["日"],r["行业"]),0)>=3],
 "首板_全": [r for r in ok if r["连板"]==1],
 "首板_温度40_60": [r for r in ok if r["连板"]==1 and r["温度"] is not None and 40<=r["温度"]<=60],
 "首板_温度40_60_封单≥1": [r for r in ok if r["连板"]==1 and r["温度"] is not None and 40<=r["温度"]<=60 and (r["封单比"] or 0)>=1],
 "连板2_温度40_60": [r for r in ok if r["连板"]==2 and r["温度"] is not None and 40<=r["温度"]<=60],
 "4板+_全": [r for r in ok if r["连板"]>=4],
 "连板3_温4060_封<2": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60 and (r["封单比"] or 0)<2],
 "连板3_温4060_封2_4": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60 and 2<=(r["封单比"] or 0)<4],
 "连板3_温4060_封≥4": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60 and (r["封单比"] or 0)>=4],
 "连板3_温4060_开0": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60 and r["炸板"]==0],
 "连板3_温4060_开≥1": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60 and r["炸板"]>=1],
 "连板3_温4060_换5_15": [r for r in ok if r["连板"]==3 and r["温度"] is not None and 40<=r["温度"]<=60 and r["换手"] and 5<=r["换手"]<15],
 "连板3_一字": [r for r in ok if r["连板"]==3 and r["首封"] and r["首封"]<="0925"],
 "连板3_0930_1000": [r for r in ok if r["连板"]==3 and r["首封"] and "0930"<=r["首封"]<="1000"],
}
out={k:stat(v) for k,v in B.items()}
print(json.dumps(out,ensure_ascii=False,indent=1))
# 今日候选所在格的最近同格样本(供历史对照)
for code in ("601599","600892","605577","605111","002827","002578","605288"):
    h=[r for r in ok if r["代码"]==code]
    print(code, h[-3:] if h else None)
json.dump(dict(口径="20250701~20261030; 执1=T+1开→T+1收; gap=T+1开/T收; 可兑现期望=执1均收×gap∈[-3,+3]触发率",格=out),
          open(os.path.join(L,"题材格统计_20261104.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
