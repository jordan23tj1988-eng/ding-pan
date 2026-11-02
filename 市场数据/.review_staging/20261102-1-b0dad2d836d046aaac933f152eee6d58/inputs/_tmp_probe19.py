# -*- coding: utf-8 -*-
import json,sys
sys.stdout.reconfigure(encoding='utf-8')
base="D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p,encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("FAIL",p,last); return None
s6=L("主流题材6有_20261102.json")
print("全场判定:",json.dumps(s6['全场判定'],ensure_ascii=False))
print("阈值:",json.dumps(s6['阈值'],ensure_ascii=False))
for r in s6['题材_聚类口径']:
    print(json.dumps(r,ensure_ascii=False))
print("\n=== 四维 20261102 ===")
q=L("_题材四维.json")["20261102"]
for k,v in q.items():
    if k=='_警报': print("_警报:",json.dumps(v,ensure_ascii=False)[:600]); continue
    print("%-16s" % k, json.dumps(v,ensure_ascii=False))
print("\n=== 四维 20261030 (对比) ===")
q0=L("_题材四维.json")["20261030"]
for k,v in q0.items():
    if k=='_警报': continue
    print("%-16s" % k, json.dumps(v,ensure_ascii=False))
