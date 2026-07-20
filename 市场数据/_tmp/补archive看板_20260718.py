# -*- coding: utf-8 -*-
"""一次性: 0715/0716 archive补当日master看板(#014回退锚同款逻辑,只动archive不碰live)"""
import os
for d in ['20260715','20260716']:
    kb='_学习/_模拟盘/master/看板_%s.html'%d
    pg='复盘/盯盘台/archive/%s.html'%d
    if not (os.path.isfile(kb) and os.path.isfile(pg)):
        print(d,'缺文件跳过', os.path.isfile(kb), os.path.isfile(pg)); continue
    h=open(pg,encoding='utf-8').read()
    if '<!--PAPERTRADE-->' in h:
        print(d,'已有看板跳过'); continue
    block='<!--PAPERTRADE-->\n'+open(kb,encoding='utf-8').read()+'\n<!--/PAPERTRADE-->'
    j=h.find('<div class="card">')
    if j<0: print(d,'!无card锚'); continue
    h=h[:j]+block+'\n'+h[j:]
    open(pg,'w',encoding='utf-8').write(h)
    chk=open(pg,encoding='utf-8').read()
    print(d,'注入', 'OK' if ('<!--PAPERTRADE-->' in chk and '<!--/PAPERTRADE-->' in chk) else 'FAIL')
