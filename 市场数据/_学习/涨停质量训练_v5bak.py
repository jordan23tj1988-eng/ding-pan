# -*- coding: utf-8 -*-
"""涨停质量训练.py v5 [--fetch] —— 多因子涨停质量评分·每晚自动循环。
v3(2026-07-10,用户拍板"因子远远不够且同质化"):
- 因子2→14(全部T日收盘可知,零后视镜):首封/封单比/连板/开板/换手/市值/股价/涨停基因/
  量比/60日位置/板前动能/行业共振/题材共振(数据攒够自动激活)/涨停环境。
- ★因子有效性自动评估:每晚全量重算→区分度(桶间执1胜率极差)×单调性(spearman)→
  区分度<3pp或样本不足自动淘汰;近10日方向与全窗翻转的自动降权50%(时效衰减)。
- 质量分=有效因子加权评分卡(执行口径为主:T+1开买入→执1/执2);1641级样本撑不起高维交叉,评分卡稳健。
- 每晚快照记全部因子 权重/方向/区分度/状态 → _涨停质量库快照.jsonl,自我进化可追溯。
v4(2026-07-10,用户拍板"温度+分板量化"): 因子14→16(+封单绝对额/市场温度[市场温度.py产,滚动250日分位0-100]);
连板桶细化首板/2板/3板/4板+;新增分板胜率库(一维观察基准+连板×封单比+连板×温度交叉,执行口径为主)。
自动循环:18:00定时任务 市场温度.py→本脚本--fetch → 荐票 → 次日结算 → 近窗翻转校准,无人工干预。"""
import os,sys,glob,json,datetime
import pandas as pd,numpy as np
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache"); os.makedirs(CDIR,exist_ok=True)
MINB=25; RECENT=10; MIN_DISC=3.0

# ---------- 分桶(值→桶标签;order=底层变量升序,方向由rho自动判) ----------
def _c(v):
    return None if (v is None or v!=v) else v
def b_首封(r):
    v=_c(r.get('首封'))
    if v is None: return None
    return '一字≤9:25' if v<='09:25' else '秒板≤9:31' if v<='09:31' else '早盘≤10:00' if v<='10:00' else ('盘中10-14' if v<='14:00' else '尾盘>14')
def b_封单(r):
    v=_c(r.get('封单比'))
    if v is None: return None
    return '弱<0.5%' if v<0.5 else '偏弱0.5-1%' if v<1 else '中1-2%' if v<2 else '强2-4%' if v<4 else '超强≥4%'
def b_连板(r):
    v=_c(r.get('连板'));  return None if v is None else ('首板' if v<=1 else '2板' if v==2 else '3板' if v==3 else '4板+')
def b_开板(r):
    v=_c(r.get('开板'));  return None if v is None else ('未开板' if v==0 else '开1次' if v==1 else '开2次+')
def b_换手(r):
    v=_c(r.get('换手'));  return None if v is None else ('<3%' if v<3 else '3-10%' if v<10 else '10-20%' if v<20 else '≥20%')
def b_市值(r):
    v=_c(r.get('市值亿')); return None if v is None else ('微盘<30亿' if v<30 else '小盘30-80亿' if v<80 else '中盘80-200亿' if v<200 else '大盘≥200亿')
def b_股价(r):
    v=_c(r.get('股价'));  return None if v is None else ('<5元' if v<5 else '5-15元' if v<15 else '15-40元' if v<40 else '≥40元')
def b_基因(r):
    v=_c(r.get('基因'));  return None if v is None else ('0次' if v==0 else '1-2次' if v<=2 else '3次+')
def b_量比(r):
    v=_c(r.get('量比'));  return None if v is None else ('缩量<1' if v<1 else '温和1-2' if v<2 else '放量2-4' if v<4 else '爆量≥4')
def b_位置(r):
    v=_c(r.get('位置'));  return None if v is None else ('低位<0.7' if v<0.7 else '半山0.7-0.9' if v<0.9 else '高位0.9-99.5%' if v<0.995 else '新高≥99.5%')
def b_动能(r):
    v=_c(r.get('动能'));  return None if v is None else ('回调<-3%' if v<-3 else '平稳-3~3%' if v<3 else '抬升3-12%' if v<12 else '过热≥12%')
def b_行业(r):
    v=_c(r.get('行业家数')); return None if v is None else ('孤板1只' if v<=1 else '2-3只' if v<=3 else '4只+')
