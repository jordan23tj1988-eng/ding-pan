# -*- coding: utf-8 -*-
import re
out=open('_学习/总审_20261023.json',encoding='utf-8').read()
for t in ['3388','92.5','5.36','4.32','一年']:
    print('OUT has',t,out.count(t))
def show(path,pat,w=260,maxn=6):
    s=open(path,encoding='utf-8').read()
    n=0
    for m in re.finditer(pat,s):
        print('   ...',s[max(0,m.start()-w):m.start()+w].replace('\n',' '))
        n+=1
        if n>=maxn: break
    print('  --hits',n)
print('=== auction: 库规模 / 3388 / 425 ')
show('_学习/auction判断_20261023.json', r'3388|一年|样本|库')
print('=== auction: 925 分位')
show('_学习/auction判断_20261023.json', r'925|分位')
