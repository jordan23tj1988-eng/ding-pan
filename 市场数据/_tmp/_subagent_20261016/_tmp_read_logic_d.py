# -*- coding: utf-8 -*-
import json, io, sys, re, glob, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/_学习/'
R = 'D:/股票数据/市场数据/'

def rd(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

print("===== fact_20261016 =====")
try:
    print(json.dumps(rd(B+'fact_20261016.json'), ensure_ascii=False, indent=1))
except Exception as e:
    print("ERR", e)
    for p in glob.glob(B+'fact_*.json')[-6:]:
        print("cand", p)

print("\n===== 市场温度表 last rows =====")
wt = rd(B+'_市场温度表.json')
if isinstance(wt, dict):
    ks = list(wt.keys())
    print("KEYS sample:", ks[:5], "...", ks[-5:])
    for k in ks[-4:]:
        print(k, "->", json.dumps(wt[k], ensure_ascii=False)[:800])
elif isinstance(wt, list):
    for row in wt[-4:]:
        print(json.dumps(row, ensure_ascii=False)[:800])

print("\n===== 待深挖清单_20261016 =====")
print(json.dumps(rd(B+'待深挖清单_20261016.json'), ensure_ascii=False, indent=1)[:3000])

print("\n===== 战绩画像_logic_20261016 =====")
print(json.dumps(rd(B+'子agent增强/战绩画像_logic_20261016.json'), ensure_ascii=False, indent=1))

print("\n===== _逻辑荐票结算.jsonl =====")
for line in open(B+'_逻辑荐票结算.jsonl', 'r', encoding='utf-8'):
    line=line.strip()
    if line: print(line[:600])
