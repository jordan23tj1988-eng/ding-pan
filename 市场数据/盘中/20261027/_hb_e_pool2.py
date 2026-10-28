# -*- coding: utf-8 -*-
"""hb-e 补探：东财 ZT/ZB 池明细（行业、连板、首封时间、炸板次数），供持仓题材核对。只读。"""
import json, urllib.request, os, datetime

D = os.path.dirname(os.path.abspath(__file__))


def http_get(url, timeout=12):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
        'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'ignore')


def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    j = json.loads(http_get(url))
    return (j.get('data') or {}).get('pool') or []


def fmt_t(v):
    s = str(v).zfill(6)
    return f'{s[:2]}:{s[2:4]}:{s[4:]}'


today = datetime.datetime.now().strftime('%Y%m%d')
now = datetime.datetime.now().strftime('%H:%M:%S')
zt = em_pool('zt', today)
zb = em_pool('zb', today)


def brief(r):
    return {'code': str(r.get('c')).zfill(6), 'name': r.get('n'), 'ind': r.get('hybk'),
            'lbc': r.get('lbc'), 'fbt': fmt_t(r.get('fbt')) if r.get('fbt') else None,
            'lbt': fmt_t(r.get('lbt')) if r.get('lbt') else None,
            'zbc': r.get('zbc'), 'pct': r.get('zdp'), 'amt_yi': round((r.get('amount') or 0)/1e8, 2),
            'fund_yi': round((r.get('fund') or 0)/1e8, 2)}


ztl = [brief(r) for r in zt]
zbl = [brief(r) for r in zb]
ind_zt, ind_zb = {}, {}
for x in ztl:
    ind_zt[x['ind']] = ind_zt.get(x['ind'], 0) + 1
for x in zbl:
    ind_zb[x['ind']] = ind_zb.get(x['ind'], 0) + 1

motor = [x for x in ztl if x['ind'] == '电机Ⅱ']
autop = [x for x in ztl if x['ind'] == '汽车零部']
autop_zb = [x for x in zbl if x['ind'] == '汽车零部']

out = {'ts': now, 'zt_n': len(ztl), 'zb_n': len(zbl),
       'ind_zt_top': sorted(ind_zt.items(), key=lambda x: -x[1])[:8],
       'ind_zb_top': sorted(ind_zb.items(), key=lambda x: -x[1])[:8],
       'motor_zt': motor, 'autop_zt': autop, 'autop_zb': autop_zb,
       'zb_all': zbl,
       'lb_ge3': [x for x in ztl if (x['lbc'] or 1) >= 3]}
json.dump(out, open(os.path.join(D, '_hb_e_pool2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ['ts', 'zt_n', 'zb_n', 'ind_zt_top', 'ind_zb_top',
                                      'motor_zt', 'autop_zt', 'autop_zb', 'lb_ge3']},
                 ensure_ascii=False, indent=1))
