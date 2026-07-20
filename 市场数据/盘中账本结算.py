#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中账本结算.py · 第七账「盘中作战账户」独立逐日盯市(阶段②B,变更总账#031)
版本戳: v1.0 | 2026-07-18

定位(设计稿v1.9.2 §3.3.2):
  route=intraday,本金100万,nav起点1.0;独立账本 _学习/_模拟盘/intraday/;
  ★成交只产自两源:①盘中规则引擎.py 执行流水(盘中/{d}/执行流水.jsonl)
                   ②检查点会话决断(盘中/{d}/临盘决断_{d}_*.json 内 fills 列表,schema见下)
  ★不接模拟盘引擎.py:master与五子路v2.1零触碰,本脚本自带全部结算逻辑。
  ★账内纯晚间影子(主裁判):同一份 盘中/{d}/playbook.json,忽略全部盘中条款,
    按旧口径T+1开盘买(trigger.open_range当buy_gate用)/sells按leg开盘或收盘卖;
    临盘增益pp = 盘中账nav - 影子nav(×100),周考核唯一裁判。

口径(与模拟盘v2.1一致处全数继承):
  成本双边0.15%(买0.05%卖0.10%,结算侧计);流水px_exec已含盘中滑点0.10%;
  一字拒单/整手/禁ST退NC/跌停封死顺延次日开盘/停牌顺延/T+1不可卖;
  影子仓位=影子权益×weight;盘中账数量=流水qty(引擎按本金100万整手);
  卖出=在持全量;涨停封板buy defer收盘未成=如实弃单(引擎finalize已abort)。

临盘决断json成交接口(检查点会话写,发出版不可覆盖):
  盘中/{d}/临盘决断_{d}_{场次}.json:
  {"date","session","ts","fills":[{"ts","code","name","action":"fill_buy|fill_sell",
    "px","px_exec","qty"(买必带,整手),"rule","route","note"}], ...其余决断字段自由}
  无fills字段=纯判断决断,本脚本跳过。px_exec必带(检查点按留档tick+滑点0.10%自算)。

