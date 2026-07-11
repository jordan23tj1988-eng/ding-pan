# -*- coding: utf-8 -*-
"""涨停质量训练.py [--fetch] —— 涨停板质量因子→T+1/T+2溢价的每日滚动训练库(自我进化,零后视镜)。
样本=本地zt_pool历史中【已有T+1/T+2前向行情】的涨停(今日及最近2日无前向,不入库);
因子(T日收盘可知):封单比(封板资金/流通市值)/首封时间/连板/流通市值;溢价(T之后):T1=T收→T+1收,T2=T收→T+2收,不复权。
产出 _学习/_涨停质量库.json/.md + 快照。并暴露 质量查表(封单比,首封,连板,流通市值亿)->预测T1/T2胜率+均涨+综合质量分。"""
import os,sys,glob,json,datetime
import pandas as pd,numpy as np
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(os.path.dirname(os.path.abspath(__file__)),"_学习","_bars_cache"); os.makedirs(CDIR,exist_ok=True)

def fb_bucket(t):
    t=str(t)
    return '一字≤9:25' if t<='09:25' else '秒板≤9:31' if t<='09:31' else '早盘≤10:00' if t<='10:00' else '盘中>10:00'
def fd_bucket(v):
    if v is None or v!=v: return '未知'
    return '弱<0.5%' if v<0.5 else '偏弱0.5-1%' if v<1 else '中1-2%' if v<2 else '强2-4%' if v<4 else '超强≥4%'
def lb_bucket(x): return '首板' if x<=1 else '2板' if x==2 else '3板+'
def mv_bucket(x):
    if x!=x: return '未知'
    return '微盘<30亿' if x<30 else '小盘30-80亿' if x<80 else '中盘80-200亿' if x<200 else '大盘≥200亿'
def cross_key(fb,fd): return fb+' × '+('封单≥2%' if (fd==fd and fd>=2) else '封单<2%')

def _load_factors():
    days=sorted([os.path.basename(d) for d in glob.glob(os.path.join(BASE,'2026*')) if os.path.isdir(d) and os.path.isfile(os.path.join(d,'zt_pool.csv'))])
    rows=[]
    for d in days:
        df=pd.read_csv(os.path.join(BASE,d,'zt_pool.csv'),dtype={'代码':str}); df['代码']=df['代码'].str.zfill(6)
        for _,r in df.iterrows():
            mv=pd.to_numeric(r.get('流通市值'),errors='coerce'); fj=pd.to_numeric(r.get('封板资金'),errors='coerce')
            fdb=round(float(fj)/float(mv)*100,3) if (mv and mv>0 and fj==fj) else None
            fb=str(r['首次封板时间']).split('.')[0].zfill(6)
            rows.append(dict(日=d,代码=r['代码'],封单比=fdb,首封=fb[:2]+':'+fb[2:4],
                连板=int(pd.to_numeric(r.get('连板数',1),errors='coerce') or 1),
                流通市值=float(mv) if mv==mv else None))
    return pd.DataFrame(rows)
def _bars(c):
    f=os.path.join(CDIR,c+".csv")
    if os.path.isfile(f):
        try:
            b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-',''); return b.reset_index(drop=True)
        except: return None
    return None
def _fetch(codes,last_map=None):
    import akshare as ak
    from concurrent.futures import ThreadPoolExecutor
    def needs(c):
        f=os.path.join(CDIR,c+".csv")
        if not os.path.isfile(f): return True
        if not last_map or c not in last_map: return False
        try:
            b=pd.read_csv(f); dates=b['date'].astype(str).str.replace('-','')
            return int((dates>str(last_map[c])).sum())<2   # 该股最后涨停日T+2未完整→刷新
        except Exception: return True
    todo=[c for c in codes if needs(c)]
    print(f"fetch增量: {len(todo)}/{len(codes)}")
    def one(c):
        try:
            pre="sh" if c[0] in "69" else ("bj" if c[0] in "48" else "sz")
            b=ak.stock_zh_a_daily(symbol=pre+c,start_date="20260601",end_date=datetime.date.today().strftime("%Y%m%d"))
            b[["date","open","close"]].to_csv(os.path.join(CDIR,c+".csv"),index=False)
        except Exception as e: open(os.path.join(CDIR,c+".err"),"w").write(str(e)[:80])
    with ThreadPoolExecutor(max_workers=16) as ex: list(ex.map(one,todo))

