#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自主拓展扫描 v1.0 (2026-07-12) —— 全系统"自主立项"三层机制的兜底层(零遗漏)
源起=用户给11号产逻的方案(横切面扫描),按职能推广到 auction/lhb/theme/limitup/cycle/master 六域。
★产业逻辑(logic)不在本脚本范围——11号的横切面扫描由另一程序实现,勿重复勿冲突(故本脚本文件名用"自主拓展*"错开"待深挖*")。
规范=_agent规格/自主拓展机制.md
子命令:
 scan {d}  : 横切面扫描→ _学习/自主拓展清单_{d}.json (agent对每项强制应答:立项或写不深挖理由→自主拓展应答_{d}.json)
 audit {d} : ★拒绝也要结算——回看2个交易日前应答中"不深挖"的项,标签计数翻倍=打脸→ _学习/错过机会.jsonl(共享,route字段)
 tick {d}  : 孵化区状态机维护(_学习/孵化区.json):截止日已过且未推进→自动"搁置";在研>3/路→告警
零编造:数据缺=该域跳过;打脸判据全部A档可复算。
扫描规则(各路只扫自己职能域,不破坏隔离):
 theme  : 题材归位近3日"大方向"计数≥3 且题材四维无该线序列 → 待挖(6有/生命周期判定缺口)
 auction: _竞价池反思.jsonl近5日同维度档位连续同向≥3日 → 待挖(该档位该不该进评分/闸门)
 lhb    : 席位动向近3日(剔类别汇总/区间榜/通道席) 净买≥5000万真席位不在分档库 → 待挖;同票双真席位共现≥2次 → 待挖
 limitup: 套票主导因子近5日累计≥3次 → 待挖(因子失效);选股增益连续≤0≥3日 → 待挖(荐票口径)
 cycle  : 先行指标/温度分量250日分位≥95或≤5 → 待挖(极值判读,应答写进cycle页判读card)
 master : ★裁决质量域——总账净值落后最佳子路≥1pp → 待挖(裁决alpha复盘);错过机会.jsonl近7日≥3条未消化 → 待挖(miss督办);某子路近3日选股增益均>0 → 待挖(该路是否被低配)
