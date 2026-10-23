# -*- coding: utf-8 -*-
import json,io,sys
sys.path.insert(0,'.')
p='_学习/推演_20261023.json'
raw=open(p,'rb').read()
print('BOM:', raw[:3]==b'\xef\xbb\xbf', 'bytes:', len(raw))
d=json.loads(raw.decode('utf-8'))
print('顶层键:', list(d.keys()))
pred=d['次日可证伪预测']
print('条数:', len(pred))
FACT=set(json.load(open('_学习/fact_20261023.json',encoding='utf-8'))['facts'].keys())
print('fact字段数:',len(FACT))
ok=True
for it in pred:
    c=it['判定条件']; f=c['指标']
    inwhitelist = f in FACT or f in ('一进二率','二进三率','代码封板','代码收红')
    good = inwhitelist and c.get('比较') in ('>=','<=','=') and isinstance(c.get('阈值'),(int,float))
    ok &= good
    print(f"  P{it['序号']}: {f} {c['比较']} {c['阈值']} 档={it['档位']} 置信={it['置信度']} 白名单={inwhitelist} 代码={c.get('代码','-')} {'OK' if good else 'FAIL'}")
print('字段/运算符全部合规:', ok)
print('每条必备键:', all(set(['项','预测','判定条件','预期','置信度','档位','validation_spec','代价'])<=set(x) for x in pred))
# 后视检查
import re
txt=json.dumps(d,ensure_ascii=False)
for bad in ['20261024','20261025']:
    print(bad,'出现次数=',txt.count(bad))
print('20261026 出现次数=',txt.count('20261026'))
# 关禁词检查
for w in ['买入','卖出','止损','仓位建议','加仓','减仓至']:
    if w in txt: print('!! 出现禁词',w)
