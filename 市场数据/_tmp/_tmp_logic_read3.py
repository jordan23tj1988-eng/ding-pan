import json, io, sys, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')

def jl(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

print('=== fact_20260826 ===')
print(json.dumps(jl(os.path.join(X, 'fact_20260826.json')), ensure_ascii=False, indent=1))
print()
print('=== 待深挖清单_20260826 ===')
print(json.dumps(jl(os.path.join(X, '待深挖清单_20260826.json')), ensure_ascii=False, indent=1))
print()
print('=== summary 20260826 ===')
print(json.dumps(jl(os.path.join(B, '20260826', 'summary.json')), ensure_ascii=False, indent=1))
print()
print('=== 模拟盘 logic 状态.json ===')
print(json.dumps(jl(os.path.join(X, '_模拟盘', 'logic', '状态.json')), ensure_ascii=False, indent=1))
print()
print('=== 认知库_logic_20260825 ===')
print(json.dumps(jl(os.path.join(X, '子agent增强', '认知库_logic_20260825.json')), ensure_ascii=False, indent=1)[:5000])
