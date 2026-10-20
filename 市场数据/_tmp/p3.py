# -*- coding: utf-8 -*-
import sys, io, json, re, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"; L = B + "/_学习"
raw = open(L + "/中报预增雷达_20261020.json", 'rb').read().decode('utf-8', errors='replace')
print("== 双源/iwencai keyword scan ==")
for kw in ["双源", "iwencai", "东财", "交叉", "三季报", "报告期口径"]:
    idxs = [m.start() for m in re.finditer(kw, raw)]
    print(f"{kw}: {len(idxs)} hits")
    for i in idxs[:4]:
        print("   ...", raw[max(0,i-90):i+110].replace("\n", " "))

rad = json.load(open(B + "/_tmp/radar_parsed.json", encoding='utf-8'))
for key in ["概念叠加候选", "纯预增未叠加", "预期已兑现(年内已翻倍,不入候选)", "已发酵对照Top12"]:
    v = rad[key]
    print("\n==", key, len(v), "sample keys:", list(v[0].keys()) if v else None)

# zt_pool
print("\n== zt_pool ==")
rows = list(csv.DictReader(open(B + "/20261020/zt_pool.csv", encoding='utf-8-sig')))
print("n=", len(rows), "fields=", list(rows[0].keys()))
for r in rows:
    print("  ", r.get("代码"), r.get("名称"), r.get("连板数"), r.get("所属行业"), r.get("封板资金"), r.get("首次封板时间"), r.get("炸板次数"))
