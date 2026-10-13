# -*- coding: utf-8 -*-
"""MA-20261012-04 可复算脚本：媒体AI内容系 族聚合（白名单+宽窄边界）
用法: python _tmp_族聚合.py 20261013 [20261012 ...]
口径: 族成员 = 该日 题材归位_{d}.json 的『大方向』∈线名白名单; 封板总额/涨停总数来自 涨停对链条_{d}.json + zt_pool
"""
import json, os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'D:/股票数据/市场数据'
XL = os.path.join(ROOT, '_学习')

# ---- 白名单（宽窄边界）----
# 宽口径(族)：AI内容/传媒/出版/IP 全链
FAMILY_WIDE = ["AI应用","AI漫剧","AI短剧","传媒重组","AI影视","AI营销","AI内容安全","出版发行","影视院线","出版"]
# 窄口径(核)：仅"内容生产+IP"两条最贴主线的线
FAMILY_CORE = ["AI漫剧","AI短剧","AI应用"]

def load(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try:
            with open(p, encoding=enc) as f: return json.load(f)
        except Exception:
            pass
    raise RuntimeError(p)

def ztpool(d):
    p=os.path.join(ROOT,d,'zt_pool.csv')
    rows=[]
    with open(p, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def family_agg(d, lines):
    gw = load(os.path.join(XL,f'题材归位_{d}.json'))
    mp = gw['映射']
    rows = ztpool(d)
    amt_all = sum(float(r['封板资金']) for r in rows if r['封板资金'])
    n_all = len(rows)
    members=[]
    fam_amt=0.0
    for code,v in mp.items():
        if v['大方向'] in lines:
            # 封板资金 from zt_pool
            row = next((r for r in rows if r['代码']==code), None)
            amt = float(row['封板资金']) if row and row['封板资金'] else 0.0
            fam_amt += amt
            members.append((code, v['名称'], v['大方向'], int(v['连板数']), amt))
    ladders={}
    for m in members: ladders[m[3]]=ladders.get(m[3],0)+1
    return dict(日=d, 口径线名=lines, 族成员数=len(members), 全场涨停=n_all,
                族占涨停比=round(len(members)/n_all*100,1),
                族封板资金亿=round(fam_amt/1e8,2), 全场封板总额亿=round(amt_all/1e8,2),
                族封板资金占比=round(fam_amt/amt_all*100,1) if amt_all else None,
                阶梯=dict(sorted(ladders.items(),reverse=True)),
                成员=sorted(members, key=lambda x:-x[3]))

for d in sys.argv[1:]:
    print("="*70); print("日期", d)
    for name, lines in [("宽口径", FAMILY_WIDE), ("窄口径", FAMILY_CORE)]:
        a = family_agg(d, lines)
        print(f"[{name}] 族成员{a['族成员数']}只 占全场涨停{a['族占涨停比']}% | 封板资金{a['族封板资金亿']}亿 占全场{a['族封板资金占比']}% (全场{a['全场封板总额亿']}亿) | 阶梯{a['阶梯']}")
        print("   成员:", ", ".join(f"{m[1]}({m[2]}{m[3]}板)" for m in a['成员']))
