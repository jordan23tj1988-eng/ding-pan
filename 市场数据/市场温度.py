# -*- coding: utf-8 -*-
"""市场温度.py —— 每日涨停生态统计表 + 市场温度(0-100)。v1 2026-07-10 用户拍板
用法:
  python3 市场温度.py                    # 同步本地日目录→重算全表温度
  python3 市场温度.py --backfill 20250701 # akshare历史回填(断点续传,可反复跑)
  python3 市场温度.py --card 20260709    # 产温度卡html(嵌limitup页)
统计行(全部T日收盘可知,零后视镜): 涨停数/炸板数/跌停数/炸板率/两市成交额亿/
  封板总额亿/回封数(炸板>=1仍在册)/最高板/二板及以上家数/连板梯队。
★温度=各分量滚动250日分位数(不足250用全历史,>=30日才出值)等权合成0-100:
  正向=涨停数/成交额/封板总额/最高板/二板+  负向=跌停数/炸板率。null分量跳过重归一。
★零编造: 拿不到的分量标null不编(成交额历史用腾讯指数amount对本地summary校准,校不准=null)。
存: _学习/_市场温度表.json (日期→行, 幂等, 本地源优先覆盖akshare源)"""
import os,sys,json,glob,time,datetime
import pandas as pd,numpy as np
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")
CDIR=os.path.join(L,"_bars_cache")
TAB=os.path.join(L,"_市场温度表.json")
POS=['涨停数','成交额亿','封板总额亿','最高板','二板加']; NEG=['跌停数','炸板率']
WIN=250; MINH=30

def _load(): return json.load(open(TAB,encoding='utf-8')) if os.path.isfile(TAB) else {}
def _save(t): json.dump(t,open(TAB,'w',encoding='utf-8'),ensure_ascii=False,indent=1)

def _junk(name):
    """ST/退市整理/N/C新股->统计层剔除(与THS三池历史口径对齐;原始csv保留)。2026-07-11 P0-2。"""
    s=str(name or "")
    return ("ST" in s.upper()) or ("退" in s) or s.startswith("N") or s.startswith("C")

def _cnt(d,fn):
    p=os.path.join(BASE,d,fn)
    if not os.path.isfile(p): return None
    try:
        df=pd.read_csv(p)
        if '名称' in df.columns: df=df[~df['名称'].astype(str).map(_junk)]
        return int(len(df))
    except Exception: return None

def _row_local(d):
    """本地日目录取行(统计口径剔ST/退/N/C,自算为准;成交额取summary);缺标null(零编造)。"""
    zp=os.path.join(BASE,d,'zt_pool.csv')
    if not os.path.isfile(zp): return None
    sp=os.path.join(BASE,d,'summary.json')
    s=json.load(open(sp,encoding='utf-8')) if os.path.isfile(sp) else {}
    zt=pd.read_csv(zp)
    if '名称' in zt.columns: zt=zt[~zt['名称'].astype(str).map(_junk)]
    if len(zt)==0: return None
    fj=pd.to_numeric(zt['封板资金'],errors='coerce')
    kb=pd.to_numeric(zt['炸板次数'],errors='coerce').fillna(0)
    lb=pd.to_numeric(zt.get('连板数'),errors='coerce').fillna(1).astype(int)
    lad={str(int(k)):int(v) for k,v in lb.value_counts().items()}
    nzt=int(len(zt))
    nzb=_cnt(d,'zb_pool.csv')
    ndt=_cnt(d,'dt_pool.csv')
    zr=nzb/(nzt+nzb) if (nzb is not None and nzt+nzb>0) else None
    amt=s.get('两市成交额_亿')
    return dict(日=d,来源='local',
        涨停数=nzt,炸板数=nzb,跌停数=ndt,
        炸板率=round(float(zr),3) if zr is not None else None,
        成交额亿=round(float(amt),0) if amt is not None else None,
        封板总额亿=round(float(fj.sum())/1e8,1),回封数=int((kb>=1).sum()),
        最高板=int(lb.max()),
        二板加=int(sum(v for k,v in lad.items() if int(k)>=2)),梯队=lad)

_THSH={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
   "Referer":"https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html"}
