import csv,json
from collections import defaultdict
D='20261023'
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
zt=list(csv.DictReader(open(f'{D}/zt_pool.csv',encoding='utf-8-sig')))
print('涨停',len(zt))
lhb=list(csv.DictReader(open(f'{D}/lhb.csv',encoding='utf-8-sig')))
ded=[r for r in lhb if not is_int(r['上榜原因'])]
byc=defaultdict(list)
for r in ded: byc[r['代码']].append(r)
A=sum(float(r['龙虎榜净买额']) for r in ded)
B=sum(float(r['龙虎榜净买额']) for r in lhb)
print(f'值A(lhb_net_stock_dedup) {A/1e8:.4f}亿 正{sum(1 for r in ded if float(r["龙虎榜净买额"])>0)}/{len(ded)}行 唯一码{len(byc)}')
print(f'值B(lhb_net_stock_with_interval) {B/1e8:.4f}亿 正{sum(1 for r in lhb if float(r["龙虎榜净买额"])>0)}/{len(lhb)}行')
# 每码取当日榜唯一净额（同码多行：取上榜原因非区间且金额最大？先列重复）
for c,rs in byc.items():
    if len(rs)>1:
        print('同码多行',c,rs[0]['名称'],[ (r['上榜原因'],r['龙虎榜净买额']) for r in rs])
# 双源 flag
ds=json.load(open(f'_学习/龙虎榜双源校验_20261023.json',encoding='utf-8'))
flag={r['代码']:r['判定'] for r in ds['全量']}
src1={r['代码']:r['源1净买亿'] for r in ds['全量']}
src2={r['代码']:r['源2买侧净额亿'] for r in ds['全量']}
# 席位 S/A per code (股票only)
rows=list(csv.DictReader(open(f'_学习/_席位动向/{D}.csv',encoding='utf-8')))
dd=[r for r in rows if not is_int(r['类型'])]
seen=set(); Q=[]
for r in dd:
    k=(r['代码'],r['席位'])
    if k in seen: continue
    seen.add(k); Q.append(r)
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def dgof(seat):
    v=pj.get(seat); return v['档'] if v else '未入档'
sa=defaultdict(list)
for r in Q:
    if r['代码'][:2] in ('11','12'): continue
    d=dgof(r['席位'])
    if d in ('S','A') and float(r['买入金额'])>=1e7:
        v=pj[r['席位']]
        sa[r['代码']].append({'档':d,'席位':r['席位'],'买':float(r['买入金额']),'净':float(r['净额']),'n':v['样本'],'收缩':v['收缩执1胜率'],'均':v['收缩执1均涨'],'小样本':v['小样本'],'通道':v['通道']})
# 漏斗
ups=[z for z in zt if float(z['涨跌幅'])>9]
print('涨停数',len(zt))
inlhb=[z for z in zt if z['代码'] in byc]
print('∩当日榜',len(inlhb))
n1=[z for z in inlhb if float(byc[z['代码']][0]['龙虎榜净买额'])>0]
print('∩源1净买>0',len(n1),[ (z['代码'],z['名称'],round(float(byc[z['代码']][0]['龙虎榜净买额'])/1e8,3)) for z in n1])
def fb(z):
    f=float(z['封板资金']); amt=float(z['成交额']); return f/amt*100 if amt else 0
def ok(z):
    return fb(z)>=5 and int(z['炸板次数'])<=3 and z['首次封板时间']<='140000'
n2=[z for z in n1 if ok(z)]
print('∩封板三项',len(n2),[(z['代码'],z['名称'],round(fb(z),2),z['炸板次数'],z['首次封板时间']) for z in n2])
n3=[z for z in n2 if z['代码'] in sa]
print('∩S/A席在场',len(n3),[(z['代码'],z['名称']) for z in n3])
print('封板三项过但无S/A',[(z['代码'],z['名称']) for z in n2 if z['代码'] not in sa])
print('S/A在场涨停票(全部)',[(z['代码'],z['名称'],round(fb(z),2),z['炸板次数'],z['首次封板时间'],flag.get(z['代码'])) for z in inlhb if z['代码'] in sa])
print('--- S/A代码明细(含非涨停) ---')
for c,lst in sa.items():
    nm=next((r['名称'] for r in Q if r['代码']==c),'')
    print(c,nm,'flag=',flag.get(c),'源1=',src1.get(c),'源2=',src2.get(c),'|','; '.join(f"{x['档']}{x['席位'][:14]} 买{x['买']/1e8:.3f} 净{x['净']/1e8:.3f} n={x['n']} 收缩{x['收缩']}%" for x in lst))
json.dump({'sa':{k:v for k,v in sa.items()},'flag':flag,'src1':src1,'src2':src2},open('_学习/_tmp_ctx1023.json','w',encoding='utf-8'),ensure_ascii=False,default=float)
