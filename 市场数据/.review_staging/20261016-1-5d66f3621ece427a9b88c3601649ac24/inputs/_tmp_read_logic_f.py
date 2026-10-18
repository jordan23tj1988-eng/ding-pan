# -*- coding: utf-8 -*-
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = 'D:/股票数据/市场数据/_学习/'
raw = open(B+'中报预增雷达_20261016.json','rb').read()
print("bytes:", len(raw))
s = raw.decode('utf-8', errors='replace')
print("has 双源:", '双源' in s, "| has 交叉:", '交叉' in s, "| has 东财:", '东财' in s, "| iwencai:", 'iwencai' in s.lower())
# top-level keys
keys = re.findall(r'\n "([^"]+)":\s*([\{\[])', s)
print("TOP KEYS:", [k for k,_ in keys])
try:
    dec = json.JSONDecoder()
    obj, end = dec.raw_decode(s)
    print("raw_decode OK, end=", end, "len=", len(s))
    print("OBJ KEYS:", list(obj.keys()))
    for k in obj.keys():
        v = obj[k]
        if isinstance(v, list):
            print("  ", k, "list len", len(v))
        elif isinstance(v, dict):
            print("  ", k, "dict keys", list(v.keys())[:8])
        else:
            print("  ", k, "=", str(v)[:200])
except Exception as e:
    print("raw_decode FAIL:", e)
