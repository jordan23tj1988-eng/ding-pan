# -*- coding: utf-8 -*-
"""生成今日五路周期投票 + 周期主判(基于五路判断实际结论, 零编造)"""
import json, os
L = r'D:\股票数据\市场数据\_学习'
d = '20260902'

votes = {
    'auction':   dict(route='auction',   stage='退潮', direction='降', confidence=78, evidence='竞价温度63.1→30.5单日暴跌-32.6(中档→偏冷),回暖追池套(0901池结算-1.48%),退潮第2日'),
    'lhb':       dict(route='lhb',       stage='退潮', direction='降', confidence=75, evidence='资金温度3分位极冷(单日脉冲第4次),机构27席/游资147席无主线承接,S/A出手21笔但无共振'),
    'theme':     dict(route='theme',     stage='退潮', direction='降', confidence=76, evidence='无主线第7日,低切承接线(农业8→2/消费6→3/传媒11→3)全缩圈,算力/液冷首日爆量分歧未立'),
    'logic':     dict(route='logic',     stage='退潮', direction='降', confidence=74, evidence='业绩腿静默第5次坐实,T-1交叉(A池∩涨停)首次归零(0只),存储环节0涨停'),
    'limitup':   dict(route='limitup',   stage='退潮', direction='降', confidence=79, evidence='全池负期望第13日(执1max45.4%<50%),涨停83→52,最高板7→4断层,封板率跌破80%'),
}
for r, v in votes.items():
    v['d'] = d
    json.dump(v, open(os.path.join(L, f'周期投票_{r}_{d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

zhupan = dict(d=d, stage='退潮', direction='降',
              evidence='温度63.1→30.5暴跌32.6点,涨停83→52,跌停0→8,炸板率6.7%→22.4%,最高板7→4断层,量能跌破2万亿;五维退潮共振,昨日回暖证伪为一日脉冲,退潮第2日')
json.dump(zhupan, open(os.path.join(L, f'周期主判_{d}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已写五路周期投票 + 主判 (全部方向=降/退潮)')
