import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

R = r'D:\股票数据\市场数据'
d = json.load(open(R + r'\_学习\涨停对链条_20261104.json', encoding='utf-8'))
print('日期', d.get('日期'), '涨停总数', d.get('涨停总数'), '题材线数', d.get('题材线数'))
for line in d['题材线']:
    print('--', line['大方向'], '家数', line['家数'], '最高连板', line.get('最高连板'),
          '承载环节', line.get('承载环节'), '开板占比', line.get('开板占比'))
    print('   画像:', line.get('强度画像'))
    for env in line.get('环节', []):
        print('   [环节]', env['环节'], '家数', env['家数'], '最高', env.get('最高连板'), '快判', env.get('快判'))
        for s in env.get('个股', []):
            print('      ', s['代码'], s['名称'], '连板', s.get('连板'), '首封', s.get('首封'),
                  '开板', s.get('开板次数'), '封单比', s.get('封单比'), '档', s.get('来源档'), '|', s.get('催化'))
