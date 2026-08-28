import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
X = r'D:\股票数据\市场数据\_学习'
j = json.load(open(os.path.join(X, '_题材四维.json'), 'r', encoding='utf-8'))
print('top keys:', list(j.keys())[:12])
d = j.get('20260826')
if d is None:
    # maybe list of days
    print(type(j))
    print(json.dumps(j, ensure_ascii=False)[:800])
else:
    print('20260826 keys:', list(d.keys()) if isinstance(d, dict) else type(d))
    s = json.dumps(d, ensure_ascii=False, indent=1)
    print(s[:2500])
    for k in ['有色/贵金属', '有色/工业金属', '电力', '家居']:
        if isinstance(d, dict):
            for kk, vv in d.items():
                if isinstance(vv, dict) and k in json.dumps(kk, ensure_ascii=False):
                    print('  >>', kk, json.dumps(vv, ensure_ascii=False)[:300])
