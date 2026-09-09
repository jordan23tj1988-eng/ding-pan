import json,os
p='D:/股票数据/市场数据/_学习/judgment_20260908.json'
x=json.load(open(p,encoding='utf-8-sig'))
s=x['bodies']['lhb']
if '<!--LHBLEDGER-->' not in s: s += '<div><!--LHBLEDGER--></div>'
x['bodies']['lhb']=s
with open(p+'.tmp','w',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=1)
os.replace(p+'.tmp',p)
print('lhb anchor ensured')