def _ths(pool,d,full=False):
    """同花顺池分页取: limit_up_pool/open_limit_pool/lower_limit_pool。历史全有(实测2025-07起可用)。"""
    import urllib.request,re
    fld="199112,10,9001,330323,330324,330325,9002,330329,133971,133970" if full else "199112,10,9001"
    out=[]
    for page in (1,2,3):
        url=(f"https://data.10jqka.com.cn/dataapi/limit_up/{pool}?page={page}&limit=200"
             f"&field={fld}&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={d}")
        j=json.loads(urllib.request.urlopen(urllib.request.Request(url,headers=_THSH),timeout=15).read().decode())
        if j.get("status_code")!=0: raise RuntimeError(str(j.get("status_msg"))[:60])
        info=(j.get("data") or {}).get("info") or []
        out+=info
        if len(info)<200: break
    return out

def _hd(x):
    """high_days字符串→连板数: '首板'/None→1, 'N天M板'→M。high_days_value是编码值勿用。"""
    import re
    s=str(x.get("high_days") or "")
    m=re.search(r"(\d+)板",s)
    return int(m.group(1)) if m else 1

def _row_ak(d):
    """akshare东财池只留最近约13交易日→历史回填用同花顺三池(与本地EM口径实测吻合:
    20260709 涨停74/75 炸板17/17 跌停12/12 封板总额125.4亿=125.4亿 回封38/39)。"""
    try: zt=_ths("limit_up_pool",d,full=True)
    except Exception as e: print("  THS涨停池失败:",d,str(e)[:40]); return None
    if not zt: return None
    try: zb=len(_ths("open_limit_pool",d))
    except Exception: zb=None
    try: dt=len(_ths("lower_limit_pool",d))
    except Exception: dt=None
    lb=[_hd(x) for x in zt]
    fj=sum(x.get("order_amount") or 0 for x in zt)
    op=sum(1 for x in zt if (x.get("open_num") or 0)>=1)
    lad={}
    for v in lb: lad[str(v)]=lad.get(str(v),0)+1
    zr=round(zb/(zb+len(zt)),3) if (zb is not None and zb+len(zt)>0) else None
    return dict(日=d,来源='ths',涨停数=int(len(zt)),炸板数=zb,跌停数=dt,炸板率=zr,
        成交额亿=None,封板总额亿=round(fj/1e8,1),回封数=op,
        最高板=int(max(lb)),二板加=int(sum(1 for v in lb if v>=2)),梯队=lad)

def _amount_map(t):
    """两市成交额亿(历史):腾讯指数日线amount(单位未知)→用本地summary重叠日校准比例;
    校准样本<5或离散>5%则放弃返回{}(相应日标null,零编造)。"""
    try:
        import akshare as ak
        a=ak.stock_zh_index_daily_tx(symbol="sh000001"); b=ak.stock_zh_index_daily_tx(symbol="sz399001")
        for x in (a,b): x['date']=x['date'].astype(str).str.replace('-','')
        m=pd.merge(a[['date','amount']],b[['date','amount']],on='date',suffixes=('_sh','_sz'))
        m['tot']=pd.to_numeric(m['amount_sh'],errors='coerce')+pd.to_numeric(m['amount_sz'],errors='coerce')
        ref={d:r['成交额亿'] for d,r in t.items() if r.get('来源')=='local' and r.get('成交额亿')}
        cal=m[m['date'].isin(ref) & m['tot'].notna() & (m['tot']>0)]
        if len(cal)<5: return {}
        rt=pd.Series([ref[d]/tt for d,tt in zip(cal['date'],cal['tot'])])
        if rt.std()/rt.mean()>0.05:
            print(f"成交额校准失败 cv={rt.std()/rt.mean():.3f} → 历史成交额标null"); return {}
        k=float(rt.median()); print(f"成交额校准OK 比例{k:.6g} 样本{len(rt)} cv={rt.std()/rt.mean():.3f}")
        return {d:round(tt*k,0) for d,tt in zip(m['date'],m['tot']) if tt and tt>0}
    except Exception as e:
        print("成交额历史源不可用:",str(e)[:60]); return {}

def _recalc(t):
    ds=sorted(t); hist={k:[] for k in POS+NEG}
    for d in ds:
        r=t[d]; pcts=[]
        for k in POS+NEG:
            v=r.get(k)
            if v is None: hist[k].append(None); continue
            past=[x for x in hist[k][-(WIN-1):] if x is not None]+[v]
            hist[k].append(v)
            if len(past)>=MINH:
                p=sum(1 for x in past if x<=v)/len(past)
                pcts.append(1-p if k in NEG else p)
        r['温度']=round(float(np.mean(pcts))*100,1) if pcts else None
        r['温度档']=(None if r['温度'] is None else '冰点' if r['温度']<25 else '偏冷' if r['温度']<45
                    else '中性' if r['温度']<65 else '偏热' if r['温度']<85 else '过热')

