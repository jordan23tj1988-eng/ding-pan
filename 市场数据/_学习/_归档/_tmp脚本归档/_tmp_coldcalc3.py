# -*- coding: utf-8 -*-
import os, json, csv
L = r"D:/股票数据/市场数据/_学习"
B = r"D:/股票数据/市场数据"
recs = json.load(open(os.path.join(L, "_tmp_cold_recs.json"), encoding="utf-8"))
tr = [r for r in recs if r["tradeable"]]
trm = sum(r["e1"] for r in tr)/len(tr)

def stats(xs, base=None):
    if not xs: return None
    m = sum(x["e1"] for x in xs)/len(xs)
    w = 100*sum(1 for x in xs if x["e1"] > 0)/len(xs)
    d = dict(n=len(xs), mean=round(m,3), win=round(w,1))
    if base is not None: d["ex"]=round(m-base,3)
    return d

print("=== ① 的换手子段（可成交口径，基准%.3f%%）===" % trm)
for nm, fn in [("换手3-5%", lambda r: 3 <= r["to"] < 5),
               ("换手5-7%", lambda r: 5 <= r["to"] < 7),
               ("换手7-10%", lambda r: 7 <= r["to"] <= 10),
               ("换手3-5%×首板", lambda r: 3 <= r["to"] < 5 and r["lb"] == 1),
               ("换手3-5%×炸≥2", lambda r: 3 <= r["to"] < 5 and r["zb"] >= 2)]:
    a = [r for r in tr if r["seal"] < 0.5 and fn(r)]
    s = stats(a, trm)
    print("  %-14s %s" % (nm, s if s else "n=0"))

print("\n=== ② 强封≥4%×炸0 可成交明细（n=17）===")
for r in recs:
    if r["seal"] >= 4 and r["zb"] == 0 and r["tradeable"]:
        print("  %s %s %s 封单%.2f%% 换手%.1f%% 首封%s e1%+.2f%% gap%+.1f%%" % (r["d"], r["code"], r["name"], r["seal"], r["to"], r["ft"], r["e1"], r["gap"]))

print("\n=== ③ 首封>14:30×首板 可成交明细（n=21）===")
for r in recs:
    if r["ft"] > "143000" and r["lb"] == 1 and r["tradeable"]:
        print("  %s %s %s 封单%.2f%% 换手%.1f%% 首封%s e1%+.2f%%" % (r["d"], r["code"], r["name"], r["seal"], r["to"], r["ft"], r["e1"]))

# 今日池落格
print("\n=== 今日 82只 落格（冰点桶参照，仅作排序参考；今日非冰点）===")
rows = list(csv.DictReader(open(os.path.join(B,"20261023","zt_pool.csv"), encoding="utf-8-sig")))
hit = []
for r in rows:
    amt=float(r["封板资金"]); cmv=float(r["流通市值"]); to=float(r["换手率"]); ft=str(r["首次封板时间"]).zfill(6)
    lb=int(float(r["连板数"])); zb=int(float(r["炸板次数"])); seal=amt/cmv*100
    tags=[]
    if seal<0.5 and 3<=to<=10: tags.append("①薄封中换手")
    if seal>=4 and zb==0: tags.append("②强封炸0")
    if ft>"143000" and lb==1: tags.append("③尾盘首板")
    if seal<0.5 and to<3: tags.append("x薄封低换手")
    if seal>=4 and zb>=1: tags.append("x强封炸")
    if tags:
        hit.append((r["代码"],r["名称"],seal,to,ft,lb,zb,tags))
for h in sorted(hit, key=lambda x: x[2]):
    print("  %s %s 封单%.2f%% 换手%.1f%% 首封%s %d板 炸%d %s" % h)
