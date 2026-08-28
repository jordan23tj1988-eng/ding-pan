import json, io, sys, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
p = os.path.join(X, 'logic判断_20260825.json')
print('=== logic判断_20260825.json ===')
print(open(p, 'r', encoding='utf-8').read())
print()
for f in ['逻辑荐票_20260825.json', '交易计划_logic_20260825.json', '中报预增成色判定_20260825.json']:
    fp = os.path.join(X, f)
    print('=== %s exists=%s ===' % (f, os.path.exists(fp)))
    if os.path.exists(fp):
        t = open(fp, 'r', encoding='utf-8').read()
        print(t[:2500])
    print()
print('风险日历_20260826 exists=', os.path.exists(os.path.join(X, '风险日历_20260826.json')))
import glob
print('风险日历 glob:', glob.glob(os.path.join(X, '风险日历*')))