def b_题材(r):
    v=_c(r.get('题材家数')); return None if v is None else ('孤板1只' if v<=1 else '2-3只' if v<=3 else '4-6只' if v<=6 else '7只+')
def b_环境(r):
    v=_c(r.get('涨停总数')); return None if v is None else ('冰点<45' if v<45 else '常态45-70' if v<70 else '活跃70-100' if v<100 else '过热≥100')
def b_封额(r):
    v=_c(r.get('封额亿'));  return None if v is None else ('<0.5亿' if v<0.5 else '0.5-1.5亿' if v<1.5 else '1.5-4亿' if v<4 else '≥4亿')
def b_温度(r):
    v=_c(r.get('温度'));  return None if v is None else ('冰点<25' if v<25 else '偏冷25-45' if v<45 else '中性45-65' if v<65 else '偏热65-85' if v<85 else '过热≥85')
FACTORS={
 '首封时间':(b_首封,['一字≤9:25','秒板≤9:31','早盘≤10:00','盘中10-14','尾盘>14']),
 '封单比':(b_封单,['弱<0.5%','偏弱0.5-1%','中1-2%','强2-4%','超强≥4%']),
 '连板':(b_连板,['首板','2板','3板','4板+']),
 '开板次数':(b_开板,['未开板','开1次','开2次+']),
 '换手率':(b_换手,['<3%','3-10%','10-20%','≥20%']),
 '流通市值':(b_市值,['微盘<30亿','小盘30-80亿','中盘80-200亿','大盘≥200亿']),
 '股价档':(b_股价,['<5元','5-15元','15-40元','≥40元']),
 '涨停基因10日':(b_基因,['0次','1-2次','3次+']),
 '量比':(b_量比,['缩量<1','温和1-2','放量2-4','爆量≥4']),
 '60日位置':(b_位置,['低位<0.7','半山0.7-0.9','高位0.9-99.5%','新高≥99.5%']),
 '板前5日动能':(b_动能,['回调<-3%','平稳-3~3%','抬升3-12%','过热≥12%']),
 '行业共振':(b_行业,['孤板1只','2-3只','4只+']),
 '题材共振':(b_题材,['孤板1只','2-3只','4-6只','7只+']),
 '涨停环境':(b_环境,['冰点<45','常态45-70','活跃70-100','过热≥100']),
 '封单额':(b_封额,['<0.5亿','0.5-1.5亿','1.5-4亿','≥4亿']),
 '市场温度':(b_温度,['冰点<25','偏冷25-45','中性45-65','偏热65-85','过热≥85']),
}

def _tradedays():
    return sorted([os.path.basename(x) for x in glob.glob(os.path.join(BASE,'2026*'))
                   if os.path.isdir(x) and os.path.isfile(os.path.join(x,'zt_pool.csv'))])

def _hhmm(ts):
    if not ts: return None
    import datetime as _dt
    try: return _dt.datetime.fromtimestamp(int(ts),tz=_dt.timezone(_dt.timedelta(hours=8))).strftime('%H:%M')
    except Exception: return None
def _hd_str(s):
    import re
    m=_re2.search(r'(\d+)板',str(s or ''))
    return int(m.group(1)) if m else 1
import re as _re2
def _cache_meta(c):
    """从本地导出缓存取(date→换手%,流通市值亿,收盘):历史样本补EM缺失字段。"""
    f=os.path.join(CDIR,c+'.csv')
    if not os.path.isfile(f): return {}
    try:
        b=pd.read_csv(f)
        if 'turnover' not in b.columns: return {}
        b['date']=b['date'].astype(str).str.replace('-','')
        return {d:(t,m,cl) for d,t,m,cl in zip(b['date'],b['turnover'],b['circ_mv亿'],b['close'])}
    except Exception: return {}

