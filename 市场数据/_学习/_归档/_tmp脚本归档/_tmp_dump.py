# -*- coding: utf-8 -*-
import csv, json
D="D:/股票数据/市场数据/"
def rd(p):
    with open(p, encoding='utf-8-sig') as f: return list(csv.DictReader(f))
zt=rd(D+"20261023/zt_pool.csv"); g=json.load(open(D+"_学习/题材归位_20261023.json",encoding='utf-8'))["映射"]
out=[]
for r in zt:
    c=r["代码"]
    if g.get(c,{}).get("大方向")!="机器人": continue
    fl=float(r["流通市值"]); fz=float(r["封板资金"]); amt=float(r["成交额"])
    out.append((c,r["名称"],int(float(r["连板数"] or 0)),str(r["首次封板时间"]).zfill(6),int(float(r["炸板次数"] or 0)),
      fz/fl*100, float(r["换手率"]), float(r["最新价"]), fl/1e8, fz/1e8, amt/1e8, fz/amt, g[c].get("环节","")))
out.sort(key=lambda x:(-x[2],-x[5]))
for x in out:
    print("|".join([x[0],x[1],f"{x[2]}板",x[3],f"炸{x[4]}",f"{x[5]:.2f}%",f"{x[6]:.1f}%",f"{x[7]:.2f}",f"{x[8]:.0f}亿",f"封{x[9]:.2f}亿",f"成交{x[10]:.1f}亿",f"{x[11]:.2f}",x[12]]))
print("N=",len(out))
