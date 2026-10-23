# -*- coding: utf-8 -*-
"""MA-20261022-03③ 质量跃迁双日确认判据 + 回测"""
import csv, json, os, urllib.request, concurrent.futures as cf
D="D:/股票数据/市场数据/"
CACHE=D+"_学习/_tmp_bars_cache.json"
days=["20261012","20261013","20261014","20261015","20261016","20261019","20261020","20261021","20261022","20261023"]
def rd(p):
    with open(p, encoding='utf-8-sig') as f: return list(csv.DictReader(f))
panel={}
for d in days:
    for r in rd(D+d+"/zt_pool.csv"):
        try:
            fz=float(r["封板资金"]); fl=float(r["流通市值"]); hs=float(r["换手率"])
        except: continue
        panel.setdefault(d,{})[r["代码"]]=dict(name=r["名称"], sealr=fz/fl*100 if fl else 0, turn=hs,
            zha=int(float(r["炸板次数"] or 0)), lb=int(float(r["连板数"] or 0)),
            first=str(r["首次封板时间"]).zfill(6), px=float(r["最新价"]), float=fl)
codes=sorted({c for d in days for c in panel.get(d,{})})
bars=json.load(open(CACHE,encoding='utf-8')) if os.path.exists(CACHE) else {}
def mkt(c):
    return ("sh" if c.startswith(("60","68","51")) else "sz")+c
def fetch(c):
    if c in bars: return c,None
    u=f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={mkt(c)},day,2026-10-08,2026-10-28,30,qfq"
    try:
        r=json.loads(urllib.request.urlopen(u,timeout=12).read().decode('utf-8'))
        k=r["data"][mkt(c)].get("qfqday") or r["data"][mkt(c)].get("day") or []
        return c,{x[0]:{"o":float(x[1]),"c":float(x[2]),"h":float(x[3]),"l":float(x[4])} for x in k}
    except Exception as e:
        return c,"ERR:"+type(e).__name__
todo=[c for c in codes if c not in bars]
print("codes",len(codes),"todo",len(todo))
if todo:
    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        for c,res in ex.map(fetch,todo):
            if isinstance(res,str): print(c,res); continue
            bars[c]=res
    json.dump(bars,open(CACHE,"w",encoding="utf-8"))
print("bars ok",len(bars))
def fmt(dd): return dd[:4]+"-"+dd[4:6]+"-"+dd[6:]
def nxt(dd):
    i=days.index(dd); return days[i+1] if i+1<len(days) else None
def exec1(c,td):
    """T=td 涨停，T+1 开→收 执行收益%"""
    nd=nxt(td)
    if not nd or c not in bars: return None
    b=bars[c].get(fmt(nd))
    if not b or not b["o"]: return None
    return (b["c"]-b["o"])/b["o"]*100
def sealed(c,nd):
    return c in panel.get(nd,{})
# 判据函数
def judge(c,td):
    cur=panel.get(td,{}).get(c); 
    if not cur: return None
    pd=days[days.index(td)-1] if days.index(td)>0 else None
    prev=panel.get(pd,{}).get(c) if pd else None
    c1 = cur["sealr"]>=1.5
    c2 = bool(prev) and prev["sealr"]>=1.0
    c3 = bool(prev) and cur["turn"]<=prev["turn"]*1.5
    return dict(T=c1,T1=c2,turnok=c3,double=c1 and c2 and c3, sealr=cur["sealr"], t1sealr=(prev["sealr"] if prev else None),
                turn=cur["turn"], t1turn=(prev["turn"] if prev else None), lb=cur["lb"], zha=cur["zha"], first=cur["first"])
res=[]
for td in days[1:]:
    for c in panel.get(td,{}):
        j=judge(c,td)
        if not j: continue
        r=exec1(c,td)
        if r is None: continue
        j.update(code=c,date=td,name=panel[td][c]["name"],exec1=r,sealed=sealed(c,nxt(td)))
        res.append(j)
res.sort(key=lambda x:(x["date"],x["code"]))
def stat(rows,label):
    if not rows: print(label,"n=0"); return
    n=len(rows); win=sum(1 for x in rows if x["exec1"]>0); mr=sum(x["exec1"] for x in rows)/n
    bad=sum(1 for x in rows if x["exec1"]<=0)
    print(f"{label}: n={n} 执1胜率={win}/{n}={win/n:.1%} 执1均收={mr:+.2f}% 误判率(执1<=0)={bad/n:.1%} T+1断板={sum(1 for x in rows if not x['sealed'])}/{n}")
print("\n=== 全窗(20261013~20261022) ===")
stat([x for x in res if x["double"]],"双日确认PASS")
stat([x for x in res if x["T"] and x["T1"] and not x["turnok"]],"双日但换手超限")
stat([x for x in res if x["T"] and not x["T1"]],"仅T日>=1.5%(单日口径)")
stat([x for x in res if x["T"] and not x["T1"] and x["turnok"]],"单日+换手OK")
stat(res,"全样本(参照)")
dbl=[x for x in res if x["double"]]
print("\n=== 双日确认PASS 逐笔 ===")
for x in dbl:
    print(f"{x['date']} {x['code']} {x['name']:6s} {x['lb']}板 封{x['sealr']:.2f}%(前{x['t1sealr']:.2f}%) 换{x['turn']:.1f}(前{x['t1turn']:.1f}) 首封{x['first']} 炸{x['zha']} 执1={x['exec1']:+.2f}% T+1封={x['sealed']}")
last20=dbl[-20:]
print("\n=== 近20笔 ===")
stat(last20,"双日确认·近20笔")
for x in last20: print(f"  {x['date']} {x['code']} {x['name']} 执1={x['exec1']:+.2f}%")
json.dump(res,open(D+"_学习/_tmp_backtest_res.json","w",encoding='utf-8'),ensure_ascii=False,indent=1)