def _factor_table():
    """全历史涨停样本的因子表(不含前向),全部T日收盘可知。"""
    days=_tradedays(); rows=[]
    for d in days:
        df=pd.read_csv(os.path.join(BASE,d,'zt_pool.csv'),dtype={'代码':str})
        df['代码']=df['代码'].str.zfill(6)
        df=df[~df['名称'].astype(str).str.contains('退')]   # 剔退市整理股:涨跌幅规则不同,污染样本(2026-07-10国华退+25%教训)
        for _,r in df.iterrows():
            mv=pd.to_numeric(r.get('流通市值'),errors='coerce'); fj=pd.to_numeric(r.get('封板资金'),errors='coerce')
            fb=str(r['首次封板时间']).split('.')[0].zfill(6)
            rows.append(dict(日=d,代码=r['代码'],名称=r.get('名称'),
                封额亿=round(float(fj)/1e8,2) if fj==fj else None,
                封单比=round(float(fj)/float(mv)*100,3) if (mv and mv>0 and fj==fj) else None,
                首封=fb[:2]+':'+fb[2:4],
                连板=int(pd.to_numeric(r.get('连板数',1),errors='coerce') or 1),
                开板=int(pd.to_numeric(r.get('炸板次数',0),errors='coerce') or 0),
                换手=float(pd.to_numeric(r.get('换手率'),errors='coerce')),
                市值亿=float(mv)/1e8 if mv==mv else None,
                股价=float(pd.to_numeric(r.get('最新价'),errors='coerce')),
                行业=str(r.get('所属行业'))))
    # ★v5 THS历史池样本(2025-07起,一年):EM缺字段用网盘导出缓存补(换手/流通市值→封单比),零编造缺则null
    tp=os.path.join(L,'_ths_zt_pool.json')
    if os.path.isfile(tp):
        ths=json.load(open(tp,encoding='utf-8'))
        indmap={}
        for d in days:
            df0=pd.read_csv(os.path.join(BASE,d,'zt_pool.csv'),dtype={'代码':str})
            for c,i in zip(df0['代码'].str.zfill(6),df0['所属行业']): indmap[c]=i
        metac={}
        for d in sorted(ths):
            if d in days: continue
            for x in ths[d]:
                c=str(x.get('code','')).zfill(6); nm=str(x.get('name') or '')
                if '退' in nm: continue
                if c not in metac: metac[c]=_cache_meta(c)
                mt=metac[c].get(d)
                hs=float(mt[0]) if (mt and mt[0]==mt[0]) else None
                mv=float(mt[1]) if (mt and mt[1]==mt[1]) else None
                fj=x.get('order_amount')
                rows.append(dict(日=d,代码=c,名称=nm,
                    封额亿=round(fj/1e8,2) if fj else None,
                    封单比=round(fj/(mv*1e8)*100,3) if (fj and mv and mv>0) else None,
                    首封=_hhmm(x.get('first_limit_up_time')),
                    连板=_hd_str(x.get('high_days')),
                    开板=int(x.get('open_num') or 0),
                    换手=hs,市值亿=mv,
                    股价=float(x.get('latest')) if x.get('latest') else None,
                    行业=indmap.get(c)))
    P=pd.DataFrame(rows)
    P['涨停总数']=P.groupby('日')['代码'].transform('size')
    P['行业家数']=P.groupby(['日','行业'])['代码'].transform('size')
    all_days=sorted(P['日'].unique())
    di={d:i for i,d in enumerate(all_days)}; occ={}
    for c,d in zip(P['代码'],P['日']): occ.setdefault(c,[]).append(di[d])
    P['基因']=[sum(1 for j in occ[c] if di[d]-10<=j<di[d]) for c,d in zip(P['代码'],P['日'])]
    tm={}   # 题材共振:涨停对链条_{d}.json(全量归位真源;题材归位_{d}.json只是override增量,勿用)
    for f in glob.glob(os.path.join(L,'涨停对链条_*.json')):
        d=os.path.basename(f).replace('涨停对链条_','')[:8]
        try:
            j=json.load(open(f,encoding='utf-8'))
            mp={}
            for t in j.get('题材线',[]):
                for s in t.get('环节',[]):
                    for g in s.get('个股',[]): mp[g['代码']]=t['大方向']
            cnt={}
            for v in mp.values(): cnt[v]=cnt.get(v,0)+1
            tm[d]={k:cnt.get(v) for k,v in mp.items()}   # 待归位股不在mp→None(不硬归)
        except Exception: pass
    P['题材家数']=[ (tm.get(d) or {}).get(c) for c,d in zip(P['代码'],P['日']) ]
    wp=os.path.join(L,'_市场温度表.json')   # v4: 市场温度截面因子(市场温度.py产,T日收盘可知)
    wt=json.load(open(wp,encoding='utf-8')) if os.path.isfile(wp) else {}
    P['温度']=[ (wt.get(d) or {}).get('温度') for d in P['日'] ]
    return P

def _bars(c):
    f=os.path.join(CDIR,c+".csv")
    if not os.path.isfile(f): return None
    try:
        b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
        return b.reset_index(drop=True)
    except Exception: return None

