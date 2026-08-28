import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
def show(name, p, n=4000):
    print('=== %s ===' % name)
    try:
        j = json.load(open(p, 'r', encoding='utf-8'))
    except Exception as e:
        print('  读取失败', e); return
    print(json.dumps(j, ensure_ascii=False, indent=1)[:n])
    print()

show('模拟盘logic状态', os.path.join(X, '_模拟盘', 'logic', '状态.json'), 2500)
show('待深挖清单', os.path.join(X, '待深挖清单_20260826.json'), 2000)
show('fact', os.path.join(X, 'fact_20260826.json'), 3500)
show('summary', os.path.join(B, '20260826', 'summary.json'), 1500)
j = json.load(open(os.path.join(X, '_题材四维.json'), 'r', encoding='utf-8'))
print('=== 题材四维 top keys ===', list(j.keys())[:10])
d = j.get('20260826') or j
print(json.dumps(d, ensure_ascii=False, indent=1)[:3000] if not isinstance(d, list) else json.dumps(d[:6], ensure_ascii=False, indent=1)[:3000])
