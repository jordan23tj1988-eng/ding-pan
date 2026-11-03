# -*- coding: utf-8 -*-
import json, sys, csv, collections, statistics
sys.stdout.reconfigure(encoding='utf-8')
base = "D:/股票数据/市场数据/_学习/"
root = "D:/股票数据/市场数据/"
def L(p):
    for enc in ('utf-8-sig','gbk','gb18030'):
        try:
            with open(base+p, encoding=enc) as f: return json.load(f)
        except Exception as e: last=e
    print("LOADFAIL", p, last); return None
gw = L("题材归位_20261102.json"); mp = gw['映射']
rows = {}
with open(root+"20261102/zt_pool.csv", encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        rows[r['代码']] = r
by = collections.defaultdict(list)
for c,v in mp.items():
    by[v['大方向']].append((c,v,rows.get(c)))
tot_seal = 0.0
print("code name 连板 首封 炸 封单亿 封单比% 换手% 流通亿 一字?")
for d,arr in sorted(by.items(), key=lambda x:-len(x[1])):
    seals=[]; rates=[]; yz=0; early=0; huan=0; env=set()
    miss=0
    for c,v,r in arr:
        if not r: miss+=1; continue
        seal = float(r['封板资金'])/1e8
        flt = float(r['流通市值'])/1e8
        rate = seal/flt*100 if flt else 0
        to = float(r['换手率'])
        seals.append(seal); rates.append(rate); tot_seal+=seal
        first, last = r['首次封板时间'], r['最后封板时间']
        isyz = (first==last and first.startswith('0925') and r['炸板次数']=='0' and to<1.0)
        if isyz: yz+=1
        if first<='093100': early+=1
        if r['炸板次数']!='0': huan+=1
        env.add(v.get('环节'))
    n=len(arr)
    print("### %s n=%d 封单%.2f亿 封单比中位%.2f%% 一字%d 早封%d 开板%d 环节数%d 离散度%.2f miss%d" % (
        d,n,sum(seals), statistics.median(rates) if rates else 0, yz, early, huan, len(env), len(env)/n if n else 0, miss))
    # 明细 top by seal
    arr2 = sorted([x for x in arr if x[2]], key=lambda x: -float(x[2]['封板资金']))
    for c,v,r in arr2[:6]:
        seal=float(r['封板资金'])/1e8; flt=float(r['流通市值'])/1e8
        print("   ", c, v['名称'], r['连板数']+"板", "首封"+r['首次封板时间'], "末封"+r['最后封板时间'], "炸"+r['炸板次数'], "封%.2f亿"%(seal), "封比%.2f%%"%(seal/flt*100), "换手%.1f%%"%float(r['换手率']), "流通%.0f亿"%flt, "|", v.get('环节'))
print("\n全场封单总额 %.2f亿" % tot_seal)
