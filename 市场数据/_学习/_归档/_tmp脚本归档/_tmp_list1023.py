# -*- coding: utf-8 -*-
import os, csv, json
B = r"D:/股票数据/市场数据"; L = os.path.join(B,"_学习")
rows = list(csv.DictReader(open(os.path.join(B,"20261023","zt_pool.csv"), encoding="utf-8-sig")))
gw = json.load(open(os.path.join(L,"题材归位_20261023.json"), encoding="utf-8"))
print("归位 keys:", list(gw.keys())[:8])
def g(code):
    for k in ("个股","明细","归位"):
        if k in gw and isinstance(gw[k], dict) and code in gw[k]: return gw[k][code]
        if k in gw and isinstance(gw[k], list):
            for x in gw[k]:
                if x.get("代码")==code: return x
    return None
out=[]
for r in rows:
    code=r["代码"]; cmv=float(r["流通市值"]); amt=float(r["封板资金"])
    out.append((code, r["名称"], int(float(r["连板数"])), str(r["首次封板时间"]).zfill(6),
                int(float(r["炸板次数"])), amt/cmv*100, float(r["换手率"]), cmv/1e8, float(r["成交额"])/1e8, r["所属行业"]))
out.sort(key=lambda x:(-x[2], -x[5]))
print("\n%-8s %-8s %2s %-7s %2s %7s %7s %7s %7s %s" % ("代码","名称","板","首封","炸","封单%","换手%","流通亿","成交亿","行业"))
for o in out:
    print("%-8s %-8s %2d %-7s %2d %7.3f %7.2f %7.1f %7.2f %s" % o)
print("\n归位样例:", json.dumps(g("002724"), ensure_ascii=False))
print("归位样例:", json.dumps(g("603278"), ensure_ascii=False))
