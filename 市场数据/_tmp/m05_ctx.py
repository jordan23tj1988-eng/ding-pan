import re,sys
pairs=[('lhb','003021'),('logic','301502'),('logic','003021'),('theme','688836'),('theme','003021'),('logic','002724'),('theme','002724'),('auction','003021')]
for r,code in pairs:
    s=open(f'_学习/{r}判断_20261023.json',encoding='utf-8').read()
    for m in re.finditer(code,s):
        print(f'--- {r} {code} @{m.start()}')
        print(s[max(0,m.start()-500):m.start()+400].replace('\n',' '))
        print()
