import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
R = r'D:\股票数据\市场数据'
raw = open(R + r'\_学习\中报预增雷达_20261104.json', 'rb').read()
s = raw.decode('utf-8', errors='replace')
obj = None
try:
    obj, idx = json.JSONDecoder().raw_decode(s)
    print('raw_decode OK end=', idx, 'len', len(s))
except Exception as e:
    print('raw_decode FAIL', e)
if obj:
    print('top keys:', list(obj.keys()))
    print('统计:', json.dumps(obj.get('统计', {}), ensure_ascii=False)[:1200])
    print('活跃线:', json.dumps(obj.get('活跃线', {}), ensure_ascii=False)[:800])
    for k in ['A共振池(重要度排序)','按题材归类','概念叠加候选','纯预增未叠加','预期已兑现(年内已翻倍,不入候选)','刚点火(有涨停未透支)','已发酵对照Top12']:
        v = obj.get(k)
        print('POOL', k, type(v).__name__, len(v) if hasattr(v,'__len__') else '')
print('--- 双源交叉 keyword checks')
for kw in ['双源','iwencai','东财','交叉','成色来源','报告期']:
    print(kw, s.count(kw))
for m in re.finditer('双源', s):
    print('CTX:', s[max(0,m.start()-120):m.start()+120].replace('\r',' ').replace('\n',' '))
