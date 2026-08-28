# -*- coding: utf-8 -*-
import json, os, csv
BASE = "D:/股票数据/市场数据"; X = BASE + "/_学习"
def load(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except FileNotFoundError: return None
        except Exception: continue
    return None

print("#### 四维 当日key(20260826) ####")
sw = load(X+"/_题材四维.json")
print("top keys:", list(sw.keys())[:5] if isinstance(sw,dict) else type(sw))
if isinstance(sw,dict):
    ks = sorted([k for k in sw.keys() if k.startswith("2026")])
    print("date keys tail:", ks[-6:])
    for d in ["20260825","20260826"]:
        print("\n--- ", d)
        print(json.dumps(sw.get(d), ensure_ascii=False, indent=1)[:9000])

print("\n#### summary 20260826 ####")
print(json.dumps(load(BASE+"/20260826/summary.json"), ensure_ascii=False, indent=1))

print("\n#### 温度表 20260826 / 20260825 ####")
wd = load(X+"/_市场温度表.json")
if isinstance(wd, dict):
    for d in ["20260825","20260826"]:
        v = wd.get(d)
        print(d, json.dumps(v, ensure_ascii=False))
elif isinstance(wd, list):
    for r in wd:
        if str(r.get("日","")) in ("20260825","20260826") or str(r.get("日期",""))in("20260825","20260826"):
            print(json.dumps(r, ensure_ascii=False))
