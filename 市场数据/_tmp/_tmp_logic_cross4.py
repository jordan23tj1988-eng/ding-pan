import json, io, sys, os, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
def jl(p): return json.load(open(p, 'r', encoding='utf-8'))
def zt(d):
    s = {}
    p = os.path.join(B, d, 'zt_pool.csv')
    if not os.path.exists(p): return s
    with open(p, 'r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f): s[r['代码'].strip()] = r
    return s

raw = open(os.path.join(B, '产业链模板.json'), 'r', encoding='utf-8').read()
tpl = json.loads(raw)
# collect (chain, 环节, code, name)
recs = []
def walk(o, chain, seg):
    if isinstance(o, dict):
        for k, v in o.items():
            if chain is None: walk(v, k, None)
            else: walk(v, chain, k if seg is None else seg + '/' + k)
    elif isinstance(o, list):
        for v in o:
            if isinstance(v, list) and len(v) >= 2 and isinstance(v[0], str) and re.fullmatch(r'\d{6}', v[0]):
                recs.append((chain, seg, v[0], v[1]))
            elif isinstance(v, str) and re.fullmatch(r'\d{6}', v):
                recs.append((chain, seg, v, ''))
            else: walk(v, chain, seg)
walk(tpl, None, None)
print('模板条目', len(recs), '去重代码', len({r[2] for r in recs}))

R = jl(os.path.join(X, '中报预增雷达_20260826.json'))
A = {str(e['代码']).zfill(6): e for e in R['A共振池(重要度排序)']}
z26 = zt('20260826')
back = [r for r in recs if r[2] in A]
print()
print('=== 链内A档背书(模板票∩A共振池) n=%d ===' % len(back))
for chain, seg, c, n in back:
    e = A[c]
    print(' %-14s %-26s %s %-6s 变动%%%-8s r250=%-7s 近20日=%-6s 距高%%=%-7s %s'
          % (chain, seg, c, n or e.get('名称'), e.get('变动幅度%'), e.get('r250'),
             e.get('近20日涨幅%'), e.get('距250日高%'), '★今日涨停' if c in z26 else ''))
print('>>> 链内A档背书 ∩ 今日涨停 =', len([1 for r in back if r[2] in z26]))
print('>>> 模板全票(153) ∩ 今日涨停 =', sorted({r[2] for r in recs} & set(z26)))

print()
print('=== T-1预测式交叉: 前日A池 ∩ 次日涨停 ===')
pairs = [('20260821','20260824'),('20260824','20260825'),('20260825','20260826')]
for d0, d1 in pairs:
    R0 = jl(os.path.join(X, '中报预增雷达_%s.json' % d0))
    A0 = {str(e['代码']).zfill(6): e for e in R0['A共振池(重要度排序)']}
    z1 = zt(d1)
    it = sorted(set(A0) & set(z1))
    print(' %s A池%d -> %s涨停%d : 命中%d %s' % (d0, len(A0), d1, len(z1), len(it), it))
    for c in it:
        print('    ', c, z1[c].get('名称'), '连板', z1[c].get('连板数'), '| 变动%', A0[c].get('变动幅度%'),
              '| r250', A0[c].get('r250'), '| 主类', A0[c].get('主类'), '| 重要度', A0[c].get('重要度分'))

print()
print('=== 链条纵深库 keys ===')
S = jl(os.path.join(X, '链条纵深库.json'))
print(type(S), list(S.keys())[:30] if isinstance(S, dict) else len(S))
print(json.dumps(S, ensure_ascii=False)[:1200])
