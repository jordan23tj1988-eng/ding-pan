import json, csv, os
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
zw = L(B+"题材归位_20261030.json")["映射"]
rows = list(csv.DictReader(open(r"D:/股票数据/市场数据/20261030/zt_pool.csv", encoding='utf-8-sig')))
print(f"{'代码':<7}{'名称':<8}{'线':<14}{'环节':<16}{'板':<3}{'封单亿':<7}{'封单比%':<7}{'首封':<7}{'末封':<7}{'炸':<3}{'换手%':<6}{'来源':<3}玄学")
for r in sorted(rows, key=lambda x:(zw.get(x['代码'],{}).get('大方向',''), -int(x['连板数']))):
    c=r['代码']; v=zw.get(c,{})
    feng=float(r['封板资金'])/1e8; ratio=feng*1e8/float(r['流通市值'])*100
    print(f"{c:<7}{r['名称']:<8}{v.get('大方向','?'):<14}{str(v.get('环节'))[:14]:<16}{r['连板数']:<3}"
          f"{feng:<7.2f}{ratio:<7.2f}{r['首次封板时间'][:4]:<7}{r['最后封板时间'][:4]:<7}{r['炸板次数']:<3}"
          f"{float(r['换手率']):<6.1f}{v.get('来源档','')}  {v.get('玄学标签') or v.get('玄学') or ''}")
print()
xs = [(c,v['名称']) for c,v in zw.items() if v.get('玄学标签') or v.get('玄学')]
print("玄学标签股 n=", len(xs), xs)
