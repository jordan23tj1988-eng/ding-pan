import csv,json
from collections import defaultdict
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
zt={r['代码']:r for r in csv.DictReader(open('20261023/zt_pool.csv',encoding='utf-8-sig'))}
lhb=list(csv.DictReader(open('20261023/lhb.csv',encoding='utf-8-sig')))
ded=[r for r in lhb if not is_int(r['上榜原因'])]
src1={}
for r in ded: src1.setdefault(r['代码'],float(r['龙虎榜净买额']))
ds=json.load(open('_学习/龙虎榜双源校验_20261023.json',encoding='utf-8'))
flag={r['代码']:r['判定'] for r in ds['全量']}
rows=list(csv.DictReader(open('_学习/_席位动向/20261023.csv',encoding='utf-8')))
dd=[r for r in rows if not is_int(r['类型']) and r['代码'][:2] not in ('11','12','90','20')]
seen=set();Q=[]
for r in dd:
    k=(r['代码'],r['席位'])
    if k in seen: continue
    seen.add(k);Q.append(r)
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def dg(s):
    v=pj.get(s);return v['档'] if v else '未入档'
sa=defaultdict(list)
for r in Q:
    if dg(r['席位']) in ('S','A'): sa[r['代码']].append((dg(r['席位']),r['席位'],float(r['买入金额'])))
def fb(c):
    z=zt[c]; return float(z['封板资金'])/float(z['成交额'])*100
def ok3(c):
    z=zt[c]; return fb(c)>=5 and int(z['炸板次数'])<=3 and z['首次封板时间']<='140000'
onboard={r['代码'] for r in ded}
print('涨停',len(zt))
s1=[c for c in zt if c in onboard]; print('∩当日榜',len(s1))
s2=[c for c in s1 if src1.get(c,0)>0]; print('∩源1>0',len(s2))
s3=[c for c in s2 if ok3(c)]; print('∩封板三项',len(s3),s3)
s4=[c for c in s3 if c in sa]; print('∩S/A',len(s4),s4)
s5=[c for c in zt if c in sa]; print('S/A在场涨停',len(s5),s5)
s6=[c for c in s5 if ok3(c) and src1.get(c,0)>0]; print('S/A∩封板∩源1>0',len(s6),s6)
print('--- 明细 ---')
for c in sorted(set(s3)|set(s5)):
    z=zt[c]
    print(c,z['名称'][:6],'封单%.2f%%'%fb(c),'炸',z['炸板次数'],'首封',z['首次封板时间'],'源1%.3f亿'%(src1.get(c,0)/1e8),'flag',flag.get(c),'SA',sa.get(c))
print('覆盖率 %.1f%%'%(len(s1)/len(zt)*100))
