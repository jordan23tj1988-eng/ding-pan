# -*- coding: utf-8 -*-
"""周训练手算聚合(20261023) —— scripts/weekly_training_run.py 缺失时的替代取证。
口径: 全部读留档结算文件, 不新增判断、不补数字。
周 = 20261019~20261023 (票日 1019-1022 已T+1结算; 票日1023 结算日20261026 未到,不计入)
"""
import json, os, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(BASE, '_学习')
DAYS = ['20261019', '20261020', '20261021', '20261022']
WEEK_END = '20261023'

FILES = {
    'auction': ('竞价池结算_%s.json', '执行胜率', '执行均收', '全场涨停均收'),
    'lhb':     ('席位荐票结算_%s.json', '执行胜率', '均收', None),
    'theme':   ('题材荐票结算_%s.json', '执行胜率', '执行均收', '全场涨停均收'),
    'logic':   ('逻辑荐票结算_%s.json', '执行胜率', '执行均收', '全场涨停均收'),
    'limitup': ('质量荐票结算_%s.json', '执行胜率', '执行均收', '全场均收'),
}
NAMES = {'auction': '第一路·竞价', 'lhb': '第二路·席位', 'theme': '第三路·题材',
         'logic': '第四路·产业逻辑', 'limitup': '第五路·涨停质量'}


def load(f):
    p = os.path.join(L, f)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception as e:
        print('!! load fail', f, e)
        return None


def parse_win(s):
    try:
        a, b = str(s).split('/')
        return int(a), int(b)
    except Exception:
        return None, None


# 每日全场基准(以质量路结算的全场均收为准, 供席位路补基准)
mkt = {}
for d in DAYS:
    x = load('质量荐票结算_%s.json' % d)
    if x:
        mkt[d] = (x.get('汇总') or {}).get('全场均收')

out = {
    '周': [DAYS[0], WEEK_END],
    '生成方式': '手算聚合(scripts/weekly_training_run.py 缺失; 训练底座体检/孵化区/miss 由本脚本另行读档生成, 未经训练脚本)',
    '口径': '票加权: 均收=∑(日均收×日票数)/∑票数; 全场基准按同日同票数加权; 增益=路均收-全场基准; 胜率=胜/可结算票数; 票日1023未结算不计入',
    '五路判断战绩': {}, '六账本周考核': {}, '训练底座体检': {}, '孵化区': {}, 'miss未消化': [], '缺口': [],
}

for route, (pat, wk, rk, bk) in FILES.items():
    rows = []
    for d in DAYS:
        x = load(pat % d)
        if not x:
            rows.append({'票日': d, '状态': 'missing'})
            continue
        s = x.get('汇总') or {}
        w, n = parse_win(s.get(wk))
        ret = s.get(rk)
        base = s.get(bk) if bk else None
        if base is None:
            base = mkt.get(d)
        rows.append({'票日': d, '结算日': x.get('结算日') or x.get('池日') and x.get('结算日'),
                     '胜': w, '票数': n, '均收pct': ret, '全场基准pct': base,
                     '日增益pp': (round(ret - base, 2) if (ret is not None and base is not None) else None)})
    tot_n = sum(r['票数'] for r in rows if r.get('票数'))
    tot_w = sum(r['胜'] for r in rows if r.get('胜') is not None)
    num = sum(r['均收pct'] * r['票数'] for r in rows if r.get('均收pct') is not None and r.get('票数'))
    bnum = sum(r['全场基准pct'] * r['票数'] for r in rows if r.get('全场基准pct') is not None and r.get('票数'))
    bn = sum(r['票数'] for r in rows if r.get('全场基准pct') is not None and r.get('票数'))
    avg = round(num / tot_n, 2) if tot_n else None
    bavg = round(bnum / bn, 2) if bn else None
    zero_days = [r['票日'] for r in rows if r.get('票数') == 0]
    zero_ok = [r['票日'] for r in rows if r.get('票数') == 0 and (r.get('全场基准pct') or 0) < 0]
    out['五路判断战绩'][route] = {
        '路': NAMES[route], '逐日': rows, '票数': tot_n, '胜数': tot_w,
        '胜率pct': round(tot_w / tot_n * 100, 1) if tot_n else None,
        '均收pct': avg, '全场基准pct': bavg,
        '选股增益pp': round(avg - bavg, 2) if (avg is not None and bavg is not None) else None,
        '零票日': zero_days,
        '空仓正确率': ('%d/%d' % (len(zero_ok), len(zero_days))) if zero_days else None,
    }

