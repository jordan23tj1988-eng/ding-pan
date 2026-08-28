import json, io, sys, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
p = os.path.join(X, '中报预增雷达_20260826.json')
raw = open(p, 'rb').read()
print('bytes', len(raw))
s = raw.decode('utf-8', errors='replace')
print('replace_count', s.count('\ufffd'))
obj = None
try:
    obj = json.loads(s)
    print('json.loads OK')
except Exception as e:
    print('loads FAIL', e)
    try:
        obj, idx = json.JSONDecoder().raw_decode(s)
        print('raw_decode OK, consumed', idx, 'of', len(s))
    except Exception as e2:
        print('raw_decode FAIL', e2)

if obj is not None:
    print('TOP KEYS:')
    for k, v in obj.items():
        if isinstance(v, list):
            print(' ', k, 'list', len(v))
        elif isinstance(v, dict):
            print(' ', k, 'dict', len(v), list(v.keys())[:12])
        else:
            print(' ', k, '=', str(v)[:300])
else:
    for m in re.finditer(r'\n (\"[^\"]{1,60}\"): [\{\[]', s):
        print('KEY@', m.start(), m.group(1))
print()
print('双源关键词:', s.count('双源'), '| 交叉:', s.count('交叉'), '| iwencai:', s.count('iwencai'), '| 东财:', s.count('东财'))
for m in list(re.finditer(r'双源', s))[:5]:
    print('  ctx:', s[max(0,m.start()-90):m.start()+90].replace('\n',' '))
