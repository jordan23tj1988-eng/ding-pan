# -*- coding: utf-8 -*-
import json, io, os
base = r'D:\股票数据\市场数据\_学习'
t = json.load(io.open(os.path.join(base, '_市场温度表.json'), encoding='utf-8'))
# 收集有温度的行(排除null温度的历史ths回填), 按日期排序
rows = []
for k, v in t.items():
    zt = v.get('涨停数'); zb = v.get('炸板数'); dt = v.get('跌停数')
    if zt is None or zb is None:
        continue
    fbl = zt / (zt + zb) if (zt + zb) > 0 else None
    zbl = zb / (zt + zb) if (zt + zb) > 0 else None
    rows.append((k, zt, zb, dt, fbl, zbl, v.get('温度'), v.get('温度档'), v.get('最高板'), v.get('梯队')))
rows.sort(key=lambda r: r[0])
# 找同类日: 封板率>=0.80 且 炸板率<0.15 且 跌停<=1 (0817: 89.8%/10.2%/跌停1)
print('=== 历史同类日(封板率>=80% 且 炸板率<15% 且 跌停<=1) ===')
cand = []
for i, r in enumerate(rows):
    k, zt, zb, dt, fbl, zbl, wd, wdd, gb, td = r
    if fbl >= 0.80 and zbl < 0.15 and (dt is None or dt <= 1):
        cand.append(i)
        print('同类日', k, '涨停', zt, '炸板', zb, '封板率%.1f%%' % (fbl*100), '炸板率%.1f%%' % (zbl*100), '跌停', dt, '温度', wd, '最高板', gb)
print()
print('=== 同类日次日变化(分化统计) ===')
for i in cand:
    if i + 1 >= len(rows):
        print(rows[i][0], '-> 无次日数据')
        continue
    r0 = rows[i]; r1 = rows[i+1]
    k0, zt0, zb0, dt0, fbl0, zbl0 = r0[0], r0[1], r0[2], r0[3], r0[4], r0[5]
    k1, zt1, zb1, dt1, fbl1, zbl1 = r1[0], r1[1], r1[2], r1[3], r1[4], r1[5]
    print('%s -> %s: 涨停 %d->%d (%+d), 封板率 %.1f%%->%.1f%%, 炸板率 %.1f%%->%.1f%%, 跌停 %s->%s, 温度 %s->%s' % (
        k0, k1, zt0, zt1, zt1-zt0, fbl0*100, fbl1*100, zbl0*100, zbl1*100, dt0, dt1, r0[6], r1[6]))
