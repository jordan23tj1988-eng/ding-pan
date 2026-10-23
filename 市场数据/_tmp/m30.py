# -*- coding: utf-8 -*-
import re
s=open('_学习/theme判断_20261023.json',encoding='utf-8').read()+open('_学习/交易计划_theme_20261023.json',encoding='utf-8').read()
for pat in ['35.3','0.07','12/34','加权']:
    for m in re.finditer(re.escape(pat),s):
        print(pat,'>>',s[max(0,m.start()-180):m.start()+180].replace('\n',' '))
        break
