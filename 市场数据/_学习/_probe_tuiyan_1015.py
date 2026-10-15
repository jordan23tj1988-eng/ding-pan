# -*- coding: utf-8 -*-
import json, io, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"D:/股票数据/市场数据"

def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

# 1) 先行指标 取尾部
try:
    d = load(BASE + "/_学习/_情绪先行指标.json")
    ks = sorted(d.keys())
    print("=== 先行指标 keys tail 8 ===")
    print(ks[-8:])
    for k in ks[-6:]:
        print(k, json.dumps(d[k], ensure_ascii=False))
except Exception as e:
    print("先行指标 ERR", e)

# 2) 温度表 尾10
try:
    t = load(BASE + "/_学习/_市场温度表.json")
    print("=== 温度表 type ===", type(t))
    if isinstance(t, dict):
        ks = sorted(t.keys())
        print("水keys tail12:", ks[-12:])
        for k in ks[-12:]:
            print(k, json.dumps(t[k], ensure_ascii=False))
except Exception as e:
    print("温度表 ERR", e)
