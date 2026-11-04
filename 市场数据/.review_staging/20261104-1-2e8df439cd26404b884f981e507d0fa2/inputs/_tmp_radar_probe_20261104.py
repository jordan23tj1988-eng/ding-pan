import json, io, sys, re, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
R = r'D:\股票数据\市场数据'
raw = open(R + r'\_学习\中报预增雷达_20261104.json', 'rb').read()
s = raw.decode('utf-8', errors='replace')
print('bytes', len(raw), 'chars', len(s))
# locate top-level keys
for m in re.finditer(r'\n (\"[^"]+\"): [\{\[]', s):
    print('KEY', m.group(1), '@', m.start())
print('--- tail 600')
print(s[-600:])
print('--- head 800')
print(s[:800])
