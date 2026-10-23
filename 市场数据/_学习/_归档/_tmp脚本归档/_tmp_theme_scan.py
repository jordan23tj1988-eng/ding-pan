# -*- coding: utf-8 -*-
import csv, json, statistics, io, os
D = "D:/股票数据/市场数据/"
def rd(p):
    with open(p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))
zt = rd(D+"20261023/zt_pool.csv")
g = json.load(open(D+"_学习/题材归位_20261023.json", encoding='utf-8'))
mp = g["映射"]
print("zt", len(zt))
rows=[]
for r in zt:
    c=r["代码"]
    a=mp.get(c,{})
    def f(x):
        try: return float(x)
        except: return 0.0
    row=dict(code=c, name=r["名称"], 大方向=a.get("大方向","未归位"), 环节=a.get("环节",""),
             连板=a.get("连板口径",""), 连板数=int(float(r["连板数"] or 0)),
             首封=r["首次封板时间"], 末封=r["最后封板时间"], 炸=int(float(r["炸板次数"] or 0)),
             封单=f(r["封板资金"]), 流通=f(r["流通市值"]), 成交=f(r["成交额"]), 换手=f(r["换手率"]),
             行业=r["所属行业"], 价=f(r["最新价"]), 统计=r["涨停统计"])
    row["封单率"]= row["封单"]/row["流通"]*100 if row["流通"] else 0
    row["封成比"]= row["封单"]/row["成交"] if row["成交"] else 0
    rows.append(row)
by = {}
for r in rows: by.setdefault(r["大方向"],[]).append(r)
def early(t):
    t=str(t).zfill(6); return t<="093600"
print("\n=== 方向聚合 ===")
for k,v in sorted(by.items(), key=lambda x:-len(x[1])):
    n=len(v); sb2=sum(1 for x in v if x["连板数"]==2); sb3p=sum(1 for x in v if x["连板数"]>=3)
    fb=[x for x in v if x["炸"]>0]
    med=statistics.median([x["封单率"] for x in v])
    er=sum(1 for x in v if early(x["首封"]))
    print(f"{k}: n={n} 2板={sb2} 3板+={sb3p} 开板占比={len(fb)/n:.2f} 炸合计={sum(x['炸'] for x in v)} 封单率中位={med:.2f}% 早封(<=0936)={er}/{n} 高度={max(x['连板数'] for x in v)}")
print("\n=== 机器人 37 只逐只 ===")
rob=sorted(by.get("机器人",[]), key=lambda x:(-x["连板数"], -x["封单率"]))
for x in rob:
    print(f"{x['code']} {x['name']:6s} {x['连板']:5s} {x['连板数']}板 首封{x['首封']} 末封{x['末封']} 炸{x['炸']} 封单率{x['封单率']:.2f}% 封成{x['封成比']:.2f} 换手{x['换手']:.1f}% 成交{x['成交']/1e8:.2f}亿 流通{x['流通']/1e8:.1f}亿 价{x['价']:.2f} | {x['环节']}")
