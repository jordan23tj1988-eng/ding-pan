# -*- coding: utf-8 -*-
import json, os
B = r'D:\股票数据\市场数据'; L = os.path.join(B, '_学习')
def j(p): return json.load(open(p, encoding='utf-8'))

out=[]
for name in ('auction','lhb','theme','logic','limitup'):
    d = j(os.path.join(L, f'{name}判断_20261026.json'))
    out.append('\n\n##### %s keys=%s' % (name, list(d.keys())))
    for k,v in d.items():
        if k in ('bodies','body','html','段'):
            out.append(f'  [{k}] <skipped len={len(str(v))}>')
            continue
        s = json.dumps(v, ensure_ascii=False)
        out.append(f'--- {k}: {s[:1800]}')

open(os.path.join(B,'_tmp','dump2.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
