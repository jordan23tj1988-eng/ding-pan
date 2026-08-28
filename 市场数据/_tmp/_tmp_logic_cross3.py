import json, io, sys, os, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
def jl(p):
    try:
        return json.load(open(p, 'r', encoding='utf-8'))
    except UnicodeDecodeError:
        print('   [warn] %s 非法utf-8字节, 用errors=replace降级读取' % os.path.basename(p))
        return json.loads(open(p, 'r', encoding='utf-8', errors='replace').read())
def ztset(d):
    s = {}
    p = os.path.join(B, d, 'zt_pool.csv')
    if not os.path.exists(p): return s
    with open(p, 'r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f): s[r['代码'].strip()] = r
    return s

print('=== 结构性检验: A池成员是否可能当日涨停 ===')
for d in ['20260820','20260821','20260824','20260825','20260826']:
    try:
        R = jl(os.path.join(X, '中报预增雷达_%s.json' % d))
    except Exception as e:
        print(' %s 雷达文件损坏不可解析(%s)=> null, 不参与结论' % (d, type(e).__name__))
        continue
    A = {str(e['代码']).zfill(6): e for e in R['A共振池(重要度排序)']}
    z = ztset(d)
    n5 = [c for c,e in A.items() if (e.get('近5日涨停') or 0) > 0]
    r20 = [c for c,e in A.items() if (e.get('近20日涨幅%') or 0) >= 15]
    print(' %s A池%d ∩当日涨停%d(%s) | A池内近5日涨停>0的只数=%d | 近20日涨幅>=15%%只数=%d'
          % (d, len(A), len(set(A)&set(z)), sorted(set(A)&set(z)), len(n5), len(r20)))

print()
print('=== 贵金属: 按题材归类 有色/贵金属类 (0825 候选 vs 0826涨停) ===')
z26 = ztset('20260826')
for d in ['20260825','20260826']:
    R = jl(os.path.join(X, '中报预增雷达_%s.json' % d))
    g = R['按题材归类'].get('有色/贵金属类')
    print(' --%s 有色/贵金属类 type=%s' % (d, type(g)))
    if isinstance(g, list):
        print('   n=', len(g))
        for e in g:
            c = str(e.get('代码')).zfill(6)
            print('   ', c, e.get('名称'), '变动%', e.get('变动幅度%'), '重要度', e.get('重要度分'),
                  'r250', e.get('r250'), '近20日', e.get('近20日涨幅%'),
                  '=> 0826涨停' if c in z26 else '')
    else:
        print(json.dumps(g, ensure_ascii=False)[:1500])
    print('   活跃线[有色/贵金属]=', json.dumps(R['活跃线'].get('有色/贵金属'), ensure_ascii=False)[:400])

print()
print('=== 按题材归类 全类目计数 (0826) + 各类∩涨停 ===')
R = jl(os.path.join(X, '中报预增雷达_20260826.json'))
for k, v in R['按题材归类'].items():
    if isinstance(v, list):
        cs = {str(e.get('代码')).zfill(6) for e in v}
        it = sorted(cs & set(z26))
        print(' %-22s n=%-4d ∩涨停=%d %s' % (k, len(v), len(it), it))
