# -*- coding: utf-8 -*-
import json,sys,collections
sys.stdout.reconfigure(encoding='utf-8')
d=json.load(open("D:/股票数据/市场数据/_学习/题材生命周期结算_20261030.json",encoding='utf-8'))
print("汇总",json.dumps(d['汇总'],ensure_ascii=False))
c=collections.Counter(r['注'] for r in d['明细'])
print("按注:",json.dumps(c,ensure_ascii=False))
for r in d['明细']:
    print("%-14s %-4s→%-4s P%.2f 判=%-3s 注=%-22s 次日四维=%s" % (r['线'],r['预判日阶段'],r['转移'],r.get('概率') or 0,r['判定'],r['注'],json.dumps(r.get('次日四维'),ensure_ascii=False)))
