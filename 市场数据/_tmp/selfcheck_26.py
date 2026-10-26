# -*- coding: utf-8 -*-
import json, os, sys, csv
B = r'D:\股票数据\市场数据'
d8 = '20261026'
d = json.load(open(os.path.join(B, '_学习', f'推演_{d8}.json'), encoding='utf-8'))
errs = []
def ck(c, m):
    if not c: errs.append(m)

WL = {'温度','温度档','涨停数','跌停数','炸板率','最高连板','最高板','二板加','两市成交额_亿',
      '涨停家数_净','一进二率','二进三率','高度晋级率','昨停溢价','核按钮率','温度变化','代码封板','代码收红'}
DIR = {'升','降','>=','>','<','<=','=='}
preds = d['次日可证伪预测']
ck(d['日期'] == d8, '日期')
ck('推演推理员' in d['来源'], '来源')
for k in ('情绪几度','明日攻防','主线站队','龙头接力','竞价强弱预判'):
    ck(isinstance(d.get(k), str) and len(d[k]) > 20, '字段 '+k)
summ = json.load(open(os.path.join(B, d8, 'summary.json'), encoding='utf-8'))
temp = json.load(open(os.path.join(B, '_学习','_市场温度表.json'), encoding='utf-8'))[d8]
lead = json.load(open(os.path.join(B, '_学习','_情绪先行指标.json'), encoding='utf-8'))[d8]['晋级']
facts = {'涨停数': summ['涨停家数'], '跌停数': summ['跌停家数'], '炸板率': summ['炸板率'],
         '最高连板': summ['最高连板'], '两市成交额_亿': summ['两市成交额_亿'],
         '温度': temp['温度'], '一进二率': lead['一进二率'], '二进三率': lead['二进三率'],
         '高度晋级率': lead['高度晋级率']}
codes = {str(r['代码']).zfill(6) for r in csv.DictReader(open(os.path.join(B, d8,'zt_pool.csv'), encoding='utf-8-sig'))}
for i, p in enumerate(preds):
    c = p.get('判定条件') or {}
    ck(c.get('指标') in WL, f'P{i} 指标越界 {c.get("指标")}')
    ck(c.get('方向') in DIR, f'P{i} 方向越界 {c.get("方向")}')
    ck(isinstance(c.get('>='), (int,float)), f'P{i} 阈值非数值')
    if c.get('指标') in ('代码封板','代码收红'):
        ck(isinstance(c.get('代码'), str) and len(c['代码']) == 6, f'P{i} 代码字段')
        ck(c.get('代码') in codes, f'P{i} 代码不在当日涨停池')
    if c.get('指标') in facts and c.get('方向') in ('升','降'):
        ck(c['>='] == facts[c['指标']], f'P{i} 锚值 {c[">="]} != 真源 {facts[c["指标"]]}')
print('预测条数=%d' % len(preds))
print('锚值比对: ' + ', '.join(f'{k}={v}' for k,v in facts.items()))
sys.path.insert(0, B)
import review_learning as rl
from pathlib import Path
parsed = rl._prediction_rows(Path(B), d8)
machine = [r for r in parsed if r.get('field') and r.get('op') and r.get('threshold') is not None]
print('生产解析器 parsed=%d machine=%d coverage=%.1f%%' % (len(parsed), len(machine), 100*len(machine)/len(parsed)))
for r in parsed:
    if not (r.get('field') and r.get('op') and r.get('threshold') is not None):
        print('  [narrative] %s field=%s' % (str(r.get('claim'))[:24], r.get('field')))
print('ops: ' + ' | '.join(f"{r['field']}/{r['op']}/{r['threshold']}" for r in machine))
ck(len(machine) >= 12, 'machine<12')
ck(len(machine)/len(parsed) >= 0.70, 'coverage<70%')
# 交易计划
mp = json.load(open(os.path.join(B, '_学习','交易计划_master_20261026.json'), encoding='utf-8')) if os.path.exists(os.path.join(B,'_学习','交易计划_master_20261026.json')) else None
if mp:
    st = json.load(open(os.path.join(B, '_学习','_模拟盘','master','状态.json'), encoding='utf-8'))
    hold = [(h['code'], h.get('buy_px'), h.get('shares')) for h in st['持仓']]
    sell = [s['代码'] for s in mp['sells']]
    print('持仓=%d 卖单=%d' % (len(hold), len(sell)))
    for h in hold:
        ck(h[0] in sell, f'漏票 {h[0]}')
    w = sum(b['权重%'] for b in mp['buys'])
    print('buys=%d 权重合计=%.2f 单票max=%.2f' % (len(mp['buys']), w, max([b['权重%'] for b in mp['buys']] or [0])))
    ck(w <= 2.0 + 1e-9, '权重合计>2.0')
    ck(all(b['权重%'] <= 1.0 for b in mp['buys']), '单票>1.0')
    ck(mp['日期'] == d8, '计划日期')
print('FAILS: %s' % (errs if errs else 'none'))
