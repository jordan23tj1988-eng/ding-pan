import csv,json
from collections import defaultdict,Counter
D='20261023'
# 1. 席位动向
rows=list(csv.DictReader(open(f'_学习/_席位动向/{D}.csv',encoding='utf-8')))
print('动向行',len(rows))
print('类型样例',Counter(r['类型'] for r in rows).most_common(5))
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
ded=[r for r in rows if not is_int(r['类型'])]
itv=[r for r in rows if is_int(r['类型'])]
print('剔区间榜后',len(ded),'区间榜',len(itv))
seen=set(); ded2=[]
for r in ded:
    k=(r['代码'],r['席位'])
    if k in seen: continue
    seen.add(k); ded2.append(r)
print('去重后笔数',len(ded2),'唯一代码',len({r['代码'] for r in ded2}))
# 2. 分档
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def rank(name):
    v=pj.get(name)
    return v if v else None
cnt=Counter(); amt=defaultdict(float); net=defaultdict(float)
minbought=1e7
SA=[]
for r in ded2:
    v=rank(r['席位'])
    dg=v['档'] if v else '未入档'
    cnt[dg]+=1; amt[dg]+=float(r['买入金额']); net[dg]+=float(r['净额'])
    if dg in ('S','A') and float(r['买入金额'])>=minbought:
        SA.append((dg,r['代码'],r['名称'],r['席位'],float(r['买入金额']),float(r['净额']),v))
tot=len(ded2); totamt=sum(float(r['买入金额']) for r in ded2); totnet=sum(float(r['净额']) for r in ded2)
print(f'总买额 {totamt/1e8:.2f}亿 总净额 {totnet/1e8:.3f}亿')
for dg in ['S','A','B','C','P','未入档']:
    print(f'{dg}: {cnt[dg]}笔 {cnt[dg]/tot*100:.2f}% 买额{amt[dg]/1e8:.2f}亿 净额{net[dg]/1e8:.3f}亿')
sa_n=cnt['S']+cnt['A']; sa_amt=(amt['S']+amt['A'])
print(f'S/A {sa_n}笔={sa_n/tot*100:.2f}% 买额{sa_amt/1e8:.2f}亿={sa_amt/totamt*100:.1f}% 净额{(net["S"]+net["A"])/1e8:.3f}亿')
print(f'S档 {cnt["S"]}笔 买额{amt["S"]/1e8:.3f}亿 净额{net["S"]/1e8:.3f}亿 单笔max{max([float(r["买入金额"]) for r in ded2 if rank(r["席位"]) and rank(r["席位"])["档"]=="S"] or [0])/1e8:.3f}亿')
print('--- S/A 明细(买额>=1000万) ---')
for dg,code,nm,seat,b,n,v in sorted(SA,key=lambda x:-x[4]):
    print(f'{dg} {code} {nm} | {seat} | 买{b/1e8:.3f}亿 净{n/1e8:.3f}亿 | n={v["样本"]} 收缩{v["收缩执1胜率"]}% 均{v["收缩执1均涨"]}% 小样本={v["小样本"]} {v["通道"]}')
json.dump([{'档':d,'代码':c,'名称':n,'席位':s,'买额':b,'净额':n,'样本':v['样本'],'收缩胜率':v['收缩执1胜率'],'收缩均涨':v['收缩执1均涨'],'小样本':v['小样本'],'通道':v['通道']} for d,c,n,s,b,n2,v in SA],open('_学习/_tmp_sa1023.json','w',encoding='utf-8'),ensure_ascii=False)
print('--- 今日 S/A 席位按票聚合 ---')
byc=defaultdict(list)
for dg,code,nm,seat,b,n,v in SA: byc[(code,nm)].append((dg,seat,b,n,v))
for (c,n),lst in sorted(byc.items(),key=lambda x:-sum(y[2] for y in x[1])):
    print(c,n,'S/A笔',len(lst),'买额合计%.3f亿'%(sum(y[2] for y in lst)/1e8),'净额%.3f亿'%(sum(y[3] for y in lst)/1e8))
