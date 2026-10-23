# -*- coding: utf-8 -*-
import json, io, os
P='_学习/总审_20261023.json'; P0='_学习/总审_20261022.json'
raw=open(P,'rb').read()
print('BOM?', raw[:3]==b'\xef\xbb\xbf', 'bytes', len(raw))
print('CRLF?', b'\r\n' in raw, 'LF count', raw.count(b'\n'))
d=json.loads(raw.decode('utf-8'))
d0=json.load(open(P0,encoding='utf-8'))
print('keys match set:', set(d)==set(d0), 'order match:', list(d)==list(d0), 'n', len(d))
print('五路裁决 n=', len(d['五路裁决']), [x['路'] for x in d['五路裁决']])
need=['原档位','原置信度','裁决','裁决理由','荐票核验','档位','置信度','结论']
print('五路字段齐:', all(all(k in x for k in need) for x in d['五路裁决']))
print('裁决值:', [x['裁决'] for x in d['五路裁决']])
for k in ['综合深挖','认知迭代','线索跟踪','指派清单']:
    print(k,'n=',len(d[k]),'nonempty=',bool(d[k]))
print('线索来源路集合', sorted(set(x['来源路'] for x in d['线索跟踪'])))
print('指派ID', [x['指派ID'] for x in d['指派清单']], '截止', set(x['截止'] for x in d['指派清单']))
print('昨日战绩验收 n=', len(d['昨日战绩验收']), [x['路'] for x in d['昨日战绩验收']])
print('矛盾捕获 n=', len(d['矛盾捕获']), [x['编号'] for x in d['矛盾捕获']])
for i,x in enumerate(d['矛盾捕获']): 
    miss=[k for k in ('矛盾','各路口径','裁决','依据') if k not in x]
    if miss: print('  缺字段',x['编号'],miss)
s=d['筛选清单']
w=sum(x['建议权重%'] for x in s['明细'])
print('明细n',len(s['明细']),'sum建议权重',round(w,4),'声明',s['留用合计权重%'],'留/剔',s['留数'],s['剔数'],
      '实际留',sum(1 for x in s['明细'] if x['留/剔']=='留'),'实际剔',sum(1 for x in s['明细'] if x['留/剔']=='剔'))
print('原权重合计',round(sum(x['原权重%'] for x in s['明细']),4))
print('总诀键', list(d['总裁决'].keys()), '次日验证点 n', len(d['总裁决']['次日验证点']))
print('检查四项 bool', {k:v for k,v in d['检查四项'].items() if isinstance(v,bool)})
# 20261026 出现位置
def walk(o,p=''):
    if isinstance(o,dict):
        for k,v in o.items(): yield from walk(v,p+'/'+str(k))
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from walk(v,p+'[%d]'%i)
    elif isinstance(o,str):
        if '20261026' in o: yield p
hits=list(walk(d))
from collections import Counter
c=Counter(hits)
print('20261026 出现字段路径数', len(hits))
for k,v in c.items(): print('   ',k,v)
