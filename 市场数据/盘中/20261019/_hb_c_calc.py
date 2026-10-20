# hb-c 20261019 11:00 场 计算器 —— 只做机械对齐, 不做推断补数
import json, urllib.request, os
D='盘中/20261019'
DEC_TS='2026-10-19 11:11:00'   # 决断时间戳(固定写入, 之后取"下一tick")

# ---- 1. 已留档 tick 帧(截止性: 只统计 <=DEC_TS 的帧) ----
frames=[json.loads(l) for l in open(f'{D}/realtime_ticks.jsonl',encoding='utf-8') if l.strip()]
pre=[f for f in frames if f['ts']<=DEC_TS]
last=pre[-1]
print('frames total',len(frames),'| <=dec',len(pre),'| last',last['ts'],'| stale_min', round((11*60+11-(int(last['ts'][11:13])*60+int(last['ts'][14:16]))),1))

pool={r['code']:r for r in last['rows']}
# ---- 2. 腾讯/东财 实时(11:0x) 覆盖非池票 ----
extra={}
def em(code):
    sec='1' if code[0]=='6' else '0'
    url=f'https://push2.eastmoney.com/api/qt/stock/get?secid={sec}.{code}&fields=f43,f44,f45,f46,f47,f58,f60,f170'
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    d=json.loads(urllib.request.urlopen(req,timeout=10).read().decode())['data']
    return dict(code=code,name=d['f58'],latest=d['f43']/100,open=d['f46']/100,high=d['f44']/100,
                low=d['f45']/100,preClose=d['f60']/100,pct=d['f170']/100)
for c in ['002860','605189','603968','000011','000601','000823','600693','600668','600802','300045']:
    extra[c]=em(c)
json.dump({'fetched_at':'11:07:2x','src':'东财push2','quotes':extra},open(f'{D}/_hb_c_quote_1107.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

# ---- 3. 预案失效线机械核对 ----
def gap(q): return round((q['open']-q['preClose'])/q['preClose']*100,2)
checks={
 '300045':dict(kind='buy_gate',band=(-3.0,5.0)),
 '600802':dict(kind='sub_gate',band=(-3.0,3.0)),
 '000011':dict(kind='invalidate',gap_le=-4.0),
 '600668':dict(kind='invalidate',gap_le=-4.0,cost=8.15),
 '000601':dict(kind='invalidate',cost=6.68,ma10=6.275,low1016=6.45),
 '000823':dict(kind='invalidate',cost=25.13,ma20=23.706),
 '002860':dict(kind='sell_open',cost=20.08),
 '605189':dict(kind='sell_open',cost=17.97),
 '603968':dict(kind='sell_open',cost=14.3),
 '600693':dict(kind='not_in_plan',cost=12.40),
}
out={}
for c,k in checks.items():
    q=extra[c]; g=gap(q)
    row=dict(代码=c,名称=q['name'],open=q['open'],preClose=q['preClose'],gap_pct=g,
             latest=q['latest'],pct=q['pct'],high=q['high'],low=q['low'],
             vs_cost_pct=round((q['latest']-k['cost'])/k['cost']*100,2) if k.get('cost') else None,
             from_open_pct=round((q['latest']-q['open'])/q['open']*100,2),
             from_high_pct=round((q['latest']-q['high'])/q['high']*100,2))
    if k['kind']=='buy_gate':
        row['gate']=list(k['band']); row['verdict']='出带(上沿)' if g>k['band'][1] else ('出带(下沿)' if g<k['band'][0] else '入带')
    if k['kind']=='sub_gate':
        row['gate']=list(k['band']); row['verdict']='入带' if k['band'][0]<=g<=k['band'][1] else '出带'
    if k['kind']=='invalidate':
        row['gap_le']=k.get('gap_le'); row['gap_trig']=(g<=k['gap_le']) if k.get('gap_le') is not None else None
        if 'ma10' in k: row['ma10']=k['ma10']; row['ma10_trig']=q['latest']<k['ma10']
        if 'low1016' in k: row['low1016']=k['low1016']; row['low_trig']=q['latest']<k['low1016']
        if 'ma20' in k: row['ma20']=k['ma20']; row['ma20_trig']=q['latest']<k['ma20']
    out[c]=row
print(json.dumps(out,ensure_ascii=False,indent=1))

# ---- 4. 池内环境(11:05 帧) ----
def est(f):
    rows=f['rows']; pcts=[r['pct'] for r in rows]; lu=[];zb=[]
    for r in rows:
        f10=r['code'].startswith('3') or r['code'].startswith('68')
        lim=round(r['preClose']*(1.2 if f10 else 1.1),2)
        if abs(r['latest']-lim)<0.011: lu.append(r['code'])
        elif abs(r['high']-lim)<0.011: zb.append(r['code'])
    sp=sorted(pcts); return len(lu),len(zb),round(sp[len(sp)//2],2),round(sum(pcts)/len(pcts),2),min(pcts),max(pcts)
env={'09:31':est(frames[0]),'10:30':est([f for f in frames if f['ts']<='2026-10-19 10:30:00'][-1]),'11:05':est(pre[-1])}
print('env(锁板,炸板,中位,均值,min,max)',env)

json.dump({'dec_ts':DEC_TS,'last_frame':last['ts'],'frames_used':len(pre),'checks':out,'env':env,
           'pool_date':last.get('pool_date'),'pool_stale':last.get('pool_stale')},
          open(f'{D}/_hb_c_calc.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
