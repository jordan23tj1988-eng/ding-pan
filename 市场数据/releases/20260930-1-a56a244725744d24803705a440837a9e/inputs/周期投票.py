#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""周期投票 v1.0 (2026-07-12 用户拍板)
五路agent每晚对情绪周期投票(总agent不投),与cycle主判对账:
- 票: _学习/周期投票_{route}_{d}.json {route,stage,direction(升|平|降),confidence,evidence} (隔离:各路只写自己的,禁看他路)
- 主判: _学习/周期主判_{d}.json {stage,direction,evidence} (05认知写)
- tally {d}: 反对计数+加权反对份额(权重=收缩准确率K=10)+双层触发(当日≥3/5或加权≥0.60=复议;连续3日≥2路同向=重做复盘)
- settle {d}: 结算昨晚"明日方向"票,裁判=A档三指标Δ多数(温度Δ±2/1进2Δ±3pp/溢价Δ±0.5pp死区)→_周期投票准确率.json(主判同样记账作对照)
零编造:缺票=弃权照实;裁判数据缺=当日不结算。stage∈{冰点,启动,发酵主升,高潮,退潮}
"""
import os,sys,json,glob,time

def find_root():
    for p in glob.glob('/sessions/*/mnt/股票数据/市场数据'): return p
    return '.'
ROOT=None
ROUTES=['auction','lhb','theme','logic','limitup']
RN={'auction':'①竞价','lhb':'②席位','theme':'③题材','logic':'④产逻','limitup':'⑤质量'}
DIR_RANK={'降':-1,'平':0,'升':1}
K_SHRINK=10

def L(): return os.path.join(ROOT,'_学习')
def jload(p,dft):
    try:
        with open(p,encoding='utf-8') as f: return json.load(f)
    except Exception: return dft
def jsave(p,o):
    t=p+'.tmp'
    with open(t,'w',encoding='utf-8') as f: json.dump(o,f,ensure_ascii=False,indent=1)
    os.replace(t,p)

def acc_path(): return os.path.join(L(),'_周期投票准确率.json')
def ledger_path(): return os.path.join(L(),'_周期投票台账.jsonl')

def weight(route,acc):
    a=acc.get(route,{'n':0,'hits':0})
    return (a['hits']+0.5*K_SHRINK)/(a['n']+K_SHRINK)

def referee(d):
    """A档三指标Δ多数方向;数据缺→None(不结算)"""
    temp=jload(os.path.join(L(),'_市场温度表.json'),{})
    lead=jload(os.path.join(L(),'_情绪先行指标.json'),{})
    ks=sorted(k for k in temp if k<=d)
    if d not in temp or len(ks)<2: return None,None
    pd_=ks[-2]
    subs=[]
    try:
        dt=temp[d]['温度']-temp[pd_]['温度']
        subs.append('升' if dt>2 else ('降' if dt<-2 else '平'))
    except Exception: pass
    try:
        dj=lead[d]['晋级']['一进二率']-lead[pd_]['晋级']['一进二率']
        subs.append('升' if dj>0.03 else ('降' if dj<-0.03 else '平'))
    except Exception: pass
    try:
        dp=lead[d]['昨日涨停溢价']['执行均收']-lead[pd_]['昨日涨停溢价']['执行均收']
        subs.append('升' if dp>0.5 else ('降' if dp<-0.5 else '平'))
    except Exception: pass
    if len(subs)<2: return None,pd_
    for cand in ('升','降','平'):
        if subs.count(cand)>=2: return cand,pd_
    return '平',pd_

def settle(d):
    """结算 prev交易日 晚上投的'明日方向'票(明日=d)"""
    ref,pd_=referee(d)
    if ref is None:
        print('裁判数据不足,今日不结算'); return
    acc=jload(acc_path(),{})
    scored=[]
    for route in ROUTES+['cycle主判']:
        if route=='cycle主判':
            v=jload(os.path.join(L(),'周期主判_%s.json'%pd_),None)
        else:
            v=jload(os.path.join(L(),'周期投票_%s_%s.json'%(route,pd_)),None)
        if not v or v.get('direction') not in DIR_RANK: continue
        hit=1 if v['direction']==ref else 0
        a=acc.setdefault(route,{'n':0,'hits':0})
        a['n']+=1; a['hits']+=hit
        scored.append((route,v['direction'],hit))
    jsave(acc_path(),acc)
    print('settle %s 裁判=%s(投票日%s):'%(d,ref,pd_),scored)

def tally(d):
    main=jload(os.path.join(L(),'周期主判_%s.json'%d),None)
    if not main or not main.get('stage'):
        print('缺周期主判_%s.json,先让05认知写主判'%d); return
    acc=jload(acc_path(),{})
    votes={}; dissent=[]
    for route in ROUTES:
        v=jload(os.path.join(L(),'周期投票_%s_%s.json'%(route,d)),None)
        if not v or not v.get('stage'):
            votes[route]=None; continue
        votes[route]=v
        opp=(v['stage']!=main['stage']) or ({v.get('direction'),main.get('direction')}=={'升','降'})
        if opp: dissent.append(route)
    w_all=sum(weight(r,acc) for r in ROUTES if votes[r])
    w_dis=sum(weight(r,acc) for r in dissent)
    w_share=(w_dis/w_all) if w_all>0 else 0.0
    sides=[]
    for r in dissent:
        dv=DIR_RANK.get(votes[r].get('direction'),0)-DIR_RANK.get(main.get('direction'),0)
        sides.append(1 if dv>0 else (-1 if dv<0 else 0))
    ssum=sum(sides)
    day_side=1 if ssum>0 else (-1 if ssum<0 else 0)
    trig_day=(len(dissent)>=3) or (w_share>=0.60)
    # 连续3日≥2路同向
    hist=[]
    if os.path.exists(ledger_path()):
        with open(ledger_path(),encoding='utf-8') as f:
            hist=[json.loads(x) for x in f if x.strip()]
    hist=[h for h in hist if h['d']!=d]
    recent=hist[-2:]+[{'d':d,'n_dissent':len(dissent),'day_side':day_side}]
    trig_streak=(len(recent)==3 and all(h['n_dissent']>=2 for h in recent)
                 and len({h['day_side'] for h in recent})==1 and recent[0]['day_side']!=0)
    n_voted=sum(1 for r in ROUTES if votes[r])
    entry={'d':d,'主判':main,'votes':{r:(votes[r] or '弃权') for r in ROUTES},
           'n_voted':n_voted,'一致率':round((n_voted-len(dissent))/n_voted,2) if n_voted else None,
           'n_dissent':len(dissent),'dissent':dissent,'w_share':round(w_share,3),
           'day_side':day_side,'当日复议':trig_day,'连续重做':trig_streak,
           'ts':time.strftime('%Y-%m-%d %H:%M:%S')}
    with open(ledger_path(),'w' if not hist else 'w',encoding='utf-8') as f:
        for h in hist: f.write(json.dumps(h,ensure_ascii=False)+'\n')
        f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    res={'d':d,'当日复议':trig_day,'连续重做':trig_streak,'反对路':dissent,
         '加权反对份额':round(w_share,3),'反对侧':{1:'偏乐观',0:'中性',-1:'偏悲观'}[day_side] if dissent else '无',
         '要求':('当晚必须复议:改判或维持都要在cycle认知迭代写明理由' if trig_day else '')+
               ('; 连续3日≥2路同向反对:强制重做周期复盘并出专项报告 周期复盘重做_%s.md'%d if trig_streak else '')}
    jsave(os.path.join(L(),'周期投票结果_%s.json'%d),res)
    board(d,main,votes,dissent,acc,res)
    print(json.dumps(res,ensure_ascii=False))

def board(d,main,votes,dissent,acc,res):
    h=['<div style="margin:10px 0;padding:12px 14px;background:#14171e;border:1px solid #2a2f3a;border-radius:10px">']
    h.append('<div style="font-size:11px;letter-spacing:2px;color:#d9a441;font-family:monospace">五路周期投票 · 主判=%s·%s</div>'%(main['stage'],main.get('direction','')))
    h.append('<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">')
    for r in ROUTES:
        v=votes.get(r)
        w=weight(r,acc); a=acc.get(r,{'n':0,'hits':0})
        if not v:
            h.append('<div style="flex:1;min-width:100px;padding:8px;border:1px solid #2a2f3a;border-radius:8px;color:#5c6674;font-size:11.5px">%s<br>弃权</div>'%RN[r]); continue
        opp=r in dissent
        bc='#e05d5d' if opp else '#2a2f3a'
        h.append('<div style="flex:1;min-width:100px;padding:8px;border:1px solid %s;border-radius:8px;font-size:11.5px;color:#d8dee9">%s %s<br><b style="color:%s">%s·%s</b><br><span style="color:#5c6674">权%.0f%%·准确率%s</span></div>'%(
            bc,RN[r],('<span style="color:#e05d5d">反对</span>' if opp else '<span style="color:#4caf7d">同意</span>'),
            '#e05d5d' if opp else '#d8dee9',v['stage'],v.get('direction',''),
            w*100,('%d/%d'%(a['hits'],a['n']) if a['n'] else '新')))
    h.append('</div>')
    if res['当日复议'] or res['连续重做']:
        h.append('<div style="margin-top:8px;padding:6px 10px;border-left:3px solid #e05d5d;color:#e05d5d;font-size:12px">★触发:%s</div>'%res['要求'])
    else:
        h.append('<div style="margin-top:8px;color:#5c6674;font-size:11px">分歧未达阈值(当日≥3/5或加权≥0.60复议;连续3日≥2路同向重做) · 次日A档三指标Δ客观结算,准确率定话语权 · ★一致率长期>0.8=回声室警示(evidence须私有数据)</div>')
    h.append('</div>')
    with open(os.path.join(L(),'周期投票牌_%s.html'%d),'w',encoding='utf-8') as f:
        f.write('\n'.join(h))

if __name__=='__main__':
    a=sys.argv[1:]
    if '--root' in a:
        i=a.index('--root'); ROOT=a[i+1]; a=a[:i]+a[i+2:]
    else: ROOT=find_root()
    if len(a)<2: print(__doc__); sys.exit(0)
    {'settle':settle,'tally':tally}[a[0]](a[1])