# ---- 六账本周考核(引擎实跑产物) ----
wk = None
p = os.path.join(L, '_模拟盘', '周考核_%s.json' % WEEK_END)
if os.path.exists(p):
    wk = json.load(open(p, encoding='utf-8'))
    out['六账本周考核'] = {
        '源': '_模拟盘/周考核_%s.json (模拟盘引擎.py weekly 实跑)' % WEEK_END,
        '基准周收益pct': wk.get('基准周收益pct'),
        'agents': wk.get('agents'), '路内池基准': wk.get('路内池基准'),
        '卖腿反事实': wk.get('卖腿反事实'), '账本统计': wk.get('账本统计'),
    }
else:
    out['缺口'].append('六账本周考核缺失: 周考核_%s.json 不存在' % WEEK_END)

# ---- 训练底座体检 ----
def _jload(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

def _norm(x):
    s = str(x or '')
    s = s.replace('-', '').replace(' ', '')[:8]
    return s

libs = []
spec = [('涨停质量库', '_涨停质量库.json'), ('席位分档', '_席位分档.json'),
        ('竞价池分桶库', '_竞价池分桶库.json'), ('市场温度表', '_市场温度表.json')]
for name, fn in spec:
    fp = os.path.join(L, fn)
    if not os.path.exists(fp):
        libs.append({'库': name, '状态': 'missing'}); continue
    d = _jload(fp)
    if name == '市场温度表':
        ks = sorted(k for k in (d or {}) if str(k).isdigit())
        last = ks[-1] if ks else None
        upd = last
        window = (ks[0] + '~' + last) if ks else None
    else:
        upd = _norm((d or {}).get('更新'))
        window = (d or {}).get('窗口')
        last = _norm(str(window).split('~')[-1]) if window else upd
    # 判定: 数据末日期 < 上一交易日(20261022) 才算停更; =上一交易日属设计滞后(T+1前向未到,如席位分档只用有前向的笔)
    prev_td = '20261022'
    stale = (last is None) or (last < prev_td)
    libs.append({'库': name, '更新': upd, '窗口': window, '数据末日期': last,
                 '文件mtime': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(fp))),
                 '是否落后本周五': stale,
                 '滞后性质': ('停更·须补跑' if stale else
                            ('设计滞后(末=上一交易日,当日笔无T+1前向不入样本)' if last == prev_td else '新鲜(含本周五)'))})
out['训练底座体检'] = {'本周五': WEEK_END, '库': libs,
                  '停更项': [x['库'] for x in libs if x.get('是否落后本周五')]}

# ---- 孵化区 ----
inc = _jload(os.path.join(L, '孵化区.json')) or {}
act_status = ('孵化中', '在研', '探索')
inc_out = {'按路': {}, '在研': [], '超期搁置': [], '已结案': []}
for route, items in inc.items():
    c = {'总': len(items), '在研': 0, '搁置': 0, '已结案': 0}
    for it in items:
        st = str(it.get('状态'))
        dl = str(it.get('截止') or '')
        row = {'路': route, 'id': it.get('id'), '题': it.get('题'), '状态': st, '截止': it.get('截止')}
        if any(k in st for k in act_status):
            c['在研'] += 1; inc_out['在研'].append(row)
        elif '固化成脚本' in st or '已证伪' in st or '毕业' in st:
            c['已结案'] += 1; inc_out['已结案'].append(row)
        else:
            c['搁置'] += 1
            if dl.isdigit() and dl < WEEK_END:
                inc_out['超期搁置'].append(row)
    inc_out['按路'][route] = c
out['孵化区'] = inc_out

# ---- miss(错过机会) ----
mis = os.path.join(L, '错过机会.jsonl')
if os.path.exists(mis):
    for line in open(mis, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        d = str(r.get('日期') or r.get('d') or '')
        dn = _norm(d)
        r['_记录日'] = dn
        r['_状态'] = '未消化(无消化记录字段, 档案仅有本条)'
        out['miss未消化'].append(r)

json.dump(out, open(os.path.join(L, '_周训练手算_%s.json' % WEEK_END), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ('五路判断战绩',)}, ensure_ascii=False)[:1200])
for r, v in out['五路判断战绩'].items():
    print(r, v['路'], 'n=%s' % v['票数'], '胜率%s' % v['胜率pct'], '均收%s' % v['均收pct'],
          '基准%s' % v['全场基准pct'], '增益%s' % v['选股增益pp'], '空仓%s' % v['空仓正确率'])
print('底座停更:', out['训练底座体检']['停更项'])
print('孵化 在研/超期:', len(out['孵化区']['在研']), len(out['孵化区']['超期搁置']))
print('miss:', len(out['miss未消化']))
print('-> _学习/_周训练手算_%s.json' % WEEK_END)
