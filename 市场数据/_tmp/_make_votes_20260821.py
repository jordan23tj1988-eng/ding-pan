# -*- coding: utf-8 -*-
"""一次性: 从五路判断提炼周期投票文件(20260821)。evidence 全部来自各路判断原文提炼, 零编造。"""
import json, io, os
L = r'D:\股票数据\市场数据\_学习'

# 各路的 stage/direction 从判断结论提炼(独立核实)
# 证据从判断 json 的 结论/一句话 摘取, 加后缀说明
votes = {
    'auction': {
        'stage': '冰点', 'direction': '平',
        'evidence': '竞价路C档防守空仓:温度23.4冰点再探(昨29.4修复一日游回落)+涨停54收缩+量能18793亿跌破2万亿+竞价池0820执行胜率9/26=34.6%<50%全池负期望;评分半区反转(高分深套),空仓等修复或温度≥40',
        'confidence': 57,
    },
    'lhb': {
        'stage': '冰点', 'direction': '平',
        'evidence': '席位路C档防守空仓:冰点边缘二次探底(29.4→23.4/涨停79→54/最高板4→3/成交缩至18793亿)+资金温度15分位冷(机构23席11.1亿未放量,仅游资108席27.9亿捡筹)+医药主线高位退潮(昨26只→今5只,誉衡净买TOP1→净卖TOP1);S档银河学院南n=31扎实但冰点不主动开仓',
        'confidence': 60,
    },
    'theme': {
        'stage': '冰点', 'direction': '平',
        'evidence': '题材路C档防守空仓:冰点深化(23.4,-6下探)+涨停54回落+米开主线判定零达标(医药宽度37→7陷阱兑现、通信设备6只新候选线未确认);汉森制药3板孤高标无宽度支撑,0荐3观察带闸门',
        'confidence': 65,
    },
    'logic': {
        'stage': '冰点', 'direction': '平',
        'evidence': '产业逻辑路C档防守空仓:业绩线连续第8日零共振(A池115∩涨停54=0)+温度23.4冰点情绪修复中断+刚点火业绩票3只涨停(星网锐捷/士兰微/水发燃气)末端首次点火未扩散;本路战绩3/14=21.4%负期望从严空仓',
        'confidence': 66,
    },
    'limitup': {
        'stage': '冰点', 'direction': '平',
        'evidence': '质量路C档防守空仓:全池负期望第5日(54只执1胜率max45.8%无一>50%)+量能18793亿跌破2万亿地板+温度23.4再入冰点+医药立出3板(汉森)但仅7家收缩不足;农业主线虚胖第5次坐实(金健米业断板),缩量退潮中的局部修复不进攻',
        'confidence': 84,
    },
}
for r, v in votes.items():
    p = os.path.join(L, f'周期投票_{r}_20260821.json')
    obj = {'d': '20260821', 'route': r, 'stage': v['stage'], 'direction': v['direction'],
           'evidence': v['evidence'], 'confidence': v['confidence']}
    io.open(p, 'w', encoding='utf-8', newline='').write(json.dumps(obj, ensure_ascii=False))
    print('写', p)
print('5 个投票文件完成')