def _enrich(P,forward=True):
    """K线因子(量比/位置/动能)+前向(E1/E2执行,T1/T2信号)。"""
    cache={}; out={k:[] for k in ['量比','位置','动能','E1','E2','T1','T2']}
    for _,r in P.iterrows():
        c=r['代码']
        if c not in cache: cache[c]=_bars(c)
        b=cache[c]; v={k:np.nan for k in out}
        if b is not None:
            idx=b.index[b['date']==r['日']]
            if len(idx):
                i=idx[0]; has_vol='volume' in b.columns
                if has_vol and i>=4:
                    pv=b['volume'].iloc[max(0,i-5):i]
                    if len(pv)>=3 and pv.mean()>0: v['量比']=round(float(b.loc[i,'volume'])/float(pv.mean()),2)
                if i>=19:
                    mx=b['close'].iloc[max(0,i-59):i+1].max()
                    if mx>0: v['位置']=round(float(b.loc[i,'close'])/float(mx),4)
                if i>=6 and b.loc[i-6,'close']>0:
                    v['动能']=round((float(b.loc[i-1,'close'])/float(b.loc[i-6,'close'])-1)*100,2)
                if forward and i+1<len(b):
                    Tc=b.loc[i,'close']; o1=b.loc[i+1,'open']
                    if Tc>0: v['T1']=b.loc[i+1,'close']/Tc-1
                    if o1 and o1>0:
                        v['E1']=b.loc[i+1,'close']/o1-1
                        if i+2<len(b):
                            v['E2']=b.loc[i+2,'close']/o1-1
                            if Tc>0: v['T2']=b.loc[i+2,'close']/Tc-1
        for k in out: out[k].append(v[k])
    for k in out: P[k]=out[k]
    return P

def _fetch(codes,last_map=None):
    import akshare as ak
    from concurrent.futures import ThreadPoolExecutor
    def needs(c):
        f=os.path.join(CDIR,c+".csv")
        if not os.path.isfile(f): return True
        try:
            head=open(f,encoding='utf-8').readline()
            if 'volume' not in head: return True   # v3扩列:旧3列缓存强制重拉
            if not last_map or c not in last_map: return False
            b=pd.read_csv(f); dates=b['date'].astype(str).str.replace('-','')
            return int((dates>str(last_map[c])).sum())<2
        except Exception: return True
    todo=[c for c in codes if needs(c)]
    print(f"fetch增量: {len(todo)}/{len(codes)}",flush=True)
    def one(c):
        try:
            pre="bj" if (c[0] in "48" or c.startswith("92")) else ("sh" if c[0] in "69" else "sz")
            b=ak.stock_zh_a_daily(symbol=pre+c,start_date="20250601",end_date=datetime.date.today().strftime("%Y%m%d"))
            b=b[["date","open","high","low","close","volume"]].copy()
            f=os.path.join(CDIR,c+".csv")
            if os.path.isfile(f):
                try:
                    ob=pd.read_csv(f)
                    if 'turnover' in ob.columns:   # 本地导出缓存:只用sina续尾部,保留turnover/circ_mv列
                        b['date']=b['date'].astype(str); mx=str(ob['date'].max())
                        nb=b[b['date']>mx].copy()
                        if len(nb):
                            nb['turnover']=None; nb['circ_mv亿']=None
                            pd.concat([ob,nb[ob.columns]]).to_csv(f,index=False)
                        return
                except Exception: pass
            b.to_csv(f,index=False)
        except Exception as e: open(os.path.join(CDIR,c+".err"),"w").write(str(e)[:80])
    with ThreadPoolExecutor(max_workers=16) as ex: list(ex.map(one,todo))

def _agg(g):
    def wr(col):
        v=g[col].dropna()
        return (round((v>0).mean()*100,1),round(v.mean()*100,2)) if len(v) else (None,None)
    t1w,t1r=wr('T1'); t2w,t2r=wr('T2'); e1w,e1r=wr('E1'); e2w,e2r=wr('E2')
    v2=g['E2'].dropna()
    return dict(n=int(len(g)),T1胜率=t1w,T1均涨=t1r,T2胜率=t2w,T2均涨=t2r,
                执1胜率=e1w,执1均涨=e1r,执2胜率=e2w,执2均涨=e2r,
                抓龙率=round((v2>=0.08).mean()*100,1) if len(v2) else None)
