#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模拟盘引擎 v2.0 (2026-07-12)
六本账(五路+总)组合级模拟实盘。规则=R/_模拟盘设计.md v2.0(2026-07-12用户拍板持有期自主):
每晚计划(发出版不可覆盖)={buys:[{code,name,weight_pct,reason,可选buy_gate}],sells:[{code,leg:"open|close",可选sell_switch,reason}],notes}
买=次日开盘(一字拒单/闸门/整手/禁ST退NC);卖=指令驱动:agent每晚对每只在持票决定"明日卖(开/收腿)或继续持有",
持有天数自主无上限,最早T+2可卖(T+1制度:买入次日起),无卖单=默认持有;跌停/停牌顺延次日开盘;≤5只(含在持)。
成本双边0.15%(买0.05%卖0.10%);逐日盯市;影子基准=全场涨停T+1开→T+2开等权(固定节奏环境基线,与账户持有期无关)。
子命令: settle {d} | dashboard {d} | inject {d} | weekly {d} | morning {d}
★v1.1 早盘规则(晚间预declare,零后视镜):
 buy_gate={"max_gap_pct":5}/{"min_gap_pct":-3} → T+1开盘gap越界=闸门弃单(用bars结算:开盘价=9:25竞价价)
 sell_switch={"if_gap_ge_pct":3,"then":"T2_close"} → T+2高开达阈改持到收盘卖(仅首次卖出日生效,顺延日不适用)
 morning {d} = 9:25-9:31实时预告(sina竞价价机判买卖动作,写_模拟盘/早盘执行_{d}.json供早盘页展示;结算以bars为准)
★v2.0持有期自主(取代v1.3): 止损腿+固定T+2强制卖均撤销(用户拍板:有些策略T+1浮亏T+2才兑现);现行=无卖单默认继续持有,卖出由指令单驱动,最早T+2可卖无上限,跌停/停牌顺延;买入记流动性(股数/当日成交量,≥1%警示);
 weekly增: 路内池基准(该路当周荐票发出版全体票同规则均收,对照全场涨停基准)+卖腿反事实对照(仅归因非战绩)+票一致率