def build(fetch=False):
    F=_load_factors()
    if fetch: _fetch(list(F['代码'].unique()),F.groupby('代码')['日'].max().to_dict())
    rec=[]
    for _,x in F.iterrows():
        b=_bars(x['代码'])
        if b is None: continue
        idx=b.index[b['date']==str(x['日'])]
        if len(idx)==0: continue
        i=idx[0]; Tc=b.loc[i,'close']
        if Tc<=0 or i+1>=len(b): continue  # 无T+1前向=不入库(含今日及最近2日)
        t1=b.loc[i+1,'close']/Tc-1
        t2=b.loc[i+2,'close']/Tc-1 if i+2<len(b) else np.nan
        o1=b.loc[i+1,'open']
        e1=(b.loc[i+1,'close']/o1-1) if o1>0 else np.nan            # 执行:T+1开盘买入→T+1收
        e2=(b.loc[i+2,'close']/o1-1) if (o1>0 and i+2<len(b)) else np.nan  # 执行:T+1开盘买入→T+2收
        rec.append(dict(封单比=x['封单比'],首封=x['首封'],连板=x['连板'],市值亿=(x['流通市值']/1e8 if x['流通市值'] else np.nan),T1=t1,T2=t2,E1=e1,E2=e2))
    D=pd.DataFrame(rec)
    def agg(g):
        def wr(col): 
            v=g[col].dropna()
            return (round((v>0).mean()*100,1),round(v.mean()*100,2)) if len(v) else (None,None)
        t1w,t1r=wr('T1'); t2w,t2r=wr('T2'); e1w,e1r=wr('E1'); e2w,e2r=wr('E2')
        return dict(n=int(len(g)),T1胜率=t1w,T1均涨=t1r,T2胜率=t2w,T2均涨=t2r,
                    执1胜率=e1w,执1均涨=e1r,执2胜率=e2w,执2均涨=e2r)
    def by(col,fn):
        o={}
        D['_k']=D[col].apply(fn)
        for k,g in D.groupby('_k'):
            if len(g)>=8: o[k]=agg(g)
        return o
    lib=dict(更新=datetime.date.today().strftime("%Y%m%d"),窗口=f"{F['日'].min()}~{F['日'].max()}",样本=int(len(D)),
        口径="因子T日收盘可知;信号口径T1/T2=T收→T+1/T+2收;★执行口径执1/执2=T+1开盘买入→T+1/T+2收(荐票主口径,封死票只能T+1开介入;一字开盘可能仍买不进=上界近似)。不复权,零后视镜。",
        基准=agg(D),
        封单比=by('封单比',fd_bucket),首封=by('首封',fb_bucket),连板=by('连板',lb_bucket),流通市值=by('市值亿',mv_bucket),
        交叉_首封x封单={})
    for (fb,fd),g in D.assign(_c=[cross_key(fb_bucket(r['首封']),r['封单比']) for _,r in D.iterrows()]).groupby('_c') if False else []:
        pass
    D['_c']=[cross_key(fb_bucket(r['首封']),r['封单比']) for _,r in D.iterrows()]
    for k,g in D.groupby('_c'):
        if len(g)>=10: lib['交叉_首封x封单'][k]=agg(g)
    json.dump(lib,open(os.path.join(L,"_涨停质量库.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    open(os.path.join(L,"_涨停质量库快照.jsonl"),"a",encoding="utf-8").write(json.dumps({"日":lib['更新'],"样本":lib['样本'],"基准":lib['基准']},ensure_ascii=False)+"\n")
    md=[f"# 涨停质量库 {lib['窗口']} 样本{lib['样本']} (零后视镜)"]
    md.append(f"基准 T1胜率{lib['基准']['T1胜率']}% 均涨{lib['基准']['T1均涨']}%")
    for dim in ['封单比','首封','连板','流通市值','交叉_首封x封单']:
        md.append(f"\n## {dim}")
        for k,v in lib[dim].items(): md.append(f"- {k}: n{v['n']} T1 {v['T1胜率']}%/{v['T1均涨']}% | T2 {v['T2胜率']}%/{v['T2均涨']}%")
    open(os.path.join(L,"_涨停质量库.md"),"w",encoding="utf-8").write("\n".join(md))
    print(f"质量库建成: 样本{lib['样本']} 窗口{lib['窗口']}")
    return lib

def _lib():
    p=os.path.join(L,"_涨停质量库.json")
    return json.load(open(p,encoding="utf-8")) if os.path.isfile(p) else None
def 质量查表(封单比,首封,连板,流通市值亿,lib=None):
    """给一只涨停的因子,返回预测T1/T2胜率+均涨+综合质量分(0-100)+匹配依据。"""
    lib=lib or _lib()
    if not lib: return None
    fb=fb_bucket(首封); ck=cross_key(fb,封单比)
    src=None; b=None
    if ck in lib.get('交叉_首封x封单',{}) and lib['交叉_首封x封单'][ck]['n']>=15:
        b=lib['交叉_首封x封单'][ck]; src=ck
    elif fd_bucket(封单比) in lib['封单比']:
        b=lib['封单比'][fd_bucket(封单比)]; src='封单比:'+fd_bucket(封单比)
    else:
        b=lib['基准']; src='基准'
    t1w=b['T1胜率']; t1r=b['T1均涨']; t2w=b.get('T2胜率'); t2r=b.get('T2均涨')
    e1w=b.get('执1胜率'); e1r=b.get('执1均涨'); e2w=b.get('执2胜率'); e2r=b.get('执2均涨')
    def clip(x,a,c): return max(a,min(c,x))
    if e1w is not None:   # ★质量分以执行口径为主(T+1开盘买入能不能吃到肉)
        score=round(0.5*clip((e1w-40)/35,0,1)*100 + 0.3*clip((e1r or 0)/3,0,1)*100 + 0.2*clip((e2r or 0)/4,0,1)*100)
    else:
        score=round(0.45*clip((t1w-45)/35,0,1)*100 + 0.35*clip(t1r/8,0,1)*100 + 0.20*clip((t2r or 0)/8,0,1)*100)
    return dict(预测T1胜率=t1w,预测T1均涨=t1r,预测T2胜率=t2w,预测T2均涨=t2r,
                预测执1胜率=e1w,预测执1均涨=e1r,预测执2胜率=e2w,预测执2均涨=e2r,
                质量分=score,匹配桶=src,n=b['n'])

if __name__=="__main__":
    build(fetch=("--fetch" in sys.argv))
