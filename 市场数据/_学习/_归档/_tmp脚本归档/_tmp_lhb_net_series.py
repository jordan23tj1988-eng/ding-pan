# -*- coding: utf-8 -*-
import csv,json,os,glob,importlib.util
from collections import defaultdict
spec=importlib.util.spec_from_file_location('st','席位荐票结算.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def is_int(t): return any(k in t for k in ['连续','累计','严重异常'])
pj=json.load(open('_学习/_席位分档.json',encoding='utf-8'))['席位']
def dg(seat):
    v=pj.get(seat); return v['档'] if v else '未入档'
days=sorted([os.path.basename(p)[:-4] for p in glob.glob('_学习/_席位动向/2026*.csv')])[-12:]
ser=[]
for d in days:
    rows=list(csv.DictReader(open(f'_学习/_席位动向/{d}.csv',encoding='utf-8')))
    dd=[r for r in rows if not is_int(r['类型']) and r['代码'][:2] not in ('11','12','90','20')]
    seen=set(); Q=[]
    for r in dd:
        k=(r['代码'],r['席位'])
        if k in seen: continue
        seen.add(k); Q.append(r)
    ta=sum(float(r['买入金额']) for r in Q)
    sa=[r for r in Q if dg(r['席位']) in ('S','A') and float(r['买入金额'])>=1e7]
    saa=sum(float(r['买入金额']) for r in sa)
    A=[r for r in Q if dg(r['席位'])=='A']
    Anet=sum(float(r['净额']) for r in A)
    lhb=os.path.join(d,'lhb.csv')
    flag={}; src1={}
    fz=f'_学习/龙虎榜双源校验_{d}.json'
    if os.path.isfile(fz):
        ds=json.load(open(fz,encoding='utf-8'))
        flag={r['代码']:r['判定'] for r in ds['全量']}; src1={r['代码']:r['源1净买亿'] for r in ds['全量']}
    else:
        L=list(csv.DictReader(open(lhb,encoding='utf-8-sig'))) if os.path.isfile(lhb) else []
        for r in L:
            if not is_int(r['上榜原因']): src1.setdefault(r['代码'],float(r['龙虎榜净买额'])/1e8)
        sn=defaultdict(float)
        for r in Q: sn[r['代码']]+=float(r['净额'])/1e8
        for c in src1:
            diff=abs(sn.get(c,0)-src1[c])
            flag[c]='强矛盾' if (sn.get(c,0)*src1[c]<0 and max(abs(sn.get(c,0)),abs(src1[c]))>1) else ('一致' if diff<1 else '打折')
    zt={}
    zp=os.path.join(d,'zt_pool.csv')
    if os.path.isfile(zp):
        for r in csv.DictReader(open(zp,encoding='utf-8-sig')): zt[r['代码']]=r
    def okz(c):
        z=zt.get(c)
        if not z: return False
        try: fb=float(z['封板资金'])/float(z['成交额'])*100
        except: return False
        return fb>=5 and int(z['炸板次数'])<=3 and str(z['首次封板时间']).zfill(6)<='140000'
    Aok=sum(float(r['净额']) for r in A if flag.get(r['代码'])!='强矛盾' and (src1.get(r['代码']) or 0)>0)
    Aok2=sum(float(r['净额']) for r in A if flag.get(r['代码'])!='强矛盾' and (src1.get(r['代码']) or 0)>0 and okz(r['代码']))
    net=m.lhb_net_stock(d)
    ser.append(dict(日=d, 笔数=len(Q), 全榜买额亿=round(ta/1e8,2),
        SA笔数=len(sa), SA占比pct=round(len(sa)/len(Q)*100,2) if Q else None,
        SA买额亿=round(saa/1e8,2), SA买额占全榜pct=round(saa/ta*100,2) if ta else None,
        A档净额亿=round(Anet/1e8,3),
        A档可用_非强矛盾源1正_pct=round(Aok/Anet*100,1) if Anet else None,
        A档可用_过封板三项_pct=round(Aok2/Anet*100,1) if Anet else None,
        lhb_net_stock_dedup=net.get('lhb_net_stock_dedup'),
        lhb_net_stock_with_interval=net.get('lhb_net_stock_with_interval'),
        双源_状态=('script' if os.path.isfile(fz) else 'selfbuilt')))
out=dict(产出='MA-20261022-05①②③ 落盘件', 生成时间='20261023晚',
  口径=dict(S='股票口径: 剔区间累计榜 + 按(代码,席位)去重 + 剔 11/12/90/20 开头; 一笔=席位净买>0 且 买额>=1000万',
            A档可用='A档净额中落在「双源非强矛盾 ∧ 股票级净额>0」的占比; 加「封板三项(封单比>=5% ∧ 炸<=3 ∧ 首封<=14:00)」为更严版本',
            净额='lhb_net_stock_dedup=剔区间榜每码1行; lhb_net_stock_with_interval=含区间榜全行; ★区间榜是3日/10日累计,不可与日榜相加'),
  逐日=ser,
  今日自检=m.selftest_lhb_net('20261023'),
  今日同码多行=m.lhb_net_stock('20261023').get('同码多行清单'))
json.dump(out,open('_学习/lhb净额双值_20261023.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for r in ser: print(r)
