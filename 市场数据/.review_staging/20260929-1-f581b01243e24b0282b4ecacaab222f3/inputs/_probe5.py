import json
from pathlib import Path
st = Path(r'.review_staging/20260929-1-a54d0b1cf47f449d8eec05dc30fc48b4/site/models')
for r in ['auction', 'lhb', 'limitup', 'index', 'theme', 'logic']:
    m = json.load(open(st / (r + '.json'), encoding='utf-8'))
    print('==', r, 'complete', m['complete'], 'limitations', m['limitations'])
    for s in m['sections']:
        print('    ', s['id'], '| label', s.get('label'), '| refs', len(s['claim_refs']))
    print('    claims by section:', {})
    from collections import Counter
    print('    ', Counter((c['section'], c['role']) for c in m['claims']))
