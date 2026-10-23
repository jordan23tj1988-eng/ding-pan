import json,glob,re
for r in ['auction','lhb','theme','logic','limitup']:
    p=f'_学习/{r}判断_20261023.json'
    s=open(p,encoding='utf-8').read()
    print('='*20,r)
    for code in ['003021','301502','688836','300296','603721','002474','002979','300561','002724','603278','002354','002626']:
        n=s.count(code)
        if n: print(f'  {code}: {n} 次')
