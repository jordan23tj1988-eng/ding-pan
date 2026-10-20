# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def rd(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)
B = 'D:/股票数据/市场数据/_学习/'
print("===== 昨日 logic判断_20261015 =====")
print(json.dumps(rd(B+'logic判断_20261015.json'), ensure_ascii=False, indent=1)[:9000])
print("\n===== 模拟盘 state 状态.json =====")
print(json.dumps(rd(B+'_模拟盘/logic/状态.json'), ensure_ascii=False, indent=1)[:4000])
print("\n===== state.json =====")
print(json.dumps(rd(B+'_模拟盘/logic/state.json'), ensure_ascii=False, indent=1)[:4000])
