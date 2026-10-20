# -*- coding: utf-8 -*-
import json

B = "D:/股票数据/市场数据"
c = json.load(open(f"{B}/_学习/涨停对链条_20261020.json", encoding='utf-8'))
print("线数", c['题材线数'])
for L in sorted(c['题材线'], key=lambda x: -x['家数']):
    print("%-14s 家%-3d 最高%d 早封%.2f 开板%.2f | %s" % (
        L['大方向'], L['家数'], L['最高连板'], L.get('早封占比', 0), L.get('开板占比', 0), L.get('强度画像', '')[:70]))

q = json.load(open(f"{B}/_学习/涨停质量荐票_20261020.json", encoding='utf-8'))
det = {x['代码']: x for x in q['明细']}
for k in ("002929", "003029", "603893", "603236", "600293", "600178", "600148", "002724", "300244", "001283"):
    x = det[k]
    print(json.dumps(x, ensure_ascii=False))

lib = json.load(open(f"{B}/_学习/_涨停质量库.json", encoding='utf-8'))
print("库keys:", list(lib.keys()))
print("样本", lib.get('样本'), "窗口", lib.get('窗口'), "生成", lib.get('生成日') or lib.get('日期'))
print("活跃因子", lib.get('活跃因子'))
f = lib.get('因子')
if isinstance(f, dict):
    for name, v in list(f.items()):
        if isinstance(v, dict):
            print("  F %-10s 状态=%s 区分度=%s ICt=%s 权重=%s" % (name, v.get('状态'), v.get('区分度'), v.get('IC_t'), v.get('权重')))
for k in ('分板胜率', '环境规则', '规则榜'):
    print(k, json.dumps(lib.get(k), ensure_ascii=False)[:1200])
