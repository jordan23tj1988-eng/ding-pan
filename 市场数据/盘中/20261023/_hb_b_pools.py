# -*- coding: utf-8 -*-
"""hb-b 场：东财 ZT/ZB/DT 池（DT 用 sort=zdp:asc 才能拿到行；tc=总家数）。"""
import json, urllib.request, datetime, os, sys

D = os.path.dirname(os.path.abspath(__file__))
UT = '7eea3edcaed734bea9cbfc24409ed989'

def pool(base, sort):
    u = (f'http://push2ex.eastmoney.com/{base}?ut={UT}&dpt=wz.ztzt&Pageindex=0'
         f'&pagesize=300&sort={sort}&date=20261023')
    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0',
                                             'Referer': 'http://quote.eastmoney.com/'})
    js = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8', 'ignore'))
    d = js.get('data') or {}
    return {'tc': d.get('tc'), 'qdate': d.get('qdate'), 'rows': d.get('pool') or []}

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'final'
    out = {'fetched': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    out['zt'] = pool('getTopicZTPool', 'fbt:asc')
    out['zb'] = pool('getTopicZBPool', 'fbt:asc')
    out['dt'] = pool('getTopicDTPool', 'zdp:asc')
    json.dump(out, open(os.path.join(D, f'_hb_b_pools_{tag}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    zt, zb, dt = out['zt'], out['zb'], out['dt']
    print('fetched', out['fetched'])
    print('ZT tc', zt['tc'], 'rows', len(zt['rows']))
    print('ZB tc', zb['tc'], 'rows', len(zb['rows']))
    print('DT tc', dt['tc'], 'rows', len(dt['rows']))
    lb = {}
    for r in zt['rows']:
        lb[r.get('lbc')] = lb.get(r.get('lbc'), 0) + 1
    print('连板分布', dict(sorted(lb.items())))
    print('炸板率', round(len(zb['rows']) / (len(zt['rows']) + len(zb['rows'])), 4))
    print('ZT names', [(r['n'], r.get('lbc'), round(r.get('zdp', 0), 2), r.get('hybk')) for r in zt['rows']])
    print('DT first5', [(r['n'], round(r.get('zdp', 0), 2)) for r in dt['rows'][:5]])