def sync_local(t):
    for p in sorted(glob.glob(os.path.join(BASE,'20*'))):
        d=os.path.basename(p)
        if not (os.path.isdir(p) and len(d)==8 and d.isdigit()): continue
        r=_row_local(d)
        if r:
            # 本地池文件缺炸板/跌停(早期日目录)→先用已存行,再THS兜底自愈,仍缺标null
            prev=t.get(d) or {}
            for k in ('炸板数','跌停数','炸板率','成交额亿'):
                if r.get(k) is None and prev.get(k) is not None: r[k]=prev[k]
            if r.get('炸板数') is None:
                try:
                    zb=len(_ths('open_limit_pool',d)); r['炸板数']=zb
                    if zb+r['涨停数']>0: r['炸板率']=round(zb/(zb+r['涨停数']),3)
                except Exception: pass
            if r.get('跌停数') is None:
                try: r['跌停数']=len(_ths('lower_limit_pool',d))
                except Exception: pass
            t[d]=r
    return t

def backfill(t,start):
    import akshare as ak
    cal=ak.tool_trade_date_hist_sina()
    end=datetime.date.today().strftime('%Y%m%d')
    days=[x.strftime('%Y%m%d') for x in pd.to_datetime(cal['trade_date']).dt.date]
    todo=[d for d in days if start<=d<end and d not in t]
    print(f"回填待取 {len(todo)} 日 ({start}~{end})",flush=True)
    for i,d in enumerate(todo):
        r=_row_ak(d)
        if r: t[d]=r
        else: print("  跳过(接口空):",d,flush=True)
        if (i+1)%10==0: _save(t); print(f"  进度 {i+1}/{len(todo)} 最近{d}",flush=True)
        time.sleep(0.5)
    _save(t); return t

def _liangbi(code,d):
    f=os.path.join(CDIR,code+'.csv')
    if not os.path.isfile(f): return None
    try:
        b=pd.read_csv(f); b['date']=b['date'].astype(str).str.replace('-','')
        idx=b.index[b['date']==d]
        if not len(idx) or 'volume' not in b.columns: return None
        i=idx[0]
        if i<3: return None
        pv=b['volume'].iloc[max(0,i-5):i]
        return round(float(b.loc[i,'volume'])/float(pv.mean()),2) if pv.mean()>0 else None
    except Exception: return None

def tiers(d):
    """当日分板梯队画像: 家数/封单总额/封单比中位/回封/换手中位/量比中位(量价)。"""
    p=os.path.join(BASE,d,'zt_pool.csv')
    if not os.path.isfile(p): return None
    df=pd.read_csv(p,dtype={'代码':str}); df['代码']=df['代码'].str.zfill(6)
    lb=pd.to_numeric(df['连板数'],errors='coerce').fillna(1).astype(int)
    df['_t']=['首板' if v<=1 else '2板' if v==2 else '3板' if v==3 else '4板+' for v in lb]
    df['_fj']=pd.to_numeric(df['封板资金'],errors='coerce')
    df['_mv']=pd.to_numeric(df['流通市值'],errors='coerce')
    df['_fb']=df['_fj']/df['_mv']*100
    df['_kb']=pd.to_numeric(df['炸板次数'],errors='coerce').fillna(0)
    df['_hs']=pd.to_numeric(df['换手率'],errors='coerce')
    df['_lbi']=[_liangbi(c,d) for c in df['代码']]
    out={}
    for k in ['首板','2板','3板','4板+']:
        g=df[df['_t']==k]
        if not len(g): continue
        lbi=pd.Series([x for x in g['_lbi'] if x is not None],dtype=float)
        out[k]=dict(家数=int(len(g)),封单总额亿=round(float(g['_fj'].sum())/1e8,1),
            封单比中位=round(float(g['_fb'].median()),2) if g['_fb'].notna().any() else None,
            回封数=int((g['_kb']>=1).sum()),回封率=round(float((g['_kb']>=1).mean()),2),
            换手中位=round(float(g['_hs'].median()),1) if g['_hs'].notna().any() else None,
            量比中位=round(float(lbi.median()),2) if len(lbi) else None,量比覆盖=int(len(lbi)))
    return out

