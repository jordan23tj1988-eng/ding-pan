# -*- coding: utf-8 -*-
import os, json
L = r"D:/股票数据/市场数据/_学习"
recs = json.load(open(os.path.join(L,"_tmp_all_recs.json"), encoding="utf-8"))
neu = [r for r in recs if 45 <= r["temp"] < 65]
nb = sum(r["e1"] for r in neu if r["tradeable"])/sum(1 for r in neu if r["tradeable"])
def rep(tag, rs, b=nb):
    tr = [r for r in rs if r["tradeable"]]
    if not tr: print("  %-30s n=%d 全不可成交" % (tag,len(rs))); return
    m=sum(r["e1"] for r in tr)/len(tr); w=100*sum(1 for r in tr if r["e1"]>0)/len(tr)
    print("  %-30s 可成交n=%3d 均%+.2f%% 超额%+.2fpp 胜率%5.1f%%" % (tag,len(tr),m,m-b,w))
print("中性基线 %.3f" % nb)
for tag,f in [("炸>=5(全)",lambda r:r["zb"]>=5),("炸>=8",lambda r:r["zb"]>=8),("炸=10",lambda r:r["zb"]>=10),
              ("炸5-7×换手10-20",lambda r:5<=r["zb"]<=7 and 10<=r["to"]<20),
              ("炸>=8×换手10-20",lambda r:r["zb"]>=8 and 10<=r["to"]<20),
              ("炸>=5×首板",lambda r:r["zb"]>=5 and r["lb"]==1),
              ("炸>=5×2板",lambda r:r["zb"]>=5 and r["lb"]==2),
              ("炸>=5×首封13-14:30",lambda r:r["zb"]>=5 and "130000"<r["ft"]<="143000"),
              ("炸>=5×封单<0.5%×换手10-20",lambda r:r["zb"]>=5 and r["seal"]<0.5 and 10<=r["to"]<20),
              ("封单<0.5%×换手10-20",lambda r:r["seal"]<0.5 and 10<=r["to"]<20),
              ("封单<1%×换手10-20×炸>=5×首封10-14",lambda r:r["seal"]<1 and 10<=r["to"]<20 and r["zb"]>=5 and "100000"<r["ft"]<="140000")]:
    rep(tag,[r for r in neu if f(r)])

# 风险事件
import glob
rp = [p for p in glob.glob(os.path.join(L,"*风险*20261023*.json"))]
print("\n风险文件:", rp)
for p in rp:
    d = json.load(open(p, encoding="utf-8"))
    s = json.dumps(d, ensure_ascii=False)
    print(os.path.basename(p), len(s))
    for code in ("003021","300561","002724","603278","000678","301502"):
        i = s.find(code)
        if i >= 0:
            print("  ", code, s[max(0,i-150):i+250].replace("\n"," "))
