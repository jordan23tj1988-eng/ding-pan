import json,re,os
B=r'D:\股票数据\市场数据'
files=['_学习/limitup判断_20260924.json','_学习/交易计划_limitup_20260924.json','_学习/_运行状态/limitup_20260924.json']
for rel in files:
 p=os.path.join(B,rel); x=json.load(open(p,encoding='utf-8-sig')); print('JSON_OK',rel,os.path.getsize(p))
print('DATE',json.load(open(os.path.join(B,files[0]),encoding='utf-8-sig'))['日期'])
state=json.load(open(os.path.join(B,files[2]),encoding='utf-8-sig')); print('STATE',state)
html=open(os.path.join(B,'_学习/limitup_body_20260924.html'),encoding='utf-8').read()
expected=['一 涨停复盘 · Top5荐票','二 市场温度 · 涨停生态','三 归位台账','四 涨停质量库 · 因子与规则','五 自主深挖','六 我的认知迭代']
h2=re.findall(r'<h2>(.*?)</h2>',html)
print('H2',h2,'H2_OK',h2==expected)
print('DIV_BALANCE',html.count('<div'),html.count('</div>'),'SECTION_BALANCE',html.count('<section'),html.count('</section>'))
print('NO_FORMAL_BUYS',json.load(open(os.path.join(B,files[1]),encoding='utf-8-sig'))['buys']==[])
print('NO_SECRETS',not re.search(r'(api[_ -]?key|password|token|secret)\s*[:=]',html,re.I))
