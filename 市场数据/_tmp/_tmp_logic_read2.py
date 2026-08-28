import json, io, sys, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')

def jl(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

print('=== 题材归位_20260826 ===')
d = jl(os.path.join(X, '题材归位_20260826.json'))
print(json.dumps(d, ensure_ascii=False, indent=1))
print()
print('=== _题材四维 (keys + 20260826) ===')
d4 = jl(os.path.join(X, '_题材四维.json'))
print('type', type(d4))
if isinstance(d4, dict):
    ks = list(d4.keys())
    print('keys', ks[:20], '...total', len(ks))
    tgt = d4.get('20260826') or d4.get(ks[-1])
    print(json.dumps(tgt, ensure_ascii=False, indent=1)[:6000])
