# -*- coding: utf-8 -*-
import os, json, csv, collections
L = r"D:/股票数据/市场数据/_学习"
q = json.load(open(os.path.join(L,"涨停质量荐票_20261023.json"), encoding="utf-8"))
dm = q["明细"]
out=[]
out.append("明细 n={}".format(len(dm)))
out.append("字段: " + ", ".join(list(dm[0].keys())))
sc = collections.Counter(d["质量分"] for d in dm)
out.append("质量分分布: " + json.dumps(dict(sorted(sc.items(), reverse=True)), ensure_ascii=False))
pred = sorted(dm, key=lambda x: -(x.get("预测执1胜率") or 0))
out.append("预测执1胜率 max={:.1f} min={:.1f} 均{:.2f}".format(pred[0]["预测执1胜率"], pred[-1]["预测执1胜率"], sum(d["预测执1胜率"] for d in dm)/len(dm)))
out.append("预测执1均涨 均值 {:.3f}pct".format(sum(d["预测执1均涨"] for d in dm)/len(dm)))
out.append("\n[质量分>=6]")
for d in sorted([x for x in dm if x["质量分"]>=6], key=lambda x:-x["质量分"]):
    out.append("  {} {} 分{} 首封{} 板{} 炸{} 封单{:.3f} 换手{:.2f} 流通{:.1f}亿 预执1胜率{:.1f} 预均涨{:+.2f} 方向{} 规则{}".format(
        d["代码"], d["名称"], d["质量分"], d["首封"], d["连板"], d["开板次数"], d["封单比"], d["换手"],
        d["市值亿"], d["预测执1胜率"], d["预测执1均涨"], d.get("大方向"), d.get("命中规则")))
rows = {r["代码"]: r for r in csv.DictReader(open(r"D:/股票数据/市场数据/20261023/zt_pool.csv", encoding="utf-8-sig"))}
g1=[];g2=[];g3=[]
for c,r in rows.items():
    seal=float(r["封板资金"])/float(r["流通市值"])*100; to=float(r["换手率"]); ft=str(r["首次封板时间"]).zfill(6)
    lb=int(float(r["连板数"])); zb=int(float(r["炸板次数"]))
    if seal<0.5 and 3<=to<=10: g1.append((c,r["名称"],seal,to))
    if seal>=4 and zb==0: g2.append((c,r["名称"],seal,to,lb))
    if ft>"143000" and lb==1: g3.append((c,r["名称"],ft,seal,to))
out.append("\n①薄封<0.5 x 换手3-10 n={}: {}".format(len(g1), " / ".join("{}{}({:.2f},{:.1f})".format(a,b,s,t) for a,b,s,t in sorted(g1,key=lambda x:x[2]))))
out.append("\n②封单>=4 x 炸0 n={}: {}".format(len(g2), " / ".join("{}{}({}板,{:.2f},{:.1f})".format(a,b,l,s,t) for a,b,s,t,l in sorted(g2,key=lambda x:-x[2]))))
out.append("\n③首封>14:30 x 首板 n={}: {}".format(len(g3), " / ".join("{}{}({},{:.2f},{:.1f})".format(a,b,f,s,t) for a,b,f,s,t in sorted(g3))))
c20=[r for r in rows.values() if r["代码"][:3] in ("300","301","688")]
bj=[r for r in rows.values() if r["代码"][:2] in ("92","83","87","43")]
out.append("\n20cm {} 只, 北交所 {} 只: {}".format(len(c20), len(bj), [r["代码"] for r in bj]))
buckets=collections.Counter()
for r in rows.values():
    ft=str(r["首次封板时间"]).zfill(6)
    if ft<="092500": buckets["<=09:25"]+=1
    elif ft<="093100": buckets["09:26-09:31"]+=1
    elif ft<="100000": buckets["09:32-10:00"]+=1
    elif ft<="130000": buckets["10:01-13:00"]+=1
    elif ft<="140000": buckets["13:01-14:00"]+=1
    elif ft<="143000": buckets["14:01-14:30"]+=1
    else: buckets[">14:30"]+=1
out.append("首封分布: " + json.dumps(dict(buckets), ensure_ascii=False))
out.append("炸>=5 {} 只, 炸0 {} 只, 封单<0.5pct {} 只, 换手<3pct {} 只, 换手>=20pct {} 只".format(
    sum(1 for r in rows.values() if int(float(r["炸板次数"]))>=5),
    sum(1 for r in rows.values() if int(float(r["炸板次数"]))==0),
    sum(1 for r in rows.values() if float(r["封板资金"])/float(r["流通市值"])*100<0.5),
    sum(1 for r in rows.values() if float(r["换手率"])<3),
    sum(1 for r in rows.values() if float(r["换手率"])>=20)))
open(os.path.join(L,"_tmp_out2_1023.txt"),"w",encoding="utf-8").write("\n".join(out))
print("ok", len(out))
