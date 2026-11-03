# -*- coding: utf-8 -*-
import json, sys, csv, collections
sys.stdout.reconfigure(encoding='utf-8')
base="D:/股票数据/市场数据/_学习/"; root="D:/股票数据/市场数据/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p,encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("FAIL",p,last); return None
gw=L("题材归位_20261102.json"); mp=gw['映射']
rows={}
with open(root+"20261102/zt_pool.csv",encoding='utf-8-sig') as f:
    for r in csv.DictReader(f): rows[r['代码']]=r
arr=[(c,v,rows[c]) for c,v in mp.items() if v['大方向']=='AI应用/传媒']
arr.sort(key=lambda x: x[2]['首次封板时间'])
print("== AI应用/传媒 45 按首封时间 ==")
for c,v,r in arr:
    seal=float(r['封板资金'])/1e8; flt=float(r['流通市值'])/1e8
    print("%s %-6s 首封%s 末封%s 炸%s 封%.2f亿 封比%.2f%% 换%5.1f%% 流通%4.0f亿 成交%.2f亿 | %-28s | %s" % (
      c, v['名称'], r['首次封板时间'], r['最后封板时间'], r['炸板次数'], seal, seal/flt*100, float(r['换手率']), flt, float(r['成交额'])/1e8, v.get('环节'), v.get('催化')[:40]))