零编造:缺数据标注跳过;所有战绩数字只出自本引擎。
"""
import os, sys, json, csv, math, time, glob, hashlib

def find_root():
    for p in glob.glob('/sessions/*/mnt/股票数据/市场数据'):
        return p
    return '.'

ROOT = None
CAP = 1_000_000.0
BUY_C, SELL_C = 0.0005, 0.0010
ROUTES = ['auction','lhb','theme','logic','limitup','master']
RNAME = {'auction':'第一路·竞价','lhb':'第二路·席位','theme':'第三路·题材',
         'logic':'第四路·产业逻辑','limitup':'第五路·涨停质量','master':'总·情绪总裁决'}
PAGE = {'auction':'auction.html','lhb':'lhb.html','theme':'theme.html',
        'logic':'logic.html','limitup':'limitup.html','master':'index.html'}

def r2(x): return math.floor(x*100+0.5)/100.0
def learn(): return os.path.join(ROOT,'_学习')
def simdir(route=None):
    d = os.path.join(learn(),'_模拟盘')
    if route: d = os.path.join(d,route)
    os.makedirs(d,exist_ok=True); return d

def jload(p,default):
    try:
        with open(p,encoding='utf-8') as f: return json.load(f)
    except Exception: return default
def jsave(p,obj):
    tmp = p+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=1)
    os.replace(tmp,p)
def ledger(route,ev):
    ev['ts'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(os.path.join(simdir(route),'账本.jsonl'),'a',encoding='utf-8') as f:
        f.write(json.dumps(ev,ensure_ascii=False)+'\n')

def calendar():
    ds = [x for x in os.listdir(ROOT) if len(x)==8 and x.isdigit()]
    return sorted(ds)
def prev_td(d, cal=None):
    cal = cal or calendar()
    xs = [x for x in cal if x < d]
    return xs[-1] if xs else None
def next_td(d, cal=None):
    cal = cal or calendar()
    xs = [x for x in cal if x > d]
    return xs[0] if xs else None

# ── bars ──────────────────────────────────────────────
_bcache = {}
def load_bars(code):
    if code in _bcache: return _bcache[code]
    out = {}
    for base in [os.path.join(learn(),'_bars_cache'), os.path.join(simdir(),'_bars_extra')]:
        p = os.path.join(base, code+'.csv')
        if not os.path.exists(p): continue
        try:
            with open(p,encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    dt = row.get('date','').replace('-','')
                    if len(dt)==8 and row.get('open'):
                        try:
                            vol = None
                            try: vol = float(row.get('volume') or 0) or None
                            except Exception: pass
                            out[dt] = (float(row['open']),float(row['high']),float(row['low']),float(row['close']),vol)
                        except Exception: pass
        except Exception: pass
    _bcache[code] = out
    return out

def sina_sym(code):
    if code.startswith(('60','68','90')): return 'sh'+code
    if code.startswith(('00','30','20')): return 'sz'+code
    return 'bj'+code

def fetch_bars(code, deadline):
    """补拉缺行情→_bars_extra(独立目录,不碰共享cache schema)。失败即放弃,不编。"""
    if time.time() > deadline: return False
    try:
        import akshare as ak
        df = ak.stock_zh_a_daily(symbol=sina_sym(code), adjust='')
        if df is None or df.empty: return False
        p = os.path.join(simdir(),'_bars_extra'); os.makedirs(p,exist_ok=True)
        rows = df.tail(30)
        with open(os.path.join(p,code+'.csv'),'w',encoding='utf-8') as f:
            f.write('date,open,high,low,close,volume\n')
            for _,r in rows.iterrows():
                f.write('%s,%s,%s,%s,%s,%s\n'%(str(r['date'])[:10],r['open'],r['high'],r['low'],r['close'],r.get('volume','')))
        _bcache.pop(code,None)
        return True
    except Exception:
        return False

def ratio(code):
    if code.startswith(('30','68')): return 0.20
    if code.startswith(('8','4','92')): return 0.30
    return 0.10

def bad_name(name):
    n = (name or '')
    return ('ST' in n.upper()) or ('退' in n) or n.startswith('N') or n.startswith('C')

# ── state ─────────────────────────────────────────────
def st_path(route): return os.path.join(simdir(route),'state.json')
def nav_path(route): return os.path.join(simdir(route),'净值.json')
def load_state(route):
    return jload(st_path(route), {'cash':CAP,'positions':[],'done':[],'plans_done':[],'closed':[]})
def last_nav(route, before=None):
    nav = jload(nav_path(route), {})
    ks = sorted(nav.keys())
    if before: ks = [k for k in ks if k < before]
    return (nav[ks[-1]]['nav'] if ks else 1.0), nav

def get_bar(code, d, deadline):
    b = load_bars(code)
    if d not in b and fetch_bars(code, deadline): b = load_bars(code)
    return b.get(d), b

# ── settle ────────────────────────────────────────────
def settle(d):
    cal = calendar()
    if d not in cal:
        print('非交易日或数据目录缺失:',d); return
    deadline = time.time()+30
    pd_ = prev_td(d,cal)
    for route in ROUTES:
        st = load_state(route)
        if d in st['done']:
            print(route,'已结算过',d); continue
        cash = st['cash']
        # 1) 卖出(指令驱动:昨晚计划sells+历史顺延单)
        plan_prev = jload(os.path.join(learn(),'交易计划_%s_%s.json'%(route,pd_)),{}) if pd_ else {}
        sells_map = {}
        for o in (plan_prev.get('sells') or []):
            sells_map[str(o.get('code','')).zfill(6)] = o
        keep = []
        for pos in st['positions']:
            code = pos['code']; order = sells_map.get(code)
            if order is not None and pos['buy_date'] >= d:
                ledger(route,{'ev':'warn','d':d,'code':code,'why':'卖单指向今日才买入的票,T+1制度不可卖,忽略'}); order = None
            if not pos.get('defer_sell') and order is None:
                keep.append(pos); continue
            leg = 'open' if pos.get('defer_sell') else ('close' if order.get('leg')=='close' else 'open')
            sw = None if pos.get('defer_sell') else (order or {}).get('sell_switch')
            bar,b = get_bar(code, d, deadline)
            pvc = b.get(prev_td(d,cal),(None,)*5)[3] if prev_td(d,cal) else None
            if bar is None:
                pos['defer_sell'] = True; pos['defers'] = pos.get('defers',0)+1
                ledger(route,{'ev':'defer','d':d,'code':code,'why':'无行情/停牌'})
                keep.append(pos); continue
            switched = False
            if sw and pvc and leg=='open':
                gap_s = (bar[0]/pvc-1)*100
                if gap_s >= float(sw.get('if_gap_ge_pct',1e9)):
                    leg = 'close'; switched = True
            px = bar[0] if leg=='open' else bar[3]
            dn = r2((pvc or bar[3])*(1-ratio(code)))
            if pvc is not None and px <= dn + 1e-9:
                pos['defer_sell'] = True; pos['defers'] = pos.get('defers',0)+1
                ledger(route,{'ev':'defer','d':d,'code':code,'why':'跌停无法卖出','px':px})
                keep.append(pos); continue
            proceeds = pos['shares']*px*(1-SELL_C)
            cash += proceeds
            hold_days = len([x for x in cal if pos['buy_date'] < x <= d])
            tr = {'code':code,'name':pos['name'],'plan_date':pos['plan_date'],
                  'buy_date':pos['buy_date'],'buy_px':pos['buy_px'],'sell_date':d,'sell_px':px,
                  'leg':('T_close' if leg=='close' else 'T_open'),'hold_days':hold_days,
                  'defers':pos.get('defers',0),'weight':pos['weight'],'switched':switched,
                  'pnl':round(proceeds-pos['cost'],2),
                  'ret_pct':round((proceeds/pos['cost']-1)*100,2),'reason':pos.get('reason','')}
            st['closed'].append(tr)
            ledger(route,{'ev':'sell','d':d,**tr})
        st['positions'] = keep
        # 2) 买入(昨晚计划)
        if pd_ and pd_ not in st['plans_done']:
            pf = os.path.join(learn(),'交易计划_%s_%s.json'%(route,pd_))
            if os.path.exists(pf):
                plan = jload(pf,{})
                reg = jload(os.path.join(simdir(),'发出登记.json'),{})
                key = '%s_%s'%(route,pd_)
                sha = hashlib.sha256(open(pf,'rb').read()).hexdigest()[:16]
                if key in reg and reg[key]!=sha:
                    ledger(route,{'ev':'warn','d':d,'why':'★发出版被改动!以首见sha为准记档','sha_now':sha})
                else:
                    reg[key]=sha; jsave(os.path.join(simdir(),'发出登记.json'),reg)
                poss = (plan.get('buys') or plan.get('positions') or [])[:5]
                wsum = sum(float(p.get('weight_pct',0)) for p in poss)
                scale = 100.0/wsum if wsum>100 else 1.0
                if scale<1.0: ledger(route,{'ev':'warn','d':d,'why':'仓位合计%s>100,按比例压缩'%wsum})
                eq0,_ = last_nav(route, before=d); equity = eq0*CAP
                held_codes = set(p2['code'] for p2 in st['positions'])
                for p in poss:
                    code = str(p.get('code','')).zfill(6); name = p.get('name','')
                    rej = None
                    if bad_name(name): rej = '禁ST/退/N/C'
                    bar,b = get_bar(code, d, deadline) if not rej else (None,{})
                    pvc = b.get(pd_,(None,)*4)[3] if b else None
                    if not rej and bar is None: rej = '无行情/停牌'
                    if not rej and pvc is None: rej = '缺昨收无法判涨停价'
                    if not rej and code not in held_codes and len(held_codes) >= 5:
                        rej = '超5只持仓上限(含在持)'
                    if not rej:
                        up = r2(pvc*(1+ratio(code)))
                        if bar[0] >= up - 1e-9: rej = '一字涨停买不进(开=%s=涨停价%s)'%(bar[0],up)
                    if not rej and p.get('buy_gate'):
                        bg = p['buy_gate']; gap = (bar[0]/pvc-1)*100
                        if 'max_gap_pct' in bg and gap >= float(bg['max_gap_pct']):
                            rej = '闸门弃单:高开%+.1f%%≥%s(预declare)'%(gap,bg['max_gap_pct'])
                        elif 'min_gap_pct' in bg and gap <= float(bg['min_gap_pct']):
                            rej = '闸门弃单:低开%+.1f%%≤%s(预declare)'%(gap,bg['min_gap_pct'])
                    if not rej:
                        w = float(p.get('weight_pct',0))*scale
                        budget = equity*w/100.0
                        shares = int(budget/(bar[0]*100))*100
                        cost_full = shares*bar[0]*(1+BUY_C)
                        if shares>0 and cost_full>cash:
                            shares = int(cash/(bar[0]*100*(1+BUY_C)))*100
                            cost_full = shares*bar[0]*(1+BUY_C)
                        if shares<=0: rej = '不足一手/现金不足'
                    if rej:
                        ledger(route,{'ev':'reject','d':d,'code':code,'name':name,'why':rej})
                        continue
                    cash -= cost_full
                    vol_d = bar[4] if len(bar)>4 else None
                    vol_pct = round(shares/vol_d*100,3) if vol_d else None
                    held_codes.add(code)
                    st['positions'].append({'code':code,'name':name,'shares':shares,'buy_px':bar[0],
                        'cost':round(cost_full,2),'buy_date':d,'plan_date':pd_,'weight':round(w,1),
                        'reason':p.get('reason',''),'vol_pct':vol_pct})
                    ledger(route,{'ev':'buy','d':d,'code':code,'name':name,'shares':shares,
                                  'px':bar[0],'cost':round(cost_full,2),'vol_pct':vol_pct,
                                  'liq_warn':('流动性警示:占当日成交量%.2f%%,滑点0.15%%属低估'%vol_pct) if (vol_pct and vol_pct>=1.0) else None})
                st['plans_done'].append(pd_)
        # 3) 逐日盯市
        mv = 0.0
        for pos in st['positions']:
            b = load_bars(pos['code'])
            px = b.get(d,(None,)*4)[3]
            if px is None:
                ks = [k for k in sorted(b.keys()) if k<=d]
                px = b[ks[-1]][3] if ks else pos['buy_px']
            mv += pos['shares']*px
        st['cash'] = round(cash,2); st['done'].append(d)
        nav_now = (cash+mv)/CAP
        _,nav = last_nav(route)
        nav[d] = {'nav':round(nav_now,6),'cash':round(cash,2),'mv':round(mv,2),'n':len(st['positions'])}
        jsave(nav_path(route),nav); jsave(st_path(route),st)
        write_status(route,d,st,nav)
        print(route,'settle',d,'nav=%.4f 持仓%d 现金%.0f'%(nav_now,len(st['positions']),cash))
    settle_bench(d,cal,deadline)

def settle_bench(d,cal,deadline):
    bp = os.path.join(simdir(),'基准净值.json')
    bn = jload(bp,{})
    if d in bn: return
    t = prev_td(prev_td(d,cal) or '',cal) if prev_td(d,cal) else None
    t1 = prev_td(d,cal)
    ks = sorted(bn.keys()); nav0 = bn[ks[-1]]['nav'] if ks else 1.0
    rec = {'nav':nav0,'r':None,'n':0,'total':0,'cohort':t}
    if t and t1:
        zp = os.path.join(ROOT,t,'zt_pool.csv')
        if os.path.exists(zp):
            rets = []; total = 0
            with open(zp,encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    code = str(row.get('代码','')).zfill(6); name = row.get('名称','')
                    if bad_name(name): continue
                    total += 1
                    b = load_bars(code)
                    if not b and time.time()<deadline:
                        fetch_bars(code,deadline); b = load_bars(code)
                    pvc = b.get(t,(None,)*4)[3]; o1 = b.get(t1,(None,)*4)[0]; o2 = b.get(d,(None,)*4)[0]
                    if None in (pvc,o1,o2): continue
                    if o1 >= r2(pvc*(1+ratio(code))) - 1e-9: continue  # 一字同样买不进
                    rets.append((o2*(1-SELL_C))/(o1*(1+BUY_C))-1)
            if rets:
                r = sum(rets)/len(rets)
                rec = {'nav':round(nav0*(1+r),6),'r':round(r*100,3),'n':len(rets),'total':total,'cohort':t}
    bn[d] = rec; jsave(bp,bn)
    print('bench',d,rec)

def week_bounds(d,cal):
    import datetime
    dt = datetime.date(int(d[:4]),int(d[4:6]),int(d[6:]))
    mon = dt - datetime.timedelta(days=dt.weekday())
    monday = mon.strftime('%Y%m%d')
    tds = [x for x in cal if monday <= x <= d]
    prev = [x for x in cal if x < monday]
    return (tds[-1] if tds else None), (prev[-1] if prev else None)

def week_ret(navdict,d,cal):
    we,pe = week_bounds(d,cal)
    if not we: return None
    def at(x):
        ks = [k for k in sorted(navdict.keys()) if k<=x]
        return navdict[ks[-1]]['nav'] if ks else 1.0
    if pe: return (at(we)/at(pe)-1)*100
    return (at(we)-1)*100

def write_status(route,d,st,nav):
    cal = calendar()
    bn = jload(os.path.join(simdir(),'基准净值.json'),{})
    wr = week_ret(nav,d,cal); bwr = week_ret(bn,d,cal) if bn else None
    closed = st['closed']; wins = [t for t in closed if t['ret_pct']>0]
    obj = {'date':d,'route':RNAME[route],'nav':nav.get(d,{}).get('nav'),
        '累计pct':round((nav.get(d,{}).get('nav',1)-1)*100,2),
        '本周pct':round(wr,2) if wr is not None else None,
        '基准本周pct':round(bwr,2) if bwr is not None else None,
        '现金':st['cash'],'持仓':st['positions'],
        '已平仓笔数':len(closed),'胜率pct':round(len(wins)/len(closed)*100,1) if closed else None,
        '最近平仓':closed[-5:],
        '说明':'只许本路agent读自己的状态文件;数字全部引擎产出,禁手算'}
    jsave(os.path.join(simdir(route),'状态.json'),obj)

# ── dashboard ─────────────────────────────────────────
CSS_D = 'background:linear-gradient(140deg,#171308,#12141c 46%);border:1px solid rgba(232,163,61,.28);border-radius:18px;padding:20px 24px;margin:18px 0;color:#eceef5;font-size:13px;box-shadow:0 12px 44px -18px rgba(232,163,61,.30),0 1px 3px rgba(0,0,0,.4)'
def color_ret(x):
    if x is None: return '<span style="color:#8d93a8">--</span>'
    c = '#ff5f56' if x>0 else ('#3fcb86' if x<0 else '#8d93a8')
    return '<b style="color:%s;font-family:ui-monospace,monospace">%+.2f%%</b>'%(c,x)

def nav_svg(navdict,bench,d):
    ks = sorted(navdict.keys())[-60:]
    if not ks: return '<div style="color:#8d93a8">尚无净值数据(明晚首个结算点)</div>'
    def series(dic):
        out = []
        for k in ks:
            kk = [x for x in sorted(dic.keys()) if x<=k]
            out.append(dic[kk[-1]]['nav'] if kk else 1.0)
        return out
    a = series(navdict); b = series(bench) if bench else []
    allv = a+(b or [])+[1.0]
    lo,hi = min(allv),max(allv)
    pad = max((hi-lo)*0.15, 0.004); lo-=pad; hi+=pad
    W,H = 640,150
    def pts(vs):
        n = len(vs)
        return ' '.join('%.1f,%.1f'%(20+(W-40)*i/max(n-1,1), H-18-(H-36)*(v-lo)/(hi-lo)) for i,v in enumerate(vs))
    y1 = H-18-(H-36)*(1.0-lo)/(hi-lo)
    s = ['<svg viewBox="0 0 %d %d" style="width:100%%;max-width:680px;display:block">'%(W,H)]
    s.append('<line x1="20" y1="%.1f" x2="%d" y2="%.1f" stroke="rgba(255,255,255,.13)" stroke-dasharray="3 4"/>'%(y1,W-20,y1))
    if b: s.append('<polyline points="%s" fill="none" stroke="#7b8cff" stroke-width="1.2" stroke-dasharray="5 4" opacity=".65"/>'%pts(b))
    s.append('<polyline class="drawin" points="%s" fill="none" stroke="#e8a33d" stroke-width="2.2"/>'%pts(a))
    _lx,_ly = 20+(W-40), H-18-(H-36)*(a[-1]-lo)/(hi-lo)
    s.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#e8a33d"/>'%(_lx,_ly))
    s.append('<text x="20" y="12" fill="#8d93a8" font-size="10" font-family="monospace">%s~%s  金=本账净值  紫虚线=影子基准(全场涨停同规则)  横线=1.0</text>'%(ks[0],ks[-1]))
    s.append('<text x="%d" y="%.1f" fill="#e8a33d" font-size="11" font-family="monospace" text-anchor="end">%.4f</text>'%(W-22,H-18-(H-36)*(a[-1]-lo)/(hi-lo)-5,a[-1]))
    s.append('</svg>')
    return ''.join(s)

def dashboard(d):
    bn = jload(os.path.join(simdir(),'基准净值.json'),{})
    cal = calendar()
    for route in ROUTES:
        st = load_state(route); _,nav = last_nav(route)
        stat = jload(os.path.join(simdir(route),'状态.json'),{})
        plan = jload(os.path.join(learn(),'交易计划_%s_%s.json'%(route,d)),{})
        h = ['<div style="%s">'%CSS_D]
        h.append('<div style="font-size:11.5px;letter-spacing:3px;color:#e8a33d;font-family:monospace">PAPER TRADING · 模拟实盘 · %s</div>'%RNAME[route])
        cum = stat.get('累计pct'); wk = stat.get('本周pct'); bwk = stat.get('基准本周pct')
        chips = ['累计 %s'%color_ret(cum),'本周 %s'%color_ret(wk),'基准本周 %s'%color_ret(bwk)]
        if stat.get('胜率pct') is not None: chips.append('平仓胜率 <b style="font-family:monospace">%s%%</b>(n=%s)'%(stat['胜率pct'],stat['已平仓笔数']))
        chips.append('本金100万 · 双边0.15% · 次日开盘买 · 卖点自主(最早T+2,每晚表态)')
        h.append('<div style="display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 12px;font-size:12.5px;color:#a8adbd">'+ ' '.join('<span>%s</span>'%c for c in chips)+'</div>')
        h.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:6px 20px;margin-top:6px;align-items:start"><div>')
        h.append('<div style="background:rgba(0,0,0,.22);border:1px solid rgba(255,255,255,.045);border-radius:12px;padding:10px 12px">'+nav_svg(nav,bn,d)+'</div>')
        if plan and plan.get('notes'):
            h.append('<div style="margin-top:10px;background:rgba(0,0,0,.22);border:1px solid rgba(255,255,255,.045);border-radius:10px;padding:9px 12px;color:#a8adbd;font-size:12.3px"><span style="color:#e8a33d;font-weight:700">交易心得</span> · %s</div>'%plan['notes'])
        h.append('</div><div>')
        # 持仓
        if st['positions']:
            cal2 = calendar()
            sells_tonight = {str(o.get('code','')).zfill(6):o for o in (plan.get('sells') or [])} if plan else {}
            h.append('<div style="margin-top:12px;color:#e8a33d;font-size:12px">当前持仓(卖点自主:每晚表态卖或持有)</div><table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:4px">')
            h.append('<tr style="color:#8d93a8"><td>代码/名称</td><td>股数</td><td>买价</td><td>浮盈</td><td>持有天数</td><td>今晚指令</td></tr>')
            for p in st['positions']:
                b = load_bars(p['code']); ks = [k for k in sorted(b.keys()) if k<=d]
                px = b[ks[-1]][3] if ks else p['buy_px']
                fl = (p['shares']*px/(p['cost'])-1)*100
                hd = len([x for x in cal2 if p['buy_date'] <= x <= d])
                if p.get('defer_sell'): ins = '<span style="color:#ff5f56">顺延卖出中(%d次)</span>'%p.get('defers',0)
                elif p['code'] in sells_tonight:
                    o = sells_tonight[p['code']]
                    ins = '<b style="color:#e8a33d">明日卖·%s</b>%s'%('收盘' if o.get('leg')=='close' else '开盘',
                          '(高开≥%s%%改收)'%o['sell_switch']['if_gap_ge_pct'] if o.get('sell_switch') else '')
                else: ins = '继续持有'
                h.append('<tr style="border-top:1px solid rgba(255,255,255,.07)"><td style="white-space:nowrap">%s %s</td><td style="font-family:monospace">%d</td><td style="font-family:monospace">%.2f</td><td>%s</td><td style="font-family:monospace">%d</td><td>%s</td></tr>'%(
                    p['code'],p['name'],p['shares'],p['buy_px'],color_ret(fl),hd,ins))
            h.append('</table>')
        else:
            h.append('<div style="margin-top:12px;color:#8d93a8">当前空仓</div>')
        # 当晚计划
        h.append('<div style="margin-top:12px;color:#e8a33d;font-size:12px">今晚指令单(%s发出,明日固定价执行)</div>'%d)
        buys = (plan.get('buys') or plan.get('positions') or []) if plan else []
        sells = (plan.get('sells') or []) if plan else []
        if plan and (buys or sells):
            h.append('<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:4px"><tr style="color:#8d93a8"><td>动作</td><td>代码/名称</td><td>仓位/腿</td><td>理由</td></tr>')
            for p in buys[:5]:
                gate = p.get('buy_gate') or {}
                gtxt = '·闸门高开≥%s弃'%gate['max_gap_pct'] if 'max_gap_pct' in gate else ('·闸门低开≤%s弃'%gate['min_gap_pct'] if 'min_gap_pct' in gate else '')
                h.append('<tr style="border-top:1px solid rgba(255,255,255,.07)"><td style="color:#ff5f56">买</td><td style="white-space:nowrap">%s %s</td><td style="font-family:monospace">%s%%%s</td><td style="color:#a8adbd">%s</td></tr>'%(
                    p.get('code'),p.get('name'),p.get('weight_pct'),gtxt,p.get('reason','')))
            for o in sells:
                stxt = '开盘' if o.get('leg')!='close' else '收盘'
                if o.get('sell_switch'): stxt += '(高开≥%s%%改收)'%o['sell_switch'].get('if_gap_ge_pct')
                h.append('<tr style="border-top:1px solid rgba(255,255,255,.07)"><td style="color:#3fcb86">卖</td><td style="white-space:nowrap">%s %s</td><td>%s</td><td style="color:#a8adbd">%s</td></tr>'%(
                    o.get('code'),o.get('name',''),stxt,o.get('reason','')))
            h.append('</table>')
        elif plan:
            h.append('<div style="color:#8d93a8;margin-top:4px">★今晚无买卖指令(在持票默认继续持有/或空仓)</div>')
        else:
            h.append('<div style="color:#8d93a8;margin-top:4px">今晚指令单未发出</div>')
        h.append('</div></div>')
        # 最近平仓
        rc = (stat.get('最近平仓') or [])
        if rc:
            h.append('<details style="margin-top:10px"><summary style="color:#8d93a8;cursor:pointer;font-size:12px">最近平仓明细(%d)</summary><table style="width:100%%;border-collapse:collapse;font-size:12px;margin-top:4px">'%len(rc))
            h.append('<tr style="color:#8d93a8"><td>票</td><td>买入</td><td>卖出</td><td>收益</td><td>腿/顺延</td></tr>')
            for t in reversed(rc):
                h.append('<tr style="border-top:1px solid rgba(255,255,255,.07)"><td>%s %s</td><td style="font-family:monospace">%s@%.2f</td><td style="font-family:monospace">%s@%.2f</td><td>%s</td><td>%s%s</td></tr>'%(
                    t['code'],t['name'],t['buy_date'],t['buy_px'],t['sell_date'],t['sell_px'],
                    color_ret(t['ret_pct']),('%s·持%d日'%('收' if t.get('leg')=='T_close' or t.get('leg')=='T2_close' else '开',t.get('hold_days',2))),
                    ('·顺延%d'%t['defers'] if t.get('defers') else '')))
            h.append('</table></details>')
        h.append('<div style="margin-top:10px;color:#5f6577;font-size:11px">铁律:发出版不可覆盖·一字拒单·跌停顺延·整手·逐日盯市·卖点自主(每晚表态,最早T+2,无卖单=持有)·≤5只·数字全出自引擎·本路只看本账+情绪周期</div>')
        h.append('</div>')
        out = os.path.join(simdir(route),'看板_%s.html'%d)
        with open(out,'w',encoding='utf-8') as f: f.write('\n'.join(h))
        print('dashboard',route,'->',out)

def inject(d):
    site = os.path.join(ROOT,'复盘','盯盘台')
    for route in ROUTES:
        kb = os.path.join(simdir(route),'看板_%s.html'%d)
        if not os.path.exists(kb):
            print('缺看板',route); continue
        block = '<!--PAPERTRADE-->\n'+open(kb,encoding='utf-8').read()+'\n<!--/PAPERTRADE-->'
        for pg in [os.path.join(site,PAGE[route]), os.path.join(site,'archive','%s.html'%d) if route=='master' else None]:
            if not pg or not os.path.exists(pg): continue
            h = open(pg,encoding='utf-8').read()
            if '<!--PAPERTRADE-->' in h:
                a = h.find('<!--PAPERTRADE-->'); b = h.find('<!--/PAPERTRADE-->')+len('<!--/PAPERTRADE-->')
                h = h[:a]+h[b:]
            i = h.find('class="hero"')
            j = h.find('<h2', i) if i>=0 else -1
            if j<0:
                print('!未找到锚点',pg); continue
            h = h[:j]+block+'\n'+h[j:]
            with open(pg,'w',encoding='utf-8') as f: f.write(h)
            chk = open(pg,encoding='utf-8').read()
            print('inject',route,'->',os.path.basename(pg),'OK' if '<!--PAPERTRADE-->' in chk else 'FAIL')

POOLFILES = {'auction':'竞价池发出_%s.json','lhb':'席位荐票_%s.json','theme':'题材荐票_%s.json',
             'logic':'逻辑荐票_%s.json','limitup':'涨停质量荐票_%s.json'}
def extract_codes(obj, acc):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in ('code','代码') and isinstance(v,(str,int)):
                c = str(v).zfill(6)
                if c.isdigit() and len(c)==6: acc.add(c)
            else: extract_codes(v,acc)
    elif isinstance(obj,list):
        for x in obj: extract_codes(x,acc)

def cohort_ret(codes,t,cal):
    t1 = next_td(t,cal); t2 = next_td(t1,cal) if t1 else None
    if not t1 or not t2: return None,0,len(codes)
    rets = []
    for c in codes:
        b = load_bars(c)
        pvc = b.get(t,(None,)*5)[3]; o1 = b.get(t1,(None,)*5)[0]; o2 = b.get(t2,(None,)*5)[0]
        if None in (pvc,o1,o2): continue
        if o1 >= r2(pvc*(1+ratio(c))) - 1e-9: continue
        rets.append((o2*(1-SELL_C))/(o1*(1+BUY_C))-1)
    return (sum(rets)/len(rets) if rets else None), len(rets), len(codes)

def weekly(d):
    cal = calendar()
    bn = jload(os.path.join(simdir(),'基准净值.json'),{})
    bwr = week_ret(bn,d,cal) if bn else None
    out = {'week_end':d,'基准周收益pct':round(bwr,2) if bwr is not None else None,'agents':{}}
    for route in ROUTES:
        _,nav = load_state(route),None
        navd = jload(nav_path(route),{})
        wr = week_ret(navd,d,cal) if navd else None
        fail = []
        if wr is None: verdict='无数据'
        else:
            if wr < 0: fail.append('绝对收益为负')
            if bwr is not None and wr < bwr: fail.append('跑输影子基准(%.2f%% vs %.2f%%)'%(wr,bwr))
            verdict = '不合格·须重训并写优化方向报告' if fail else '合格·写简短周记'
        out['agents'][route] = {'名':RNAME[route],'周收益pct':round(wr,2) if wr is not None else None,
                                '判定':verdict,'原因':fail}
        print(route,out['agents'][route])
    # 路内池基准(该路当周荐票发出版全体票,同规则同成本;跨周末未实现cohort自动跳过记覆盖)
    import datetime
    dt = datetime.date(int(d[:4]),int(d[4:6]),int(d[6:]))
    monday = (dt - datetime.timedelta(days=dt.weekday())).strftime('%Y%m%d')
    wk_tds = [x for x in cal if monday <= x <= d]
    pools = {}
    for route,pat in POOLFILES.items():
        nav_p = 1.0; used = 0; cov = []
        for t in wk_tds:
            f = os.path.join(learn(),pat%t)
            if not os.path.exists(f): continue
            acc = set(); extract_codes(jload(f,{}),acc)
            r,nn,tot = cohort_ret(sorted(acc),t,cal)
            if r is not None:
                nav_p *= (1+r); used += 1; cov.append('%s:%d/%d'%(t,nn,tot))
        pools[route] = {'周池基准pct':round((nav_p-1)*100,2) if used else None,'cohorts':used,'覆盖':cov}
    out['路内池基准'] = pools
    # 卖腿反事实(仅归因非战绩;顺延/止损单独标)
    cf = {}
    for route in ROUTES:
        st = load_state(route)
        rows = [t for t in st['closed'] if monday <= t['sell_date'] <= d]
        if not rows: continue
        act = []; ao = []; ac = []; skip = 0
        for t in rows:
            if t.get('defers'): skip += 1; continue
            b = load_bars(t['code']).get(t['sell_date'])
            if not b: skip += 1; continue
            act.append(t['ret_pct'])
            ao.append(((b[0]*(1-SELL_C))/(t['buy_px']*(1+BUY_C))-1)*100)
            ac.append(((b[3]*(1-SELL_C))/(t['buy_px']*(1+BUY_C))-1)*100)
        if act:
            cf[route] = {'n':len(act),'实际均pct':round(sum(act)/len(act),2),
                         '全T2开均pct':round(sum(ao)/len(ao),2),'全T2收均pct':round(sum(ac)/len(ac),2),
                         '跳过(顺延/缺bars)':skip,'口径':'反事实仅归因,非战绩'}
    out['卖腿反事实'] = cf
    p = os.path.join(simdir(),'周考核_%s.json'%d); jsave(p,out)
    print('路内池基准:',json.dumps(pools,ensure_ascii=False))
    print('卖腿反事实:',json.dumps(cf,ensure_ascii=False))
    print('周考核 ->',p)

def morning(d):
    """9:25-9:31实时预告:sina竞价价机判今日买卖动作(信息展示,结算以bars为准)"""
    import urllib.request, re as _re
    cal = calendar(); pd_ = prev_td(d,cal)
    codes = {}
    for route in ROUTES:
        plan = jload(os.path.join(learn(),'交易计划_%s_%s.json'%(route,pd_)),{}) if pd_ else {}
        for p in (plan.get('buys') or plan.get('positions') or [])[:5]:
            codes.setdefault(str(p.get('code','')).zfill(6),[]).append((route,'buy',p))
        sell_codes = {str(o.get('code','')).zfill(6):o for o in (plan.get('sells') or [])}
        st = load_state(route)
        for pos in st['positions']:
            if pos.get('defer_sell') or pos['code'] in sell_codes:
                codes.setdefault(pos['code'],[]).append((route,'sell',sell_codes.get(pos['code'],{})))
    if not codes:
        print('今日无待执行买卖'); return
    lst = ','.join(sina_sym(c) for c in codes if not sina_sym(c).startswith('bj'))
    q = {}
    try:
        req = urllib.request.Request('https://hq.sinajs.cn/list='+lst,headers={'Referer':'https://finance.sina.com.cn'})
        for l in urllib.request.urlopen(req,timeout=10).read().decode('gbk').strip().split('\n'):
            mm = _re.search('str_(?:sh|sz)([0-9]{6})="([^"]*)"',l)
            if not mm: continue
            p = mm.group(2).split(',')
            if len(p)>10 and float(p[2])>0:
                q[mm.group(1)] = {'今开':float(p[1]),'昨收':float(p[2])}
    except Exception as e:
        print('sina接口不可达:',e)
    out = {}
    for c,acts in codes.items():
        g = q.get(c)
        gap = round((g['今开']/g['昨收']-1)*100,2) if (g and g['今开']>0) else None
        for route,kind,p in acts:
            rec = {'gap_pct':gap}
            if kind=='buy':
                bg = p.get('buy_gate') or {}
                if gap is None: rec['buy_action']='未采集(结算以bars为准)'
                elif 'max_gap_pct' in bg and gap>=float(bg['max_gap_pct']): rec['buy_action']='预告:闸门弃单(高开%+.1f%%)'%gap
                elif 'min_gap_pct' in bg and gap<=float(bg['min_gap_pct']): rec['buy_action']='预告:闸门弃单(低开%+.1f%%)'%gap
                else: rec['buy_action']='预告:照买'
            else:
                sw = p.get('sell_switch') or {}
                if gap is not None and gap>=float(sw.get('if_gap_ge_pct',1e9)): rec['sell_action']='预告:高开达阈,改持到收盘卖'
                else: rec['sell_action']='预告:按declare腿卖'
            out.setdefault(route,{})[c] = rec
    jsave(os.path.join(simdir(),'早盘执行_%s.json'%d),out)
    print(json.dumps(out,ensure_ascii=False))

if __name__ == '__main__':
    args = sys.argv[1:]
    root_override = None
    if '--root' in args:
        i = args.index('--root'); root_override = args[i+1]; args = args[:i]+args[i+2:]
    ROOT = root_override or find_root()
    if len(args)<2:
        print(__doc__); sys.exit(0)
    cmd, d = args[0], args[1]
    {'settle':settle,'dashboard':dashboard,'inject':inject,'weekly':weekly,'morning':morning}[cmd](d)
