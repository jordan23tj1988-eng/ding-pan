import json, io, sys, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')

def jl(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

print('=== 战绩画像汇总 ===')
try:
    d = jl(os.path.join(X, '子agent增强', '_战绩画像汇总_20260826.json'))
    print(json.dumps(d, ensure_ascii=False, indent=1)[:3000])
except Exception as e:
    print('ERR', e)

print()
print('=== 总审_20260825 keys ===')
try:
    d = jl(os.path.join(X, '总审_20260825.json'))
    print(list(d.keys()))
    for k in d.keys():
        if '指派' in k:
            print('--- ', k)
            print(json.dumps(d[k], ensure_ascii=False, indent=1)[:4000])
except Exception as e:
    print('ERR', e)
