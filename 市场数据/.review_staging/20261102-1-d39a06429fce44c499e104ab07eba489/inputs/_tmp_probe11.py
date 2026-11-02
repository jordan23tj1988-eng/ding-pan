# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
base = "D:/股票数据/市场数据/_学习/"
p = base+"_题材生命周期反思.jsonl"
lines=[l for l in open(p,encoding='utf-8').read().splitlines() if l.strip()]
print("反思行数",len(lines))
for l in lines[-2:]:
    o=json.loads(l)
    print(json.dumps(o,ensure_ascii=False)[:6000])