def _bscore(st):
    if st.get('执1胜率') is None: return None
    cl=lambda x:max(0.,min(1.,x))
    return round(100*(0.5*cl((st['执1胜率']-40)/35)+0.3*cl((st['执1均涨'] or 0)/2)+0.2*cl((st.get('执2均涨') or 0)/3)),1)
def _spear(a,b):
    try:
        ra=pd.Series(a,dtype=float).rank(); rb=pd.Series(b,dtype=float).rank()
        v=float(np.corrcoef(ra,rb)[0,1])   # rank相关=spearman,不依赖scipy(沙箱重置友好)
        return None if v!=v else round(v,3)
    except Exception: return None

# ★v5 规则原子(T日收盘可知,None安全)——规则榜=组合条件取代加权平均排序(2026-07-10用户拍板)
def _gev(v,x): return v is not None and v==v and v>=x
ATOMS={
 '回封':lambda r:_gev(r.get('开板'),1),
 '未开板':lambda r:(r.get('开板') or 0)==0 and r.get('开板') is not None,
 '封单额≥1.5亿':lambda r:_gev(r.get('封额亿'),1.5),
 '封单额≥4亿':lambda r:_gev(r.get('封额亿'),4),
 '封单比≥2%':lambda r:_gev(r.get('封单比'),2),
 '爆量≥2':lambda r:_gev(r.get('量比'),2),
 '换手≥10%':lambda r:_gev(r.get('换手'),10),
 '早封≤10:00':lambda r:(r.get('首封') or '')!='' and r['首封']<='10:00',
 '一字≤9:25':lambda r:(r.get('首封') or '')!='' and r['首封']<='09:25',
 '2板+':lambda r:_gev(r.get('连板'),2),
 '3板+':lambda r:_gev(r.get('连板'),3),
 '涨停基因≥1':lambda r:_gev(r.get('基因'),1),
 '板前动能≥3%':lambda r:_gev(r.get('动能'),3),
 '温度冷<45':lambda r:r.get('温度') is not None and r['温度']==r['温度'] and r['温度']<45,
 '温度中性45-65':lambda r:r.get('温度') is not None and r['温度']==r['温度'] and 45<=r['温度']<65,
 '中大盘≥80亿':lambda r:_gev(r.get('市值亿'),80),
 '行业共振≥2':lambda r:_gev(r.get('行业家数'),2),
}
RULE_MINN=100; RULE_MINR=1.5
def _vec_masks(S):
    fs=S['首封'].fillna(''); wd=pd.to_numeric(S['温度'],errors='coerce')
    g=lambda c:pd.to_numeric(S[c],errors='coerce')
    return {
     '回封':(g('开板')>=1).values,'未开板':(g('开板')==0).values,
     '封单额≥1.5亿':(g('封额亿')>=1.5).values,'封单额≥4亿':(g('封额亿')>=4).values,
     '封单比≥2%':(g('封单比')>=2).values,'爆量≥2':(g('量比')>=2).values,
     '换手≥10%':(g('换手')>=10).values,
     '早封≤10:00':((fs!='')&(fs<='10:00')).values,'一字≤9:25':((fs!='')&(fs<='09:25')).values,
     '2板+':(g('连板')>=2).values,'3板+':(g('连板')>=3).values,
     '涨停基因≥1':(g('基因')>=1).values,'板前动能≥3%':(g('动能')>=3).values,
     '温度冷<45':(wd<45).values,'温度中性45-65':((wd>=45)&(wd<65)).values,
     '中大盘≥80亿':(g('市值亿')>=80).values,'行业共振≥2':(g('行业家数')>=2).values,
    }
def _rule_scan(S):
    """每晚重扫2-3条件合取规则: n≥RULE_MINN且执2均≥RULE_MINR%入榜,按执2均排序前12。多重检验风险靠大样本+每晚滚动+结算对账压制。"""
    from itertools import combinations
    masks=_vec_masks(S)
    rows=[]
    keys=list(masks)
    for r in (2,3):
        for combo in combinations(keys,r):
            m=masks[combo[0]].copy()
            for k in combo[1:]: m&=masks[k]
            n=int(m.sum())
            if n<RULE_MINN: continue
            a=_agg(S[m])
            if a['执2均涨'] is None or a['执2均涨']<RULE_MINR: continue
            rows.append(dict(规则=' × '.join(combo),条件=list(combo),n=n,
                执2均涨=a['执2均涨'],执2胜率=a['执2胜率'],抓龙率=a['抓龙率'],
                执1胜率=a['执1胜率'],执1均涨=a['执1均涨'],
                可执行=bool(a['执1胜率'] is not None and a['执1胜率']>=55)))
    rows.sort(key=lambda x:(-x['执2均涨'],len(x['条件'])))
    seen=set(); out=[]
    for e in rows:   # 去重:同(n,执2均,执2胜率)签名=同一票池的冗余组合,留条件最少的
        sig=(e['n'],e['执2均涨'],e['执2胜率'])
        if sig in seen: continue
        seen.add(sig); out.append(e)
        if len(out)>=10: break
    return out