"""
import os,sys,json,glob,csv,time
def find_root():
    for p in glob.glob('/sessions/*/mnt/股票数据/市场数据'): return p
    return '.'
ROOT=None
def L(): return os.path.join(ROOT,'_学习')
def jload(p,dft):
    try:
        with open(p,encoding='utf-8') as f: return json.load(f)
    except Exception: return dft
def jsave(p,o):
    t=p+'.tmp'
    with open(t,'w',encoding='utf-8') as f: json.dump(o,f,ensure_ascii=False,indent=1)
    os.replace(t,p)
def calendar():
    return sorted(x for x in os.listdir(ROOT) if len(x)==8 and x.isdigit())
def last_n(d,n,cal=None):
    cal=cal or calendar()
    return [x for x in cal if x<=d][-n:]

GENERIC_SEATS={'机构专用','沪股通专用','深股通专用','机构','自然人','其他自然人','中小投资者','沪股通','深股通','量化基金','其他','北向资金'}
def real_seat(name):
    n=(name or '').strip()
    if not n or n in GENERIC_SEATS: return False
    return ('营业部' in n) or ('分公司' in n) or ('总部' in n)

def tag_counts(days):
    cnt={}
    for t in days:
        m=jload(os.path.join(L(),'题材归位_%s.json'%t),{}).get('映射',{})
        for c,v in m.items():
            tag=v.get('大方向','')
            if tag: cnt.setdefault(tag,[]).append((t,c))
    return cnt

def scan(d):
    cal=calendar(); days=last_n(d,3,cal)
    items=[]
    def add(route,sig,count,ev):
        items.append({'id':'%s_%s_%d'%(route,d,len(items)),'route':route,'signal':sig,'count':count,'evidence':ev})
    # theme/logic 横切面
    cnt=tag_counts(days)
    fourd=jload(os.path.join(L(),'_题材四维.json'),{})
    fourd_lines=set()
    for t in days:
        fourd_lines |= set((fourd.get(t) or {}).keys())
    for tag,occ in sorted(cnt.items(),key=lambda x:-len(x[1])):
        if len(occ)<3 or ('散票' in tag) or ('待核' in tag): continue
        codes=sorted({c for _,c in occ})
        base=tag.split('/')[0]
        if not any(base in ch or ch in tag for ch in fourd_lines):
            add('theme','标签[%s]近3日%d只涨停但题材四维无该线序列——需线名归一或立6有判定'%(tag,len(occ)),len(occ),'代表:%s'%','.join(codes[:4]))
    # auction: 反思档位连续同向
    lines=[]
    p=os.path.join(L(),'_竞价池反思.jsonl')
    if os.path.exists(p):
        with open(p,encoding='utf-8') as f:
            lines=[json.loads(x) for x in f if x.strip()][-5:]
    for dim in ('按信号','按连板','按高开档'):
        seq={}
        for r in lines:
            for k,v in (r.get(dim) or {}).items():
                if isinstance(v,(int,float)): seq.setdefault(k,[]).append(v)
        for k,vs in seq.items():
            if len(vs)>=3 and (all(x>0 for x in vs[-3:]) or all(x<0 for x in vs[-3:])):
                add('auction','%s[%s]连续%d日同向(均收%s)——该档位是否该进评分维度/闸门规则'%(dim,k,len(vs[-3:]),['%.1f'%x for x in vs[-3:]]),len(vs),'源=_竞价池反思.jsonl')
    # lhb: 新活跃席位+共现
    rank=jload(os.path.join(L(),'_席位分档.json'),{})
    known=set((rank.get('席位') or {}).keys()) if isinstance(rank.get('席位'),dict) else set(rank.get('席位') or [])
    seat_hits={}; pair_hits={}
    for t in days:
        fp=os.path.join(L(),'_席位动向','%s.csv'%t)
        if not os.path.exists(fp): continue
        by_ticket={}
        with open(fp,encoding='utf-8') as f:
            for row in csv.DictReader(f):
                typ=row.get('类型','') or ''
                if ('连续' in typ) or ('累计' in typ) or ('区间' in typ): continue  # 区间榜行,数据污染教训
                try: net=float(row.get('净额') or 0)
                except Exception: net=0
                seat=row.get('席位',''); code=str(row.get('代码','')).zfill(6)
                if not real_seat(seat): continue  # 类别汇总行/通道类席位剔除
                if net>=5e7 and seat not in known:
                    seat_hits.setdefault(seat,[]).append((t,code,round(net/1e8,2)))
                if net>=3e7: by_ticket.setdefault((t,code),[]).append(seat)
        for (t2,code),seats in by_ticket.items():
            ss=sorted(set(seats))
            for i in range(len(ss)):
                for j in range(i+1,len(ss)):
                    pair_hits.setdefault((ss[i],ss[j]),[]).append((t2,code))
    for seat,hs in sorted(seat_hits.items(),key=lambda x:-len(x[1]))[:4]:
        if len(hs)>=2: add('lhb','新活跃席位[%s]近3日净买≥5000万×%d次,不在分档库'%(seat,len(hs)),len(hs),str(hs[:3]))
    pairs=[( (a,b),hs) for (a,b),hs in pair_hits.items() if len(hs)>=2]
    for (a,b),hs in sorted(pairs,key=lambda x:-len(x[1]))[:4]:
        add('lhb','席位共现组合[%s × %s]同票净买≥3000万×%d次——协同资金?'%(a[:14],b[:14],len(hs)),len(hs),str(hs[:3]))
    # limitup: 因子失效+增益连负
    ql=[]
    p=os.path.join(L(),'_涨停质量反思.jsonl')
    if os.path.exists(p):
        with open(p,encoding='utf-8') as f:
            ql=[json.loads(x) for x in f if x.strip()][-5:]
    fac={}
    for r in ql:
        for k,v in (r.get('套票因子') or {}).items(): fac[k]=fac.get(k,0)+1
    for k,v in fac.items():
        if v>=3: add('limitup','因子[%s]近5日%d次成为套票主导——失效复盘/降权候补'%(k,v),v,'源=_涨停质量反思.jsonl')
    gains=[r.get('选股增益pp') for r in ql if isinstance(r.get('选股增益pp'),(int,float))]
    if len(gains)>=3 and all(g<=0 for g in gains[-3:]):
        add('limitup','选股增益连续%d日≤0(%s)——荐票口径整体复盘'%(len(gains[-3:]),['%.1f'%g for g in gains[-3:]]),3,'源=_涨停质量反思.jsonl')
    # cycle: 分位极值
    lead=jload(os.path.join(L(),'_情绪先行指标.json'),{})
    temp=jload(os.path.join(L(),'_市场温度表.json'),{})
    def pctile(series,val):
        s=[x for x in series if isinstance(x,(int,float))]
        if len(s)<60 or val is None: return None
        return 100.0*sum(1 for x in s if x<=val)/len(s)
    checks=[]
    ks=sorted(k for k in lead if k<=d)
    if d in lead:
        cur=lead[d]
        checks.append(('1进2率',[ (lead[k].get('晋级') or {}).get('一进二率') for k in ks],(cur.get('晋级') or {}).get('一进二率')))
        checks.append(('昨停溢价',[ (lead[k].get('昨日涨停溢价') or {}).get('执行均收') for k in ks],(cur.get('昨日涨停溢价') or {}).get('执行均收')))
    tk=sorted(k for k in temp if k<=d)
    if d in temp:
        checks.append(('炸板率',[temp[k].get('炸板率') for k in tk],temp[d].get('炸板率')))
    for name,series,val in checks:
        pc=pctile(series,val)
        if pc is not None and (pc>=95 or pc<=5):
            add('cycle','[%s]=%s 处250日分位%.0f%%极值——页面必须有专门判读'%(name,val,pc),1,'A档自算分位')
    capped=[]
    for route in ('auction','lhb','theme','limitup','cycle','master'):
        ri=[i for i in items if i['route']==route]
        ri.sort(key=lambda x:-x['count'])
        capped+=ri[:6]
    items=capped
    # master: 裁决质量域
    simd=os.path.join(L(),'_模拟盘')
    navs={}
    for rt in ('auction','lhb','theme','logic','limitup','master'):
        nv=jload(os.path.join(simd,rt,'净值.json'),{})
        if nv:
            ks2=sorted(nv)[-5:]
            navs[rt]=nv[ks2[-1]]['nav']
    if 'master' in navs and len(navs)>=3:
        best=max((v,k) for k,v in navs.items() if k!='master')
        gap=(best[0]-navs['master'])*100
        if gap>=1.0:
            add('master','总账净值落后最佳子路[%s] %.1fpp——裁决alpha为负,复盘该信没信的路'%(best[1],gap),int(gap),'源=_模拟盘净值')
    mp=os.path.join(L(),'错过机会.jsonl')
    if os.path.exists(mp):
        cal7=set(last_n(d,7,cal))
        with open(mp,encoding='utf-8') as f:
            recent=[json.loads(x) for x in f if x.strip()]
        undig=[m for m in recent if m.get('d') in cal7 and not m.get('已消化')]
        if len(undig)>=3:
            add('master','错过机会近7日积压%d条未消化——master主审:逐条归因并转成新触发规则'%len(undig),len(undig),'源=错过机会.jsonl')
    if ql:
        g2=[r.get('选股增益pp') for r in ql[-3:] if isinstance(r.get('选股增益pp'),(int,float))]
        if len(g2)>=3 and all(x>0 for x in g2):
            add('master','质量路选股增益连续3日为正(%s)——总账裁决是否低配了该路票'%['%.1f'%x for x in g2],3,'源=_涨停质量反思.jsonl')
    out={'d':d,'items':items,'说明':'各路agent对本清单强制应答:立项(进孵化区)或写不深挖理由(★理由会被audit结算打脸)'}
    jsave(os.path.join(L(),'自主拓展清单_%s.json'%d),out)
    print('scan',d,'共%d项:'%len(items),json.dumps([{'route':i['route'],'signal':i['signal'][:40]} for i in items],ensure_ascii=False))

def audit(d):
    cal=calendar(); ds=[x for x in cal if x<d]
    if len(ds)<3: print('历史不足'); return
    d3=ds[-2]  # 回看2个交易日前的应答(拒绝要接受结算)
    resp=jload(os.path.join(L(),'自主拓展应答_%s.json'%d3),{})
    inv=jload(os.path.join(L(),'自主拓展清单_%s.json'%d3),{}).get('items',[])
    if not resp: print('无%s应答可审'%d3); return
    cnt_then=tag_counts(last_n(d3,3,cal)); cnt_now=tag_counts(last_n(d,3,cal))
    misses=[]
    for it in inv:
        r=resp.get(it['id'])
        if not r or r.get('决定')!='不深挖': continue
        hit=None
        if it['route'] in ('theme','logic'):
            import re
            m=re.search('标签\\[(.+?)\\]',it['signal'])
            if m:
                tag=m.group(1)
                then=len(cnt_then.get(tag,[])); now=len(cnt_now.get(tag,[]))
                if then and now>=2*then:
                    hit='标签[%s]涨停计数 %d→%d(≥2倍),当时拒绝理由:%s'%(tag,then,now,r.get('理由',''))
        else:
            hit=None  # 非标签类v1不自动结算,标人工复核
        if hit:
            misses.append({'d':d,'route':it['route'],'item':it['signal'],'拒绝日':d3,'拒绝理由':r.get('理由',''),'打脸证据':hit,'来源':'audit自动'})
    mp=os.path.join(L(),'错过机会.jsonl')
    seen=set()
    if os.path.exists(mp):
        with open(mp,encoding='utf-8') as f:
            for x in f:
                try:
                    o=json.loads(x); seen.add((o.get('拒绝日'),o.get('item')))
                except Exception: pass
    misses=[m for m in misses if (m['拒绝日'],m['item']) not in seen]
    with open(mp,'a',encoding='utf-8') as f:
        for m in misses: f.write(json.dumps(m,ensure_ascii=False)+'\n')
    print('audit',d,'回看%s:打脸%d条'%(d3,len(misses)), json.dumps(misses,ensure_ascii=False) if misses else '')

def tick(d):
    p=os.path.join(L(),'孵化区.json')
    hub=jload(p,{})
    warn=[]
    for route,tops in hub.items():
        active=[t for t in tops if t.get('状态') in ('探索','小样本验证','提请拍板')]
        if len(active)>3: warn.append('%s在研%d>3,注意力稀释'%(route,len(active)))
        for t in tops:
            if t.get('状态') in ('探索','小样本验证') and t.get('截止') and t['截止']<d:
                last=(t.get('log') or [{}])[-1].get('d','')
                if last < t['截止']:
                    t['状态']='搁置'; t.setdefault('log',[]).append({'d':d,'进展':'★超截止无推进,自动搁置(脚本)'})
    jsave(p,hub)
    print('tick',d,'告警:',warn or '无')

if __name__=='__main__':
    a=sys.argv[1:]
    if '--root' in a:
        i=a.index('--root'); ROOT=a[i+1]; a=a[:i]+a[i+2:]
    else: ROOT=find_root()
    if len(a)<2: print(__doc__); sys.exit(0)
    {'scan':scan,'audit':audit,'tick':tick}[a[0]](a[1])
