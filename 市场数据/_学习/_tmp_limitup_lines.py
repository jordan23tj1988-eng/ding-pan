# -*- coding: utf-8 -*-
import json, io, os
base = r'D:\股票数据\市场数据\_学习'
lz = json.load(io.open(os.path.join(base, '涨停对链条_20260818.json'), encoding='utf-8'))
print('涨停总数', lz['涨停总数'], '题材线数', lz['题材线数'])
lines = sorted(lz['题材线'], key=lambda x: -x['家数'])
for L in lines:
    print('%-16s 家数%-3d 最高%-2d板 早封%.2f 开板%.2f | %s' % (
        L['大方向'], L['家数'], L['最高连板'], L.get('早封占比', 0), L['开板占比'], L['承载环节']))
# 待归位
print('待归位(行业兜底)数:', len(lz.get('待归位_行业兜底', [])))
