# -*- coding: utf-8 -*-
"""20261105 limitup 路：重建全样本前向表（含 gap）用于格重算。零后视镜：样本只取 日<=20261105。"""
import os, sys, json, glob
import pandas as pd, numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
CDIR = os.path.join(L, '_bars_cache')
OUT = os.path.join(L, '_tmp_P_20261105.pkl')

def num(v, d=None):
    try:
        x = pd.to_numeric(v, errors='coerce')
        return float(x) if x == x else d
    except Exception:
        return d

def tradedays():
    return sorted([os.path.basename(x) for x in glob.glob(os.path.join(BASE, '2026*'))
                   if os.path.isdir(x) and os.path.isfile(os.path.join(x, 'zt_pool.csv'))])

def factor_table():
    days = [d for d in tradedays() if d <= '20261105']
    rows = []
    for d in days:
        df = pd.read_csv(os.path.join(BASE, d, 'zt_pool.csv'), dtype={'代码': str})
        df['代码'] = df['代码'].str.zfill(6)
        df = df[~df['名称'].astype(str).str.contains('退')]
        for _, r in df.iterrows():
            mv = num(r.get('流通市值')); fj = num(r.get('封板资金'))
            fb = str(r['首次封板时间']).split('.')[0].zfill(6)
            rows.append(dict(日=d, 代码=r['代码'], 名称=r.get('名称'),
                             封额亿=round(fj/1e8, 2) if fj else None,
                             封单比=round(fj/mv*100, 3) if (fj and mv and mv > 0) else None,
                             首封=fb[:2]+':'+fb[2:4],
                             连板=int(num(r.get('连板数', 1), 1) or 1),
                             开板=int(num(r.get('炸板次数', 0), 0) or 0),
                             换手=num(r.get('换手率'), 0.0),
                             市值亿=mv/1e8 if mv else None,
                             股价=num(r.get('最新价'), 0.0),
                             行业=str(r.get('所属行业'))))
    tp = os.path.join(L, '_ths_zt_pool.json')
    if os.path.isfile(tp):
        ths = json.load(open(tp, encoding='utf-8'))
        for d in sorted(ths):
            if d in days or d > '20261105':
                continue
            for x in ths[d]:
                c = str(x.get('code', '')).zfill(6); nm = str(x.get('name') or '')
                if '退' in nm:
                    continue
                import datetime as dt
                try:
                    fs = dt.datetime.fromtimestamp(int(x.get('first_limit_up_time')),
                                                   tz=dt.timezone(dt.timedelta(hours=8))).strftime('%H:%M')
                except Exception:
                    fs = None
                m = x.get('high_days')
                import re
                mm = re.search(r'(\d+)板', str(m or ''))
                rows.append(dict(日=d, 代码=c, 名称=nm, 封额亿=None, 封单比=None, 首封=fs,
                                 连板=int(mm.group(1)) if mm else 1,
                                 开板=int(x.get('open_num') or 0),
                                 换手=None, 市值亿=None, 股价=None, 行业=None))
    P = pd.DataFrame(rows)
    # 历史 THS 样本缺换手/市值 → 用 bars 缓存 turn_ 列补（缓存有 turnover/circ_mv亿 时）
    return P

def load_bars(c, cache={}):
    if c in cache:
        return cache[c]
    f = os.path.join(CDIR, c+'.csv')
    if not os.path.isfile(f):
        cache[c] = None
        return None
    try:
        b = pd.read_csv(f)
        b['date'] = b['date'].astype(str).str.replace('-', '')
        cache[c] = b
        return b
    except Exception:
        cache[c] = None
        return None

def enrich(P):
    E1 = []; E2 = []; T1 = []; T2 = []; GAP = []; VOL = []; POS = []; MOM = []
    TO_FILL = []; MV_FILL = []
    for r in P.itertuples():
        b = load_bars(r.代码)
        e1 = e2 = t1 = t2 = gap = np.nan; v = p = mo = np.nan
        tof = mvf = np.nan
        if b is not None:
            idx = np.where(b['date'].values == r.日)[0]
            if len(idx):
                i = int(idx[0]); n = len(b)
                cl = b['close'].values; op = b['open'].values
                if 'turnover' in b.columns and b['turnover'].values[i] == b['turnover'].values[i]:
                    tof = float(b['turnover'].values[i])
                if 'circ_mv亿' in b.columns and b['circ_mv亿'].values[i] == b['circ_mv亿'].values[i]:
                    mvf = float(b['circ_mv亿'].values[i])
                if 'volume' in b.columns and i >= 4:
                    pv = b['volume'].values[max(0, i-5):i]
                    if len(pv) >= 3 and pv.mean() > 0:
                        v = float(b['volume'].values[i])/float(pv.mean())
                if i >= 1:
                    mx = cl[max(0, i-59):i+1].max()
                    if mx > 0:
                        p = cl[i]/mx
                if i >= 6 and cl[i-6] > 0:
                    mo = (cl[i-1]/cl[i-6]-1)*100
                if i+1 < n:
                    Tc = cl[i]; o1 = op[i+1]
                    if Tc > 0:
                        t1 = cl[i+1]/Tc-1
                        if o1 > 0:
                            gap = o1/Tc-1
                    if o1 > 0:
                        e1 = cl[i+1]/o1-1
                        if i+2 < n:
                            e2 = cl[i+2]/o1-1
                            if Tc > 0:
                                t2 = cl[i+2]/Tc-1
        E1.append(e1); E2.append(e2); T1.append(t1); T2.append(t2); GAP.append(gap)
        VOL.append(v); POS.append(p); MOM.append(mo)
        TO_FILL.append(tof); MV_FILL.append(mvf)
    P['E1'] = E1; P['E2'] = E2; P['T1'] = T1; P['T2'] = T2; P['GAP'] = GAP
    P['量比'] = VOL; P['位置'] = POS; P['动能'] = MOM
    to = P['换手'].astype(float).copy(); mv = P['市值亿'].astype(float).copy()
    fill_to = pd.Series(TO_FILL); fill_mv = pd.Series(MV_FILL)
    to = to.where(to.notna(), fill_to); mv = mv.where(mv.notna(), fill_mv)
    P['换手'] = to; P['市值亿'] = mv
    return P

if __name__ == '__main__':
    P = factor_table()
    print('rows', len(P), 'days', P['日'].min(), P['日'].max(), flush=True)
    P = enrich(P)
    P.to_pickle(OUT)
    print('saved', OUT, P.shape, 'E1有效', int(P['E1'].notna().sum()), 'GAP有效', int(P['GAP'].notna().sum()))
