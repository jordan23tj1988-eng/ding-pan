import io, os, csv
B = r"D:/股票数据/市场数据"
cache = os.path.join(B,"_学习/_bars_cache")
def j1(poolfile, d, opend, closed):
    with io.open(os.path.join(B,poolfile), encoding="utf-8-sig") as f:
        pool=list(csv.DictReader(f))
    res=[];miss=[]
    for r in pool:
        c=r["代码"]; p=os.path.join(cache,f"{c}.csv")
        if not os.path.exists(p): miss.append(c); continue
        with io.open(p,encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
        dd={x["date"].replace("-",""):x for x in rows}
        a=dd.get(opend); b=dd.get(closed)
        if not (a and b): miss.append(c); continue
        o=float(b["open"]); cl=float(b["close"])
        res.append((c,r["名称"],(cl-o)/o*100, (o-float(a["close"]))/float(a["close"])*100))
    if not res: return
    avg=sum(x[2] for x in res)/len(res); win=sum(1 for x in res if x[2]>0)
    print(f"{poolfile} n={len(res)} miss={len(miss)} 执1均收={avg:.2f}% 胜率={win}/{len(res)}={win/len(res)*100:.1f}%")
    tr=[x for x in res if abs(x[3])<9.5]  # 排除一字开盘(隔夜≈10%)
    if tr:
        print(f"  剔除一字开盘(隔夜≥9.5%)后 n={len(tr)} 均收={sum(x[2] for x in tr)/len(tr):.2f}%")
    return res
r=j1("20261019/zt_pool.csv","20261019","20261019","20261020")
if r:
    for x in sorted(r,key=lambda y:-y[2])[:5]: print("  top",x)
    for x in sorted(r,key=lambda y:y[2])[:5]: print("  bot",x)
j1("20261016/zt_pool.csv","20261016","20261019","20261020")
