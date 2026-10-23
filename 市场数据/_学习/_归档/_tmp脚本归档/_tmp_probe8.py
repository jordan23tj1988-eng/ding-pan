import json, os, glob
B = r"D:/股票数据/市场数据"
L = os.path.join(B, "_学习")

# date folders with zt_pool.csv inside 20260615..20261023
dirs = sorted([d for d in os.listdir(B) if d.isdigit() and len(d)==8 and "20260615" <= d <= "20261023"])
have = [d for d in dirs if os.path.exists(os.path.join(B,d,"zt_pool.csv"))]
print("date dirs in window:", len(dirs), "with zt_pool:", len(have))
print("first/last:", have[:3], have[-5:])
# rows per day sample
import csv
tot = 0
bad = []
for d in have:
    try:
        n = sum(1 for _ in csv.DictReader(open(os.path.join(B,d,"zt_pool.csv"), encoding="utf-8-sig")))
        tot += n
    except Exception as e:
        bad.append((d,str(e)))
print("total zt rows in window:", tot, "bad:", bad[:5])

# temperature coverage
t = json.load(open(os.path.join(L,"_市场温度表.json"), encoding="utf-8"))
missing = [d for d in have if d not in t]
print("温度缺失日:", missing)
cold = [d for d in have if d in t and t[d].get("温度") is not None and t[d]["温度"] < 25]
print("冰点日数:", len(cold))
print("冰点日:", cold)