PPK=None
def build(fetch=False,stage=None):
    """stage=None一体跑;沙箱45s限制下用: --prep(因子表→pkl) → --enrich(→S pkl) → --fit(出库)。"""
    ppk=os.path.join(L,'_P_stage.pkl'); spk=os.path.join(L,'_S_stage.pkl')
    if stage=='prep':
        P=_factor_table()
        if fetch: _fetch(sorted(P['代码'].unique()),P.groupby('代码')['日'].max().to_dict())
        P.to_pickle(ppk); print(f"PREP_OK 样本行{len(P)}"); return
    if stage=='enrich':
        P=pd.read_pickle(ppk); D=_enrich(P,forward=True); D.to_pickle(spk); print(f"ENRICH_OK {len(D)}"); return
    if stage=='fit':
        D=pd.read_pickle(spk); P=D
    else:
        P=_factor_table()
        if fetch: _fetch(sorted(P['代码'].unique()),P.groupby('代码')['日'].max().to_dict())
        D=_enrich(P,forward=True)
    S=D[D['E1'].notna()].copy()
    days_f=sorted(S['日'].unique()); recent=set(days_f[-RECENT:])
    base=_agg(S); base['score']=_bscore(base)
    facs={}
    for name,(fn,order) in FACTORS.items():
        S['_b']=S.apply(fn,axis=1)
        st={}
        for k,g in S.groupby('_b'):
            a=_agg(g); a['score']=_bscore(a); st[k]=a
        qual=[k for k in order if k in st and st[k]['n']>=MINB]
        ent=dict(桶序=order,桶=st)
        rho=disc=rho_r=None; w=0.0; status='淘汰·样本不足'
        if len(qual)>=2:
            wrs=[st[k]['执1胜率'] for k in qual]
            rho=_spear(range(len(qual)),wrs); disc=round(max(wrs)-min(wrs),1)
            Sr=S[S['日'].isin(recent)]
            str_={k:_agg(g) for k,g in Sr.groupby('_b') if len(g)>=8}
            qr=[k for k in qual if k in str_]
            if len(qr)>=2: rho_r=_spear([qual.index(k) for k in qr],[str_[k]['执1胜率'] for k in qr])
            if disc<MIN_DISC: status='淘汰·区分度不足'
            else:
                w=disc*(0.5+0.5*abs(rho or 0)); status='有效'
                if rho_r is not None and rho is not None and rho*rho_r<0 and abs(rho_r)>=0.3:
                    status='翻转降权'; w*=0.5
        ent.update(区分度=disc,单调rho=rho,近窗rho=rho_r,状态=status,原始权重=round(w,2))
        facs[name]=ent
    tw=sum(e['原始权重'] for e in facs.values())
    for e in facs.values(): e['权重']=round(e['原始权重']/tw,4) if tw>0 else 0
    active=[k for k,e in facs.items() if e['权重']>0]
    lib=dict(更新=datetime.date.today().strftime("%Y%m%d"),窗口=f"{P['日'].min()}~{P['日'].max()}",样本=int(len(S)),
        口径=("v4多因子评分卡。因子T日收盘可知;★执行口径:执1/执2买入点同为T+1开盘——执1=T+1开→T+1收(A股T+1制度当日卖不出,故执1=买入当天浮动盈亏/逐日盯市,检验开盘追买当天吃肉还是被套);执2=T+1开→T+2收(首个可完整执行的真实回合,最贴近交割的战绩口径)。荐票主口径=执行,一字开盘可能仍买不进=上界;"
             "信号口径T1/T2=T收→T+1/T+2收(仅参考)。不复权,零后视镜。质量分=Σ权重×桶分(0.5执1胜率+0.3执1均涨+0.2执2均涨映射);"
             f"有效性=区分度×单调性,区分度<{MIN_DISC}pp自动淘汰,近{RECENT}日方向翻转自动降权50%。"),
        基准=base,活跃因子=active,因子=facs,
        待积累说明="题材共振用题材归位_{d}.json真题材口径,当前仅少数交易日有档→样本不足自动淘汰,数据攒够自动激活,零编造。")
    # ★分板胜率(v4用户拍板): 连板一维(观察基准,已知单因子区分度低)+连板×封单比+连板×温度 交叉条件胜率
    tier=S['连板'].map(lambda v:'首板' if v<=1 else '2板' if v==2 else '3板' if v==3 else '4板+')
    fq=S['封单比'].map(lambda v:None if v is None or v!=v else ('封单≥2%' if v>=2 else '封单<2%'))
    wd=S['温度'].map(lambda v:None if v is None or v!=v else ('热≥65' if v>=65 else '中40-65' if v>=40 else '冷<40'))
    t_ord=['首板','2板','3板','4板+']
    一维={k:dict(_agg(g)) for k,g in S.groupby(tier)}
    连封={f"{a}×{b2}":_agg(g) for (a,b2),g in S.groupby([tier,fq]) if len(g)>=10}
    连温={f"{a}×{b2}":_agg(g) for (a,b2),g in S.groupby([tier,wd]) if len(g)>=10}
    lib['规则榜']=_rule_scan(S)
    lib['分板胜率']=dict(一维={k:一维[k] for k in t_ord if k in 一维},连板x封单=连封,连板x温度=连温,
        说明=("主口径=执行,买入点同为T+1开盘:执1=T+1开→T+1收(T+1制度当日卖不出=当日盯市,量'追买当天有无肉');执2=T+1开→T+2收(首个可完整执行回合=真实战绩口径)。信号T1/T2(收对收)仅参考禁作战绩。"
             "连板一维已知区分度低(v3实测1.7pp),交叉条件才可能有真结构;n<25桶只观察不进评分;"
             "温度覆盖=库窗口内有温度值的样本。"))
    json.dump(lib,open(os.path.join(L,"_涨停质量库.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    snap=dict(日=lib['更新'],样本=lib['样本'],基准执1=[base['执1胜率'],base['执1均涨']],
        因子={k:dict(权重=e['权重'],区分度=e['区分度'],rho=e['单调rho'],状态=e['状态']) for k,e in facs.items()})
    open(os.path.join(L,"_涨停质量库快照.jsonl"),"a",encoding="utf-8").write(json.dumps(snap,ensure_ascii=False)+"\n")
    md=[f"# 涨停质量库v5(一年历史+温度+规则榜) {lib['窗口']} 样本{lib['样本']} 零后视镜·执行口径",
        f"基准: 执1 {base['执1胜率']}%/{base['执1均涨']}% | 执2 {base['执2胜率']}%/{base['执2均涨']}% | 信号T1 {base['T1胜率']}%/{base['T1均涨']}%",
        f"活跃因子{len(active)}/{len(FACTORS)}: "+", ".join(f"{k}(w{facs[k]['权重']})" for k in sorted(active,key=lambda x:-facs[x]['权重']))]
    for name in sorted(facs,key=lambda x:-facs[x]['权重']):
        e=facs[name]
        md.append(f"\n## {name} | 状态:{e['状态']} 权重{e['权重']} 区分度{e['区分度']}pp rho{e['单调rho']} 近窗rho{e['近窗rho']}")
        for k in e['桶序']:
            if k in e['桶']:
                v=e['桶'][k]
                md.append(f"- {k}: n{v['n']} 执1 {v['执1胜率']}%/{v['执1均涨']}% 执2 {v['执2胜率']}%/{v['执2均涨']}% 分{v['score']}")
    md.append("\n## ★龙票规则榜(组合条件,每晚重扫;n≥%d且执2均≥%.1f%%入榜)"%(RULE_MINN,RULE_MINR))
    for e in lib['规则榜']:
        md.append(f"- {e['规则']}: n{e['n']} 执2 {e['执2胜率']}%/{e['执2均涨']}% 抓龙率{e['抓龙率']}% 执1 {e['执1胜率']}%/{e['执1均涨']}%"+(" [可执行]" if e['可执行'] else " [扛出型]"))
    md.append("\n## 分板胜率(执行口径为主;连板一维=观察基准)")
    for sec,dic in (('一维',lib['分板胜率']['一维']),('连板×封单',lib['分板胜率']['连板x封单']),('连板×温度',lib['分板胜率']['连板x温度'])):
        md.append(f"### {sec}")
        for k,v in dic.items():
            md.append(f"- {k}: n{v['n']} 执1 {v['执1胜率']}%/{v['执1均涨']}% 执2 {v['执2胜率']}%/{v['执2均涨']}% | 信号T1 {v['T1胜率']}%/{v['T1均涨']}%")
    open(os.path.join(L,"_涨停质量库.md"),"w",encoding="utf-8").write("\n".join(md))
    print(f"质量库v5建成: 样本{lib['样本']} 窗口{lib['窗口']} 活跃因子{len(active)}/{len(FACTORS)}")
    for k in sorted(active,key=lambda x:-facs[x]['权重']):
        print(f"  {k}: w{facs[k]['权重']} 区分度{facs[k]['区分度']}pp rho{facs[k]['单调rho']} {facs[k]['状态']}")
    return lib

def _lib():
    p=os.path.join(L,"_涨停质量库.json")
    return json.load(open(p,encoding="utf-8")) if os.path.isfile(p) else None

def 质量打分(row,lib=None):
    """row=因子值dict(打标当日产出行)。返回质量分+加权预测+主导因子(贡献拆解)。"""
    lib=lib or _lib()
    if not lib: return None
    base=lib['基准']; tot=0.;
    pw={'执1胜率':0.,'执1均涨':0.,'执2胜率':0.,'执2均涨':0.,'抓龙率':0.}
    contrib=[]
    for name,(fn,order) in FACTORS.items():
        e=lib['因子'].get(name)
        if not e or e['权重']<=0: continue
        b=fn(row); st=e['桶'].get(b) if b else None
        use=st if (st and st['n']>=MINB and st.get('score') is not None) else base
        tot+=e['权重']*use['score']
        for k in pw: pw[k]+=e['权重']*(use.get(k) or (base.get(k) or 0) if use.get(k) is None else use.get(k))
        contrib.append((name,b if use is not st or st is base else b,round(e['权重']*(use['score']-base['score']),1),b))
    contrib=[(n,bk,dv) for n,_,dv,bk in contrib]
    pos=sorted([x for x in contrib if x[2]>0],key=lambda x:-x[2])[:3]
    neg=sorted([x for x in contrib if x[2]<0],key=lambda x:x[2])[:2]
    lead="; ".join(f"{n}:{bk}(+{dv})" for n,bk,dv in pos)+((" | 拖累 "+"; ".join(f"{n}:{bk}({dv})" for n,bk,dv in neg)) if neg else "")
    return dict(质量分=round(tot),
        预测执1胜率=round(pw['执1胜率'],1),预测执1均涨=round(pw['执1均涨'],2),
        预测执2胜率=round(pw['执2胜率'],1),预测执2均涨=round(pw['执2均涨'],2),
        预测抓龙率=round(pw['抓龙率'],1),
        主导因子=lead or "全中性(各桶样本不足按基准)")

def 打标当日(d):
    """对d日全部涨停算14因子并打分(零后视镜:库不含d日前向;d日K线因子只用≤d数据)。"""
    P=_factor_table(); P=P[P['日']==d].copy()
    if not len(P): return []
    D=_enrich(P,forward=False); lib=_lib(); out=[]
    for _,r in D.iterrows():
        row=r.to_dict(); q=质量打分(row,lib)
        if not q: continue
        hits=[e['规则'] for e in (lib.get('规则榜') or []) if all(ATOMS[k](row) for k in e['条件'] if k in ATOMS)]
        rec=dict(代码=row['代码'],名称=row['名称'],首封=row['首封'],连板=row['连板'],开板次数=row['开板'],
            命中规则=hits,命中数=len(hits),
            封单比=row['封单比'],换手=row['换手'],市值亿=round(row['市值亿'],1) if row['市值亿']==row['市值亿'] else None,
            股价=row['股价'],基因10日=row['基因'],量比=row['量比'] if row['量比']==row['量比'] else None,
            位置60日=row['位置'] if row['位置']==row['位置'] else None,动能5日=row['动能'] if row['动能']==row['动能'] else None,
            行业家数=int(row['行业家数']),涨停总数=int(row['涨停总数']),
            封单额亿=row.get('封额亿'),温度=row.get('温度'),
            抓龙率=q.pop('预测抓龙率',None),**q)
        out.append(rec)
    return out

if __name__=="__main__":
    st='prep' if '--prep' in sys.argv else 'enrich' if '--enrich' in sys.argv else 'fit' if '--fit' in sys.argv else None
    build(fetch=("--fetch" in sys.argv),stage=st)
