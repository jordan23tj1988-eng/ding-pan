# -*- coding: utf-8 -*-
import json, os, statistics
B = r"D:\股票数据\市场数据\_学习"
def load_any(p):
    for enc in ("utf-8-sig","utf-16","gbk"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception: continue
    return None
q = load_any(os.path.join(B,"涨停质量荐票_20261016.json"))
det = q["明细"]
hdr = ["代码","名称","首封","连板","开板次数","命中数","封单比","换手","市值亿","封单额亿","抓龙率","质量分","预测执1胜率","预测执1均涨","预测执2胜率","预测执2均涨","来源档","大方向"]
print("\t".join(hdr))
for d in sorted(det, key=lambda x:-(x["预测执1胜率"] or 0)):
    row=[]
    for h in hdr:
        v=d.get(h)
        if isinstance(v,float): v=round(v,2)
        row.append(str(v))
    print("\t".join(row))
s1=[d["预测执1胜率"] for d in det if d["预测执1胜率"] is not None]
s1g=[d["预测执1均涨"] for d in det if d["预测执1均涨"] is not None]
print("---")
print("执1胜率 max %.1f min %.1f median %.1f mean %.1f; >50数 %d" % (max(s1),min(s1),statistics.median(s1),statistics.mean(s1),sum(1 for x in s1 if x>50)))
print("执1均涨 max %.2f min %.2f mean %.2f; 正数 %d" % (max(s1g),min(s1g),statistics.mean(s1g),sum(1 for x in s1g if x>0)))
print("命中数>=1:", sum(1 for d in det if (d.get("命中数") or 0)>=1), " 命中数>=3:", sum(1 for d in det if (d.get("命中数") or 0)>=3))
print("质量分 max %s" % max(d.get("质量分") or 0 for d in det))
# top5 full
print("\n=== top5 ===")
for t in q["top5"]:
    print(t["代码"], t["名称"], "首封",t["首封"],"连板",t["连板"],"命中",t["命中数"],"执1",t["预测执1胜率"],t["预测执1均涨"],"执2",t["预测执2胜率"],t["预测执2均涨"],"质量分",t["质量分"],"抓龙",t["抓龙率"])
