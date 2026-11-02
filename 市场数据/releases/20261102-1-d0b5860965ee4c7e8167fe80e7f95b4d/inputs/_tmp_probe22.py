# -*- coding: utf-8 -*-
import json,csv,sys
sys.stdout.reconfigure(encoding='utf-8')
base="D:/股票数据/市场数据/_学习/"; root="D:/股票数据/市场数据/"
mp=json.load(open(base+"题材归位_20261102.json",encoding='utf-8'))['映射']
rows={r['代码']:r for r in csv.DictReader(open(root+"20261102/zt_pool.csv",encoding='utf-8-sig'))}
for line in ("AI应用/软件","周期/资源材料","机器人/具身智能"):
    print("==",line)
    for c,v in mp.items():
        if v['大方向']!=line: continue
        r=rows[c]; seal=float(r['封板资金'])/1e8; flt=float(r['流通市值'])/1e8
        print(" %s %-6s 首封%s 炸%s 封%.2f亿 封比%.2f%% 换%5.1f%% 流通%4.0f亿 成交%5.2f亿 | %s | %s" % (
          c,v['名称'],r['首次封板时间'],r['炸板次数'],seal,seal/flt*100,float(r['换手率']),flt,float(r['成交额'])/1e8,v.get('环节'),(v.get('催化') or '')[:30]))
