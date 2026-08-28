import json, io, sys, os, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
D = '20260826'
def jl(p): return json.load(open(p, 'r', encoding='utf-8'))

zt = {}
with open(os.path.join(B, D, 'zt_pool.csv'), 'r', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        zt[r['代码'].strip()] = r
ztset = set(zt)

R = jl(os.path.join(X, '中报预增雷达_%s.json' % D))
R25 = jl(os.path.join(X, '中报预增雷达_20260825.json'))
print('=== 统计 20260826 ===')
print(json.dumps(R['统计'], ensure_ascii=False, indent=1))
print('=== 统计 20260825 ===')
print(json.dumps(R25['统计'], ensure_ascii=False, indent=1))

def codes(lst):
    out = {}
    for e in lst:
        c = str(e.get('代码') or e.get('code') or '').zfill(6)
        out[c] = e
    return out

A = codes(R['A共振池(重要度排序)'])
A25 = codes(R25['A共振池(重要度排序)'])
print()
print('A池 20260826 n=%d ; 20260825 n=%d ; 净变 %+d' % (len(A), len(A25), len(A)-len(A25)))
print('A池样本字段:', json.dumps(R['A共振池(重要度排序)'][0], ensure_ascii=False))
inter = sorted(set(A) & ztset)
print('>>> A池 ∩ 涨停 =', len(inter), inter)
for c in inter:
    print('   ', c, A[c].get('名称'), '| 涨停连板', zt[c].get('连板数'), '| A池:', json.dumps(A[c], ensure_ascii=False)[:400])

# 概念叠加候选/刚点火/纯预增 ∩ 涨停
for k in ['概念叠加候选', '纯预增未叠加', '刚点火(有涨停未透支)', '预期已兑现(年内已翻倍,不入候选)', '已发酵对照Top12']:
    cm = codes(R[k]); it = sorted(set(cm) & ztset)
    print('%s n=%d ∩涨停=%d %s' % (k, len(cm), len(it), it))
    for c in it:
        print('     ', c, cm[c].get('名称'), '连板', zt[c].get('连板数'), json.dumps(cm[c], ensure_ascii=False)[:260])

# 昨日刚点火 -> 今日
gd25 = codes(R25['刚点火(有涨停未透支)'])
print()
print('昨日(0825)刚点火 n=%d ∩ 今日涨停 = %s' % (len(gd25), sorted(set(gd25) & ztset)))
for c in gd25: print('   昨刚点火', c, gd25[c].get('名称'), '今涨停' if c in ztset else '')
# 昨日A池 ∩ 今日涨停
print('昨日A池 ∩ 今日涨停 =', len(set(A25) & ztset), sorted(set(A25) & ztset))

json.dump({'A': list(A), 'A25': list(A25)}, open(os.path.join(B, '_tmp_logic_A.json'), 'w', encoding='utf-8'))
