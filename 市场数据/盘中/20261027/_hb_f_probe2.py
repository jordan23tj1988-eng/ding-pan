# -*- coding: utf-8 -*-
"""hb-f 补充探针：东财 zb 池明细 ∩ 昨涨停池；封单/换手；今日入账对账。只读。"""
import json, urllib.request, datetime, os

D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(D, '..', '..'))
DEC = datetime.datetime.now().replace(microsecond=0)


def http_get(url, timeout=12, gbk=False):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
        'Referer': 'http://quote.eastmoney.com/'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode('gbk', 'ignore') if gbk else raw.decode('utf-8', 'ignore')


def em_pool(kind, date):
    base = {'zt': 'getTopicZTPool', 'zb': 'getTopicZBPool', 'dt': 'getTopicDTPool'}[kind]
    url = (f'http://push2ex.eastmoney.com/{base}?ut=7eea3edcaed734bea9cbfc24409ed989'
           f'&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt:asc&date={date}')
    j = json.loads(http_get(url))
    return (j.get('data') or {}).get('pool') or []


today = DEC.strftime('%Y%m%d')

# 昨日池（帧文件 pool_date=20261026）
frames = [json.loads(l) for l in open(os.path.join(D, 'realtime_ticks.jsonl'), encoding='utf-8') if l.strip()]
frames = [f for f in frames if f.get('rows')]
last = frames[-1]
prev_pool = {str(r['code']): r for r in last['rows']}

zt = em_pool('zt', today)
zb = em_pool('zb', today)
dt = em_pool('dt', today)

zt_c = {str(r.get('c')) for r in zt}
zb_c = {str(r.get('c')) for r in zb}
dt_c = {str(r.get('c')) for r in dt}

out = {'probe_ts': DEC.strftime('%Y-%m-%d %H:%M:%S'),
       'zt_n': len(zt), 'zb_n': len(zb), 'dt_n': len(dt),
       'prev_pool_overlap': {
           '还涨停': sorted([(c, prev_pool[c]['name']) for c in (zt_c & set(prev_pool))]),
           '已炸板': sorted([(c, prev_pool[c]['name']) for c in (zb_c & set(prev_pool))]),
           '跌停': sorted([(c, prev_pool[c]['name']) for c in (dt_c & set(prev_pool))]),
       },
       'zb_detail': sorted([{'c': str(r.get('c')), 'n': r.get('n'), 'p': r.get('p'),
                             'zbc': r.get('zbc'), 'hy': r.get('hybk')} for r in zb],
                           key=lambda x: -x['zbc'])[:30],
       'zt_fengdan': sorted([{'c': str(r.get('c')), 'n': r.get('n'), 'lbc': r.get('lbc'),
                              'fd': r.get('fund'), 'hy': r.get('hybk'), 'zbc': r.get('zbc'),
                              'hs': r.get('hs'), 'fbt': r.get('fbt'), 'lbt': r.get('lbt')} for r in zt],
                            key=lambda x: -(x['lbc'] or 0))[:12]}

# 今日入账对账
rows = []
for f in sorted(os.listdir(D)):
    if f.startswith('入账_') and f.endswith('.json'):
        j = json.load(open(os.path.join(D, f), encoding='utf-8'))
        rows.append({'file': f, 'session': j.get('session'),
                     'write_ts': j.get('write_ts'),
                     'before': j.get('入账前'), 'after': j.get('入账后'),
                     'action': j.get('入账动作')})
out['today_ruzhang'] = rows

# playbook / warboard 存在性
out['exist'] = {k: os.path.exists(os.path.join(D, k)) for k in
                ['pulse.json', 'warboard.json', '执行流水.jsonl', '报警_20261027.jsonl', 'playbook.json']}
out['playbook_root'] = os.path.exists(os.path.join(ROOT, 'playbook.json'))

json.dump(out, open(os.path.join(D, '_hb_f_probe2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
