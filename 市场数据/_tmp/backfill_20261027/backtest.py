import json, collections

L = '_学习/'
t = json.load(open(L + '_市场温度表.json', encoding='utf-8'))
lead = json.load(open(L + '_情绪先行指标.json', encoding='utf-8'))
days = sorted(t)
cur = '20261027'
hist = [d for d in days if d < cur]


def dir_of(a, b):
    dt = b['温度'] - a['温度']
    return '升' if dt > 2 else ('降' if dt < -2 else '平')


def regime(mode):
    out = []
    for i in range(1, len(hist)):
        p, d = t[hist[i - 1]], t[hist[i]]
        if d.get('温度') is None or p.get('温度') is None:
            continue
        if mode == 'ice':
            ok = d['温度'] < 25
        elif mode == 'deep':
            ok = (d['温度'] < 30 and (d.get('跌停数') or 0) >= 20
                  and p.get('涨停数') and (d.get('涨停数') or 0)
                  and (d['涨停数'] - p['涨停数']) / p['涨停数'] <= -0.25)
        nxt = t[days[days.index(hist[i]) + 1]] if days.index(hist[i]) + 1 < len(days) else None
        if ok and nxt and nxt['日'] <= cur:
            out.append((d['日'], dir_of(d, nxt), nxt['温度'] - d['温度']))
    return out


for m in ('ice', 'deep'):
    o = regime(m)
    c = collections.Counter(x[1] for x in o)
    print(m, 'n=', len(o), dict(c), '温度回升', sum(1 for x in o if x[2] > 0),
          '均值Δ%.2f' % (sum(x[2] for x in o) / len(o) if o else 0))
    print('   样本:', [x[0] for x in o])

# 1027 当日三腿
p, d = t['20261026'], t['20261027']
dt = d['温度'] - p['温度']
d1 = lead['20261027']['晋级']['一进二率'] - lead['20261026']['晋级']['一进二率']
dp = lead['20261027']['昨日涨停溢价']['执行均收'] - lead['20261026']['昨日涨停溢价']['执行均收']
legs = ['升' if dt > 2 else ('降' if dt < -2 else '平'),
        '升' if d1 > 0.03 else ('降' if d1 < -0.03 else '平'),
        '升' if dp > 0.5 else ('降' if dp < -0.5 else '平')]
print('\n1027三腿: 温度Δ%+.1f→%s 一进二Δ%+.3f→%s 溢价Δ%+.2f→%s' % (dt, legs[0], d1, legs[1], dp, legs[2]))
print('裁判多数:', collections.Counter(legs).most_common(1)[0] if collections.Counter(legs).most_common(1)[0][1] >= 2 else '无多数→平')
print('lead1027:', json.dumps(lead['20261027'], ensure_ascii=False)[:400])
print('lead1026 一进二:', lead['20261026']['晋级'])
acc = json.load(open(L + '_周期投票准确率.json', encoding='utf-8'))
print('\n准确率台账:', json.dumps(acc, ensure_ascii=False))
