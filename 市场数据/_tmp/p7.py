# -*- coding: utf-8 -*-
import sys, io, json, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"; L = B + "/_学习"
gw = json.load(open(L + "/题材归位_20261020.json", encoding='utf-8'))
print("== 归位里含『三季报/业绩』 ==")
for c, v in {"A": gw.get("A"), "B": gw.get("B"), "C": gw.get("C")}.items():
    pass
# structure
print("keys A/B/C types:", type(gw["A"]), len(gw["A"]) if hasattr(gw["A"], '__len__') else '')
s = json.dumps(gw, ensure_ascii=False)
print("三季报 hits:", s.count("三季报"), "| 业绩 hits:", s.count("业绩"))
zc = json.load(open(L + "/涨停对链条_20261020.json", encoding='utf-8'))
szc = json.dumps(zc, ensure_ascii=False)
print("对链条 三季报 hits:", szc.count("三季报"))
for m in re.finditer("三季报", szc):
    print("   ...", szc[max(0,m.start()-80):m.start()+80].replace("\n"," "))

# risk events for candidates
ev = json.load(open(L + "/风险事件_20261020.json", encoding='utf-8'))
cands = ["600267","002881","002164","603626","600178","603278","002835","001283","003029","603119","300115","688608","603893","603236","002929"]
print("\n== 风险事件命中 ==")
for c in cands:
    hits = [e for e in ev["事件"] if e.get("代码") == c]
    if hits:
        print(f"  {c}: {len(hits)} 条")
        for h in hits[:6]:
            print("     ", json.dumps(h, ensure_ascii=False)[:260])
    else:
        print(f"  {c}: 0 条(4维内未命中)")

# yesterday summary
try:
    y = json.load(open(B + "/20261019/summary.json", encoding='utf-8'))
    print("\n== 昨日 summary ==", json.dumps({k: y.get(k) for k in ["两市成交额_亿","涨停家数","跌停家数","炸板率","最高连板","连板梯队"]}, ensure_ascii=False))
except Exception as e:
    print("yesterday summary FAIL", e)
