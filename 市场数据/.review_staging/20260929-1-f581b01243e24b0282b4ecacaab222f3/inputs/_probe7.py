import json, re
from pathlib import Path
learn = Path('_学习')
for d in ['20260928', '20260929']:
    j = json.load(open(learn / ('judgment_' + d + '.json'), encoding='utf-8'))
    print('##########', d)
    for r in ['auction', 'lhb', 'limitup', 'index']:
        b = j.get('bodies', {}).get(r) or ''
        hs = re.findall(r'<h2[^>]*>(.*?)</h2>', b, re.S)
        hs = [re.sub(r'<[^>]+>', '', h).strip() for h in hs]
        print('  ', r, 'body len', len(b), 'h2:', hs)
        fp = learn / (r + '判断_' + d + '.json')
        if fp.exists():
            top = json.load(open(fp, encoding='utf-8'))
            print('      判断 keys:', list(top.keys()))
        else:
            print('      判断 file missing:', fp.name)
