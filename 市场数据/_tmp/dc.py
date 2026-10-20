import io, os, csv
B = r"D:/股票数据/市场数据"
cache = os.path.join(B,"_学习/_bars_cache")
with io.open(os.path.join(B,"20261020/zt_pool.csv"), encoding="utf-8-sig") as f:
    pool = list(csv.DictReader(f))
res=[]
miss=[]
for r in pool:
    c=r["代码"]; p=os.path.join(cache,f"{c}.csv")
    if not os.path.exists(p): miss.append(c); continue
    with io.open(p,encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
    row=[x for x in rows if x["date"].replace("-","")=="20261020"]
    if not row: miss.append(c); continue
    o=float(row[0]["open"]); cl=float(row[0]["close"])
    res.append((c, r["名称"], r["连板数"], o, cl, (cl-o)/o*100))
print("n=",len(res),"miss=",miss)
avg=sum(x[5] for x in res)/len(res)
win=sum(1 for x in res if x[5]>0)
print("全池执1均收 %.2f%%  胜率 %d/%d=%.1f%%"%(avg,win,len(res),win/len(res)*100))
# 排除一字(open==close 且 ==涨停价 近似: open==high==low) 的可成交子集
tradeable=[x for x in res if not (abs(x[4]-x[3])<1e-9)]
print("剔除开盘即收(open==close)后 n=%d 均收%.2f%%"%(len(tradeable), sum(x[5] for x in tradeable)/len(tradeable)))
for name,codes in [("3板+",[x for x in res if x[2] in ("3","4")]),("2板",[x for x in res if x[2]=="2"]),("首板",[x for x in res if x[2]=="1"])]:
    if codes:
        print(f"{name} n={len(codes)} 均收{sum(x[5] for x in codes)/len(codes):.2f}% 胜率{sum(1 for x in codes if x[5]>0)}/{len(codes)}")
print("--- 明细(按连板)")
for x in sorted(res,key=lambda y:(-int(y[2]),y[5]))[:20]:
    print(x[0],x[1],"连板",x[2],"open",x[3],"close",x[4],"执1 %.2f%%"%x[5])
# 指定票
print("--- 指定")
for c in ["603197","603278","003029","002724","600148","600860","002889","605189"]:
    p=os.path.join(cache,f"{c}.csv")
    with io.open(p,encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
    d={x["date"].replace("-",""):x for x in rows}
    a=d.get("20261019"); b=d.get("20261020")
    if a and b:
        print(c,"1019close",a["close"],"1020open",b["open"],"close",b["close"],"执1 %.2f%%"%((float(b["close"])-float(b["open"]))/float(b["open"])*100),
              "| 隔夜 %.2f%%"%((float(b["open"])-float(a["close"]))/float(a["close"])*100))