def _f(v,suf='',dash='—'):
    return dash if v is None else (f"{v}{suf}")

def card(d):
    """温度卡html片段 → _学习/市场温度卡_{d}.html (limitup页Top5卡之后嵌入)。
    排版铁律: table-layout:fixed+关键列nowrap。"""
    t=_load(); r=t.get(d)
    if not r: print("无温度行:",d); return None
    ds=[x for x in sorted(t) if x<=d][-20:][::-1]
    wd=r.get('温度'); wg=r.get('温度档') or '样本积累中'
    col='#c0392b' if (wd or 0)>=65 else ('#1e8449' if (wd or 100)<45 else '#b45309')
    kv=''.join(f'<div class="kv"><div class="l">{k}</div><div class="v">{v}</div></div>' for k,v in [
        ('市场温度',f'<span style="color:{col}">{_f(wd)}</span> <span style="font-size:12px">{wg}</span>'),
        ('涨停/炸板/跌停',f"{_f(r['涨停数'])}/{_f(r['炸板数'])}/{_f(r['跌停数'])}"),
        ('两市成交额',_f(int(r['成交额亿']) if r.get('成交额亿') is not None else None,'亿')),('封板总额',_f(r['封板总额亿'],'亿')),
        ('最高板·二板+',f"{_f(r['最高板'])}板·{_f(r['二板加'])}家"),('回封',_f(r['回封数'],'只'))])
    rows=''
    for x in ds:
        e=t[x]; hot=e.get('温度')
        c='#c0392b' if (hot or 0)>=65 else ('#1e8449' if (hot or 100)<45 else '#b45309')
        rows+=(f'<tr><td style="white-space:nowrap">{x[4:6]}-{x[6:8]}</td>'
          f'<td style="white-space:nowrap"><b style="color:{c}">{_f(hot)}</b> <span class="mut">{e.get("温度档") or "积累中"}</span></td>'
          f'<td style="white-space:nowrap">{_f(e["涨停数"])}</td><td style="white-space:nowrap">{_f(e["炸板数"])}</td><td style="white-space:nowrap">{_f(e["跌停数"])}</td>'
          f'<td style="white-space:nowrap">{_f(e["回封数"])}</td><td style="white-space:nowrap">{_f(e["最高板"])}</td><td style="white-space:nowrap">{_f(e["二板加"])}</td>'
          f'<td style="white-space:nowrap">{_f(int(e["成交额亿"]) if e.get("成交额亿") is not None else None)}</td>'
          f'<td style="white-space:nowrap">{_f(int(round(e["封板总额亿"])) if e.get("封板总额亿") is not None else None)}</td>'
          f'<td style="white-space:nowrap">{_f(round(e["炸板率"]*100,1) if e.get("炸板率") is not None else None,"%")}</td></tr>')
    tb=tiers(d); trow=''
    if tb:
        for k in ['首板','2板','3板','4板+']:
            if k not in tb: continue
            g=tb[k]
            trow+=(f'<tr><td style="white-space:nowrap"><b>{k}</b></td><td>{g["家数"]}</td>'
              f'<td>{_f(g["封单总额亿"],"亿")}</td><td>{_f(g["封单比中位"],"%")}</td>'
              f'<td>{g["回封数"]}({int(g["回封率"]*100)}%)</td><td>{_f(g["换手中位"],"%")}</td>'
              f'<td>{_f(g["量比中位"])}<span class="mut">/{g["量比覆盖"]}只</span></td></tr>')
    # 分板胜率(读质量库v4)
    win=''
    qp=os.path.join(L,'_涨停质量库.json')
    if os.path.isfile(qp):
        lib=json.load(open(qp,encoding='utf-8')); bs=lib.get('分板胜率')
        if bs:
            def sec(title,dic,order=None):
                ks=order or list(dic)
                s=f'<p style="margin:10px 0 2px;font-weight:700;font-size:13px">{title}</p><table><tr><th>桶</th><th>n</th><th>执1胜率/均涨</th><th>执2胜率/均涨</th><th class="mut">信号T1(参考)</th></tr>'
                for k in ks:
                    if k not in dic: continue
                    v=dic[k]; small=' <span class="mut">(小样本)</span>' if v['n']<25 else ''
                    s+=(f'<tr><td style="white-space:nowrap">{k}{small}</td><td>{v["n"]}</td>'
                      f'<td>{_f(v["执1胜率"],"%")} / {_f(v["执1均涨"],"%")}</td>'
                      f'<td>{_f(v["执2胜率"],"%")} / {_f(v["执2均涨"],"%")}</td>'
                      f'<td class="mut">{_f(v["T1胜率"],"%")} / {_f(v["T1均涨"],"%")}</td></tr>')
                return s+'</table>'
            win=''
            rb=lib.get('规则榜') or []
            if rb:
                win+='<details class="chain"><summary><b>龙票规则榜</b><span class="chip cold">v5荐票规则源</span><span class="chip">每晚重扫</span></summary><div class="inner">'
                win+='<p class="hint" style="padding-left:0;margin:6px 0 4px">荐票卡与台账里的「中N规」=命中本榜条数;本榜是v5的筛选器(组合条件合取,n≥100且执2均≥1.5%入榜;抓龙率=P(执2≥+8%))。</p><table><tr><th style="width:34%">规则</th><th>n</th><th>执2胜率/均涨</th><th>抓龙率</th><th>执1(开盘追买当日)</th><th>型</th></tr>'
                for e in rb:
                    tp='<span style="color:#0f766e">可执行</span>' if e.get('可执行') else '<span class="mut">扛出型</span>'
                    win+=(f'<tr><td style="word-break:break-word">{e["规则"]}</td><td style="white-space:nowrap">{e["n"]}</td>'
                      f'<td style="white-space:nowrap">{e["执2胜率"]}% / {e["执2均涨"]}%</td><td style="white-space:nowrap"><b>{e["抓龙率"]}%</b></td>'
                      f'<td style="white-space:nowrap" class="mut">{e["执1胜率"]}% / {e["执1均涨"]}%</td><td>{tp}</td></tr>')
                win+='</table><div class="hint">扛出型=执1弱执2强:开盘买进当天大概率被套、靠次日兑现;当前榜单全为巨额封单/一字系=信号强→溢价在跳空,追买无肉,用作身位与情绪判断而非追买清单。</div></div></details>'
            win+='<details class="chain"><summary><b>分板×质量×温度胜率库</b><span class="chip">观察基准·不进荐票</span><span class="chip">执行口径为主</span></summary><div class="inner">'
            win+='<p class="hint" style="padding-left:0;margin:6px 0 4px">与上面的规则榜不是一回事:此库=分桶统计的身位地图(看环境),规则榜=进荐票的筛选器。一年16k样本下分板一维已走平——"几板"本身不挑票。</p>'
            win+=sec('① 连板一维(观察基准,已知区分度低)',bs.get('一维',{}),['首板','2板','3板','4板+'])
            win+=sec('② 连板×封单比',bs.get('连板x封单',{}))
            win+=sec('③ 连板×市场温度',bs.get('连板x温度',{}))
            win+=f'<div class="hint">{bs.get("说明","")}</div></div></details>'
    disp=d[4:6]+'-'+d[6:8]
    # ★近20日可视化(2026-07-11用户拍板换视觉图表): 上=温度曲线+档位色带, 下=涨停(红)/跌停(绿)柱
    chron=ds[::-1]
    W,HT=880,168; X0,X1=46,868; YT0,YT1=14,150   # 温度区
    def _tx(i): return X0+(X1-X0)*(i+0.5)/len(chron)
    def _ty(v): return YT1-(YT1-YT0)*v/100
    bands=[(85,100,'#f6dfdf'),(65,85,'#f8ece1'),(45,65,'#f4efe2'),(25,45,'#e9f0e9'),(0,25,'#dfeae8')]
    svg=[f'<svg viewBox="0 0 {W} 305" style="width:100%;height:auto;display:block">']
    for lo,hi,cc in bands:
        svg.append(f'<rect x="{X0}" y="{_ty(hi):.1f}" width="{X1-X0}" height="{_ty(lo)-_ty(hi):.1f}" fill="{cc}"/>')
    for gv,lab in [(85,'85 过热'),(65,'65 偏热'),(45,'45 中性'),(25,'25 偏冷')]:
        svg.append(f'<line x1="{X0}" y1="{_ty(gv):.1f}" x2="{X1}" y2="{_ty(gv):.1f}" stroke="#d8d0c2" stroke-width="1" stroke-dasharray="3,3"/>'
                   f'<text x="{X0-4}" y="{_ty(gv)+3:.1f}" font-size="9" fill="#8a8577" text-anchor="end">{lab}</text>')
    pts=[(i,e.get('温度')) for i,x in enumerate(chron) for e in [t[x]] ]
    poly=' '.join(f'{_tx(i):.1f},{_ty(v):.1f}' for i,v in pts if v is not None)
    if poly: svg.append(f'<polyline points="{poly}" fill="none" stroke="#8a6d3b" stroke-width="2"/>')
    for i,v in pts:
        if v is None: continue
        cc='#c0392b' if v>=65 else ('#1e8449' if v<45 else '#b45309')
        last=(i==len(chron)-1)
        svg.append(f'<circle cx="{_tx(i):.1f}" cy="{_ty(v):.1f}" r="{4 if last else 3}" fill="{cc}" stroke="#fffdf9" stroke-width="1"/>')
        svg.append(f'<text x="{_tx(i):.1f}" y="{_ty(v)-7:.1f}" font-size="{10 if last else 8.5}" font-weight="{700 if last else 400}" fill="{cc}" text-anchor="middle">{v:.0f}</text>')
    # 柱区: 涨停/跌停
    YB0,YB1=196,282
    mx=max([t[x]['涨停数'] or 0 for x in chron]+[t[x].get('跌停数') or 0 for x in chron]+[1])
    bw=(X1-X0)/len(chron)*0.30
    svg.append(f'<line x1="{X0}" y1="{YB1}" x2="{X1}" y2="{YB1}" stroke="#d8d0c2" stroke-width="1"/>')
    for i,x in enumerate(chron):
        e=t[x]; cx=_tx(i)
        zt=e.get('涨停数'); dt=e.get('跌停数')
        if zt is not None:
            h=(YB1-YB0)*zt/mx
            svg.append(f'<rect x="{cx-bw-1:.1f}" y="{YB1-h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="#c0392b" opacity="0.85"/>')
            svg.append(f'<text x="{cx-bw/2-1:.1f}" y="{YB1-h-2:.1f}" font-size="8" fill="#c0392b" text-anchor="middle">{zt}</text>')
        if dt is not None:
            h2=(YB1-YB0)*dt/mx
            svg.append(f'<rect x="{cx+1:.1f}" y="{YB1-h2:.1f}" width="{bw:.1f}" height="{h2:.1f}" fill="#1e8449" opacity="0.8"/>')
            if dt>=mx*0.12: svg.append(f'<text x="{cx+bw/2+1:.1f}" y="{YB1-h2-2:.1f}" font-size="8" fill="#1e8449" text-anchor="middle">{dt}</text>')
        svg.append(f'<text x="{cx:.1f}" y="297" font-size="8.5" fill="#8a8577" text-anchor="middle">{x[4:6]}-{x[6:8]}</text>')
    svg.append(f'<text x="{X0}" y="{YB0-6}" font-size="9.5" fill="#5b6672">涨停(红) / 跌停(绿) 家数</text>')
    svg.append('</svg>')
    svgs=''.join(svg)
    html=(f'<div class="strip">{kv}</div>'
      f'<div class="card"><p style="font-weight:700;margin-bottom:2px">近20日市场温度 <span class="mut" style="font-weight:400">(温度=7分量滚动250日分位合成0-100;点色=档位)</span></p>'
      +svgs+
      f'<details class="chain" style="border:none;box-shadow:none;padding:0;margin-top:4px"><summary style="padding:8px 0"><b>数据表(近20日)</b> <span class="chip">明细</span></summary><div class="inner">'
      f'<table style="table-layout:fixed;width:100%"><colgroup><col style="width:48px"><col style="width:86px"><col><col><col><col><col><col><col style="width:70px"><col style="width:66px"><col style="width:58px"></colgroup>'
      f'<tr><th>日期</th><th>温度</th><th>涨停</th><th>炸板</th><th>跌停</th><th>回封</th><th>高度</th><th>2板+</th><th>成交额亿</th><th>封板额亿</th><th>炸板率</th></tr>{rows}</table></div></details></div>')
    if trow:
        html+=(f'<div class="card"><p style="font-weight:700;margin-bottom:4px">当日分板梯队画像 · {disp}</p>'
          f'<table><tr><th>梯队</th><th>家数</th><th>封单总额</th><th>封单比中位</th><th>回封(率)</th><th>换手中位</th><th>量比中位</th></tr>{trow}</table>'
          f'<div class="hint">回封=炸板≥1次仍收盘在册(分歧后资金再锁仓);量比=T量/前5日均量,覆盖只数受K线缓存限制。</div></div>')
    # ★档位成绩单(A档,冰点触发器回测口径:y1=池T于T+1开→收全场均收;数据=温度表×执行均收回填,自动随序列更新)
    bp=os.path.join(L,'_全场涨停执行均收_回填.json')
    if os.path.isfile(bp):
        P=json.load(open(bp,encoding='utf-8'))
        bands=[('冰点<25',0,25),('偏冷25-45',25,45),('中性45-65',45,65),('偏热65-85',65,85),('过热≥85',85,101)]
        cells=''
        for name,lo,hi in bands:
            vs=[P[x]['执行均收'] for x in t if x in P and t[x].get('温度') is not None
                and lo<=t[x]['温度']<hi and P[x].get('执行均收') is not None]
            cur=(wd is not None and lo<=wd<hi)
            if vs:
                m=sum(vs)/len(vs); wr=sum(1 for v in vs if v>0)/len(vs)
                vc='#c0392b' if m>0 else '#1e8449'
                sm=' ⚠' if len(vs)<25 else ''
                bd='border:1.5px solid #b8860b;background:rgba(184,134,11,.07)' if cur else 'border:1px solid #33383f'
                cells+=(f'<div style="flex:1;min-width:118px;{bd};border-radius:8px;padding:6px 8px;text-align:center">'
                    f'<div style="font-size:11px;color:#98a0ab">{name}{"·今日" if cur else ""}</div>'
                    f'<div style="font-weight:700;font-size:14px;color:{vc}">{m:+.2f}%</div>'
                    f'<div style="font-size:10px;color:#6b7683">胜率{wr:.0%} n={len(vs)}{sm}</div></div>')
        if cells:
            html+=('<div class="card"><p style="font-weight:700;margin-bottom:6px">档位成绩单 · 次日接力执行口径 '
                '<span class="mut" style="font-weight:400">(该温度档历史上T+1开盘接力全场涨停的均收/胜率;金框=今日档)</span></p>'
                f'<div style="display:flex;gap:8px;flex-wrap:wrap">{cells}</div>'
                '<div style="font-size:11px;color:#6b7683;margin-top:6px">读法:可交易信号在两端(冰点进攻/过热禁追),偏冷档=胜率最低的诱多带;单牛市周期样本,⚠=n<25小样本。</div></div>')
    # 两折叠(龙票规则榜+分板×质量×温度胜率库)拆出单独落盘,供四段涨停质量库注入(2026-08-15移动,不再并入二段温度卡)
    p2=os.path.join(L,f'质量库折叠_{d}.html')
    open(p2,'w',encoding='utf-8').write(win)
    p=os.path.join(L,f'市场温度卡_{d}.html')
    open(p,'w',encoding='utf-8').write(html)
    print("温度卡:",p); return p

if __name__=='__main__':
    args=sys.argv[1:]
    t=_load()
    if '--card' in args:
        card(args[args.index('--card')+1]); sys.exit()
    if '--backfill' in args:
        t=sync_local(t); t=backfill(t,args[args.index('--backfill')+1])
    else:
        t=sync_local(t)
    missing=[d for d,r in t.items() if r.get('成交额亿') is None]
    if missing:   # 只在有缺口时才拉腾讯指数(约40s);日常本地summary都有成交额=零开销
        am=_amount_map(t)
        for d,r in t.items():
            if r.get('成交额亿') is None and d in am: r['成交额亿']=am[d]
    _recalc(t); _save(t)
    ds=sorted(t)
    print(f"温度表: {len(ds)}日 {ds[0]}~{ds[-1]}")
    for d in ds[-8:]:
        r=t[d]; print(f"  {d} 温度{r.get('温度')}({r.get('温度档')}) 涨停{r['涨停数']} 炸板{r.get('炸板数')} 跌停{r.get('跌停数')} 额{r.get('成交额亿')} 封板{r.get('封板总额亿')}亿")
