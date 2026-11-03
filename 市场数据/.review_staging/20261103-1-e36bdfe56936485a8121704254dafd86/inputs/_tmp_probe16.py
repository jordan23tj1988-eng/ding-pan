# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
base="D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p,encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("FAIL",p,last); return None
y=L("题材生命周期_20261030.json"); t=L("题材生命周期_20261102.json")
print("=== 昨日阶段表 ===")
for r in y['阶段表']:
    print(r['线'], "|", r['阶段'], "| 宽",r.get('宽'),"高",r.get('高'),"mom",r.get('mom'),"jj",r.get('jj'), "| 陷阱",r.get('陷阱'), "| 预判", json.dumps(r.get('预判'),ensure_ascii=False))
print("\n=== 今日阶段表 ===")
for r in t['阶段表']:
    print(r['线'], "|", r['阶段'], "| 宽",r.get('宽'),"高",r.get('高'),"mom",r.get('mom'),"jj",r.get('jj'), "| 陷阱",r.get('陷阱'), "| 预判", json.dumps(r.get('预判'),ensure_ascii=False)[:220])
print("\n=== 今日摘要 ===", json.dumps(t['摘要'],ensure_ascii=False))