用法: python3 盘中账本结算.py settle YYYYMMDD
幂等: state.done含d则跳过;重跑不重复记账。零网络,只读本地。
"""
import os, sys, json, math, csv, glob, hashlib, datetime, re

CAP = 1_000_000.0
BUY_C, SELL_C = 0.0005, 0.0010
ROUTE = 'intraday'
RNAME = '盘中作战账户(第七账)'

def find_root():
    for p in glob.glob('/sessions/*/mnt/股票数据/市场数据'):
        return p
    if os.path.isdir(r'D:\股票数据\市场数据'): return r'D:\股票数据\市场数据'
    return '.'
ROOT = find_root()

def r2(x): return math.floor(x*100+0.5)/100.0
def learn(): return os.path.join(ROOT,'_学习')
def simdir():
    d = os.path.join(learn(),'_模拟盘',ROUTE)
    os.makedirs(d,exist_ok=True); return d
def intradir(d): return os.path.join(ROOT,'盘中',d)

def jload(p,default):
    try:
        with open(p,encoding='utf-8') as f: return json.load(f)
    except Exception: return default
def jsave(p,obj):
    tmp = p+'.tmp'
    with open(tmp,'w',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=1)
    os.replace(tmp,p)
def ledger(ev):
    with open(os.path.join(simdir(),'账本.jsonl'),'a',encoding='utf-8') as f:
        f.write(json.dumps(ev,ensure_ascii=False)+'\n')

def calendar():
    return sorted(x for x in os.listdir(ROOT) if len(x)==8 and x.isdigit())
def prev_td(d, cal=None):
    xs = [x for x in (cal or calendar()) if x < d]
    return xs[-1] if xs else None

_bcache = {}
def load_bars(code):
    if code in _bcache: return _bcache[code]
    out = {}
    for base in [os.path.join(learn(),'_bars_cache'),
                 os.path.join(learn(),'_模拟盘','_bars_extra')]:
        p = os.path.join(base, code+'.csv')
        if not os.path.exists(p): continue
        try:
            with open(p,encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    dt = re.sub(r'\D','',str(row.get('date','')))[:8]
                    if len(dt)==8 and row.get('open'):
                        try:
                            vol = None
                            try: vol = float(row.get('volume') or 0) or None
                            except Exception: pass
                            out[dt] = (float(row['open']),float(row['high']),
                                       float(row['low']),float(row['close']),vol)
                        except Exception: pass
        except Exception: pass
    _bcache[code] = out
    return out

def ratio(code):
    if code.startswith(('30','68')): return 0.20
    if code.startswith(('8','4','92')): return 0.30
    return 0.10
def bad_name(name):
    n = (name or '')
    return ('ST' in n.upper()) or ('退' in n) or n.startswith('N') or n.startswith('C')

# ── 状态 ──────────────────────────────────────────────
def st_path():  return os.path.join(simdir(),'state.json')
def sh_path():  return os.path.join(simdir(),'shadow_state.json')
def nav_path(): return os.path.join(simdir(),'净值.json')
def blank_state():
    return {'cash':CAP,'positions':[],'done':[],'closed':[],'skips':[]}
def last_nav(navdict, before=None, key='nav'):
    ks = [k for k in sorted(navdict.keys()) if (before is None or k < before)]
    return (navdict[ks[-1]].get(key,1.0) if ks else 1.0)

# ── 事件源 ────────────────────────────────────────────
def read_events(d):
    """合并规则引擎流水+检查点决断fills,按ts排序。"""
    evs = []
    fp = os.path.join(intradir(d),'执行流水.jsonl')
    if os.path.isfile(fp):
        for ln in open(fp,encoding='utf-8'):
            ln = ln.strip()
            if not ln: continue
            try:
                r = json.loads(ln); r['src'] = 'engine'; evs.append(r)
            except Exception: pass
    for cf in sorted(glob.glob(os.path.join(intradir(d),'临盘决断_*.json'))):
        obj = jload(cf,{})
        for r in (obj.get('fills') or []):
            if isinstance(r,dict):
                r = dict(r); r['src'] = 'checkpoint:'+os.path.basename(cf); evs.append(r)
    evs.sort(key=lambda r: str(r.get('ts','')))
    return evs

def wt_from_note(note):
    m = re.search(r'weight([\d.]+)', note or '')
    try: return float(m.group(1)) if m else None
    except Exception: return None

# ── 通用腿:顺延卖(跌停封死/停牌 顺延次日开盘,旧口径) ──
def flush_defers(st, d, cal, tag):
    keep = []
    for pos in st['positions']:
        if not pos.get('defer_sell'):
            keep.append(pos); continue
        bars = load_bars(pos['code']); bar = bars.get(d)
        pd_ = prev_td(d,cal)
        pvc = bars.get(pd_,(None,)*5)[3] if pd_ else None
        if bar is None:
            pos['defers'] = pos.get('defers',0)+1
            ledger({'ev':'defer','acct':tag,'d':d,'code':pos['code'],'why':'无行情/停牌,顺延'})
            keep.append(pos); continue
        px = bar[0]
        if pvc is not None and px <= r2(pvc*(1-ratio(pos['code'])))+1e-9:
            pos['defers'] = pos.get('defers',0)+1
            ledger({'ev':'defer','acct':tag,'d':d,'code':pos['code'],'why':'开盘仍跌停,顺延','px':px})
            keep.append(pos); continue
        close_pos(st, pos, d, px, 'T_open', cal, tag, note='顺延单开盘成交(defers=%d)'%pos.get('defers',0))
    st['positions'] = keep

def close_pos(st, pos, d, px, leg, cal, tag, note=''):
    proceeds = pos['shares']*px*(1-SELL_C)
    st['cash'] += proceeds
    hold_days = len([x for x in cal if pos['buy_date'] < x <= d])
    tr = {'code':pos['code'],'name':pos.get('name',''),'plan_date':pos.get('plan_date'),
          'buy_date':pos['buy_date'],'buy_px':pos['buy_px'],'sell_date':d,'sell_px':px,
          'leg':leg,'hold_days':hold_days,'defers':pos.get('defers',0),
          'weight':pos.get('weight'),'route':pos.get('route'),
          'pnl':round(proceeds-pos['cost'],2),
          'ret_pct':round((proceeds/pos['cost']-1)*100,2),'reason':pos.get('reason','')}
    st['closed'].append(tr)
    ledger({'ev':'sell','acct':tag,'d':d,'note':note,**tr})

# ── 盘中账(真腿):按流水记账 ──────────────────────────
def settle_real(st, d, cal, evs):
    flush_defers(st, d, cal, 'real')
    st['skips'] = []
    sell_defer_codes = {}
    filled_sell = set()
    for r in evs:
        act = r.get('action'); code = str(r.get('code','')).zfill(6)
        if act == 'fill_buy':
            qty = r.get('qty'); px = r.get('px_exec') or r.get('px')
            if not qty or not px:
                ledger({'ev':'reject','acct':'real','d':d,'code':code,'why':'流水缺qty/px_exec,拒单(零编造)','src':r.get('src')}); continue
            qty = int(qty); px = float(px)
            cost = qty*px*(1+BUY_C)
            if cost > st['cash']:
                qty2 = int(st['cash']/(px*100*(1+BUY_C)))*100
                ledger({'ev':'warn','acct':'real','d':d,'code':code,
                        'why':'现金不足,缩股%d→%d'%(qty,qty2)})
                qty = qty2; cost = qty*px*(1+BUY_C)
            if qty <= 0:
                ledger({'ev':'reject','acct':'real','d':d,'code':code,'why':'不足一手/现金不足'}); continue
            st['cash'] -= cost
            st['positions'].append({'code':code,'name':r.get('name',''),'shares':qty,
                'buy_px':px,'cost':round(cost,2),'buy_date':d,'plan_date':prev_td(d,cal),
                'weight':wt_from_note(r.get('note')),'route':r.get('route'),
                'rule':r.get('rule'),'src':r.get('src'),'reason':(r.get('note') or '')[:80]})
            ledger({'ev':'buy','acct':'real','d':d,'code':code,'name':r.get('name',''),
                    'shares':qty,'px':px,'cost':round(cost,2),'rule':r.get('rule'),'src':r.get('src')})
        elif act == 'fill_sell':
            px = r.get('px_exec') or r.get('px')
            if not px:
                ledger({'ev':'warn','acct':'real','d':d,'code':code,'why':'fill_sell缺px_exec,忽略'}); continue
            px = float(px)
            hit = [p for p in st['positions'] if p['code']==code]
            if not hit:
                ledger({'ev':'warn','acct':'real','d':d,'code':code,'why':'流水卖出但无在持,忽略'}); continue
            ok = False
            for pos in list(hit):
                if pos['buy_date'] >= d:
                    ledger({'ev':'warn','acct':'real','d':d,'code':code,'why':'T+1制度:当日买当日卖流水,忽略'}); continue
                st['positions'].remove(pos)
                close_pos(st, pos, d, px, 'INTRA', cal, 'real',
                          note='盘中成交 rule=%s src=%s'%(r.get('rule'),r.get('src')))
                ok = True
            if ok: filled_sell.add(code)
        elif act == 'defer':
            if r.get('rule') != 'zt_no_chase':
                sell_defer_codes[code] = str(r.get('note',''))
        elif act == 'skip':
            st['skips'].append({'code':code,'name':r.get('name',''),'rule':r.get('rule'),
                                'note':(r.get('note') or '')[:80]})
    for code, why in sell_defer_codes.items():
        if code in filled_sell: continue
        for pos in st['positions']:
            if pos['code']==code and pos['buy_date'] < d and not pos.get('defer_sell'):
                pos['defer_sell'] = True
                pos['defers'] = pos.get('defers',0)+1
                ledger({'ev':'defer','acct':'real','d':d,'code':code,'why':'流水defer未成交,顺延次日开盘:'+why[:60]})

# ── 影子账(纯晚间旧口径):同playbook,T+1开盘买/leg卖 ──
def norm_routes(pb):
    if isinstance(pb, list):
        return [(p.get('route') or 'r%d'%i, p) for i,p in enumerate(pb) if isinstance(p,dict)]
    if isinstance(pb, dict):
        if isinstance(pb.get('routes'), list):
            return [(p.get('route') or 'r%d'%i, p) for i,p in enumerate(pb['routes']) if isinstance(p,dict)]
        if 'buys' in pb or 'sells' in pb or 'watch' in pb:
            return [(pb.get('route') or 'master', pb)]
        return [(k,v) for k,v in pb.items() if isinstance(v,dict) and ('buys' in v or 'sells' in v or 'watch' in v)]
    return []

def settle_shadow(st, d, cal, pb, navdict):
    flush_defers(st, d, cal, 'shadow')
    pd_ = prev_td(d,cal)
    routes = norm_routes(pb) if pb else []
    sells_map = {}
    for rt,plan in routes:
        for o in (plan.get('sells') or []):
            sells_map[str(o.get('code','')).zfill(6)] = o
    keep = []
    for pos in st['positions']:
        o = sells_map.get(pos['code'])
        if o is None or pos['buy_date'] >= d:
            keep.append(pos); continue
        bars = load_bars(pos['code']); bar = bars.get(d)
        pvc = bars.get(pd_,(None,)*5)[3] if pd_ else None
        if bar is None:
            pos['defer_sell']=True; pos['defers']=pos.get('defers',0)+1
            ledger({'ev':'defer','acct':'shadow','d':d,'code':pos['code'],'why':'无行情/停牌'})
            keep.append(pos); continue
        leg = 'close' if o.get('leg')=='close' else 'open'
        px = bar[3] if leg=='close' else bar[0]
        if pvc is not None and px <= r2(pvc*(1-ratio(pos['code'])))+1e-9:
            pos['defer_sell']=True; pos['defers']=pos.get('defers',0)+1
            ledger({'ev':'defer','acct':'shadow','d':d,'code':pos['code'],'why':'跌停无法卖出','px':px})
            keep.append(pos); continue
        close_pos(st, pos, d, px, 'T_close' if leg=='close' else 'T_open', cal, 'shadow')
    st['positions'] = keep
    eq0 = last_nav(navdict, before=d, key='sh_nav'); equity = eq0*CAP
    held_by_rt = {}
    for p in st['positions']:
        held_by_rt.setdefault(p.get('route'),set()).add(p['code'])
    for rt,plan in routes:
        buys = (plan.get('buys') or [])[:5]
        wsum = sum(float(x.get('weight_pct',0) or 0) for x in buys)
        scale = 100.0/wsum if wsum>100 else 1.0
        if scale<1.0:
            ledger({'ev':'warn','acct':'shadow','d':d,'route':rt,'why':'仓位合计%s>100,压缩'%wsum})
        for x in buys:
            code = str(x.get('code','')).zfill(6); name = x.get('name','')
            rej = None
            if bad_name(name): rej = '禁ST/退/N/C'
            trig = x.get('trigger')
            if not rej and trig is not None and not (isinstance(trig,dict) and trig.get('type')=='open_range'):
                rej = 'trigger不可机读(与引擎对称跳过)'
            bars = load_bars(code) if not rej else {}
            bar = bars.get(d) if not rej else None
            pvc = bars.get(pd_,(None,)*5)[3] if (not rej and pd_) else None
            if not rej and bar is None: rej = '无行情/停牌'
            if not rej and pvc is None: rej = '缺昨收无法判涨停价'
            if not rej:
                held = held_by_rt.setdefault(rt,set())
                if code not in held and len(held) >= 5: rej = '超5只持仓上限(该路)'
            if not rej:
                up = r2(pvc*(1+ratio(code)))
                if bar[0] >= up-1e-9: rej = '一字涨停买不进(开=%s=涨停价%s)'%(bar[0],up)
            if not rej and isinstance(trig,dict) and trig.get('type')=='open_range':
                gap = (bar[0]/pvc-1)*100
                mn = float(trig.get('min_gap',-100)); mx = float(trig.get('max_gap',100))
                if not (mn - 1e-9 <= gap <= mx + 1e-9):
                    rej = '闸门弃单:gap%+.2f%%越界[%g,%g](旧口径=开盘gap)'%(gap,mn,mx)
            if not rej:
                w = float(x.get('weight_pct',0) or 0)*scale
                budget = equity*w/100.0
                shares = int(budget/(bar[0]*100))*100
                cost = shares*bar[0]*(1+BUY_C)
                if shares>0 and cost>st['cash']:
                    shares = int(st['cash']/(bar[0]*100*(1+BUY_C)))*100
                    cost = shares*bar[0]*(1+BUY_C)
                if shares<=0: rej = '不足一手/现金不足'
            if rej:
                ledger({'ev':'reject','acct':'shadow','d':d,'code':code,'name':name,'why':rej}); continue
            st['cash'] -= cost
            held_by_rt.setdefault(rt,set()).add(code)
            st['positions'].append({'code':code,'name':name,'shares':shares,'buy_px':bar[0],
                'cost':round(cost,2),'buy_date':d,'plan_date':pd_,'weight':round(w,1),
                'route':rt,'reason':(x.get('reason') or '')[:80]})
            ledger({'ev':'buy','acct':'shadow','d':d,'code':code,'name':name,
                    'shares':shares,'px':bar[0],'cost':round(cost,2),'route':rt})

def mark(st, d):
    mv = 0.0
    for pos in st['positions']:
        b = load_bars(pos['code'])
        px = b.get(d,(None,)*5)[3]
        if px is None:
            ks = [k for k in sorted(b.keys()) if k<=d]
            px = b[ks[-1]][3] if ks else pos['buy_px']
        pos['last_px'] = px
        mv += pos['shares']*px
    return mv

# ── 周口径/展示 ───────────────────────────────────────
def week_bounds(d,cal):
    dt = datetime.date(int(d[:4]),int(d[4:6]),int(d[6:]))
    mon = (dt - datetime.timedelta(days=dt.weekday())).strftime('%Y%m%d')
    tds = [x for x in cal if mon <= x <= d]
    prev = [x for x in cal if x < mon]
    return (tds[-1] if tds else None), (prev[-1] if prev else None)
def week_ret(navdict,d,cal,key='nav'):
    we,pe = week_bounds(d,cal)
    if not we: return None
    def at(x):
        ks = [k for k in sorted(navdict.keys()) if k<=x]
        return (navdict[ks[-1]].get(key,1.0) if ks else 1.0)
    return (at(we)/at(pe)-1)*100 if pe else (at(we)-1)*100
def sse_week(d,cal):
    obj = jload(os.path.join(learn(),'_指数基准.json'),{})
    closes = obj.get('sse_close') or {}
    if not closes: return None
    we,pe = week_bounds(d,cal)
    def at(x):
        ks = [k for k in sorted(closes.keys()) if k<=x]
        return closes[ks[-1]] if ks else None
    if not we: return None
    a,b = at(we),(at(pe) if pe else None)
    return round((a/b-1)*100,2) if (a and b) else None

def write_status(d, st, sh, navdict, cal):
    nv = navdict.get(d,{})
    closed = st['closed']; wins = [t for t in closed if (t.get('ret_pct') or 0)>0]
    wr = week_ret(navdict,d,cal,'nav'); swr = week_ret(navdict,d,cal,'sh_nav')
    out = {'date':d,'route':RNAME,
        'nav':nv.get('nav'),'累计pct':round((nv.get('nav',1)-1)*100,2),
        '本周pct':round(wr,2) if wr is not None else None,
        '基准本周pct':round(swr,2) if swr is not None else None,
        '基准说明':'主裁判=账内纯晚间影子(同预案单旧口径);上证为展示参考',
        '影子nav':nv.get('sh_nav'),
        '临盘增益pp_累计':nv.get('gain_pp'),
        '临盘增益pp_本周':round(wr-swr,2) if (wr is not None and swr is not None) else None,
        '上证本周pct':sse_week(d,cal),
        '现金':round(st['cash'],2),
        '持仓':st['positions'],
        '已平仓笔数':len(closed),
        '胜率pct':round(len(wins)/len(closed)*100,1) if closed else None,
        '最近平仓':closed[-5:],
        '待人判':st.get('skips') or []}
    jsave(os.path.join(simdir(),'状态.json'), out)

# ── 主流程 ────────────────────────────────────────────
def settle(d):
    cal = calendar()
    if d not in cal:
        print('非交易日或数据目录缺失:',d); return 2
    st = jload(st_path(), blank_state())
    sh = jload(sh_path(), blank_state())
    navdict = jload(nav_path(), {})
    if d in st['done']:
        print(ROUTE,'已结算过',d); return 0
    pf = os.path.join(intradir(d),'playbook.json')
    pb = jload(pf,None)
    if os.path.isfile(pf):
        reg = jload(os.path.join(simdir(),'发出登记.json'),{})
        sha = hashlib.sha256(open(pf,'rb').read()).hexdigest()[:16]
        key = '%s_%s'%(ROUTE,d)
        if key in reg and reg[key]!=sha:
            ledger({'ev':'warn','d':d,'why':'★playbook发出版被改动!以首见sha为准记档','sha_now':sha})
        else:
            reg[key]=sha; jsave(os.path.join(simdir(),'发出登记.json'),reg)
    evs = read_events(d)
    if not evs and pb is None:
        ledger({'ev':'warn','d':d,'why':'当日无流水无playbook,仅盯市'})
    settle_real(st, d, cal, evs)
    settle_shadow(sh, d, cal, pb, navdict)
    mv = mark(st,d); smv = mark(sh,d)
    nav_now = (st['cash']+mv)/CAP; sh_now = (sh['cash']+smv)/CAP
    navdict[d] = {'nav':round(nav_now,6),'cash':round(st['cash'],2),'mv':round(mv,2),
                  'n':len(st['positions']),
                  'sh_nav':round(sh_now,6),'sh_cash':round(sh['cash'],2),
                  'sh_mv':round(smv,2),'sh_n':len(sh['positions']),
                  'gain_pp':round((nav_now-sh_now)*100,2)}
    st['cash']=round(st['cash'],2); sh['cash']=round(sh['cash'],2)
    st['done'].append(d)
    sh.setdefault('done',[]).append(d)
    jsave(nav_path(),navdict); jsave(st_path(),st); jsave(sh_path(),sh)
    write_status(d, st, sh, navdict, cal)
    ledger({'ev':'mark','d':d,**navdict[d]})
    print('%s settle %s nav=%.4f(影%.4f 增益%+.2fpp) 持%d 现金%.0f 流水事件%d'
          % (ROUTE,d,nav_now,sh_now,(nav_now-sh_now)*100,len(st['positions']),st['cash'],len(evs)))
    return 0

def main():
    if len(sys.argv)>=3 and sys.argv[1]=='settle' and re.match(r'^\d{8}$',sys.argv[2]):
        sys.exit(settle(sys.argv[2]))
    print('盘中账本结算.py · 第七账intraday独立结算(阶段②B)')
    print('用法: python3 盘中账本结算.py settle YYYYMMDD'); sys.exit(2)

if __name__ == '__main__':
    main()
