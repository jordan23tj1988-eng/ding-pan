# -*- coding: utf-8 -*-
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"; L = B + "/_学习"

# 温度
html = open(L + "/资金温度卡_20261020.html", encoding='utf-8', errors='replace').read()
m = re.findall(r'温度[^<>]{0,20}?(\d+\.\d+)', html)
print("温度候选:", m[:12])
txt = re.sub(r'<[^>]+>', ' ', html)
txt = re.sub(r'\s+', ' ', txt)
i = txt.find('温度')
print("片段:", txt[max(0,i-200):i+700])

# template full
tpl = json.load(open(B + "/产业链模板.json", encoding='utf-8'))
print("\n== 模板详情 ==")
for plate, v in tpl.items():
    if not isinstance(v, dict):
        continue
    print("##", plate)
    for step, arr in v.items():
        names = [x[1] if isinstance(x, list) and len(x) > 1 else str(x) for x in arr] if isinstance(arr, list) else [str(arr)]
        codes = [x[0] for x in arr if isinstance(x, list)] if isinstance(arr, list) else []
        print("   -", step, "|", "/".join(names), "|", ",".join(codes))
