# -*- coding: utf-8 -*-
import re, json, os
from html.parser import HTMLParser
L=r'D:/股票数据/市场数据/_学习'
new=open(os.path.join(L,'cycle_body_20261023.html'),encoding='utf-8').read()
old=open(os.path.join(L,'cycle_body_20261022.html'),encoding='utf-8').read()

h2n=re.findall(r'<h2>(.*?)</h2>',new); h2o=re.findall(r'<h2>(.*?)</h2>',old)
print('h2 数 =',len(h2n)); print('h2 一致 =',h2n==h2o)
for a,b in zip(h2n,h2o): print('  %s  %s'%(('OK ' if a==b else 'DIFF'),a))

anchors=['<!--VOLSTEP-->','<!--LEADIND-->','<!--LADDER-->','<!--MACHVOTE-->','<!--VOTEBOARD-->']
print('机器锚(应全0) =',{a:new.count(a) for a in anchors})
print('任意注释 =',re.findall(r'<!--.*?-->',new))

# 栈式配平
VOID={'br','img','hr','input','meta','link'}
class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.st=[]; s.err=[]
    def handle_starttag(s,t,a):
        if t not in VOID: s.st.append((t,s.getpos()))
    def handle_endtag(s,t):
        if t in VOID: return
        if not s.st: s.err.append(('多余闭合',t,s.getpos())); return
        if s.st[-1][0]!=t:
            s.err.append(('不匹配',t,s.getpos(),'栈顶',s.st[-1]))
            # 尝试弹到匹配
            for i in range(len(s.st)-1,-1,-1):
                if s.st[i][0]==t: del s.st[i:]; break
        else: s.st.pop()
p=P(); p.feed(new)
print('未闭合栈 =',p.st)
print('配平错误 =',p.err if p.err else 'None')
print('div <%d> </%d> ; section %d/%d'%(new.count('<div'),new.count('</div>'),new.count('<section>'),new.count('</section>')))

# 裸 null / None / NaN
print('裸null/None/NaN 命中 =',re.findall(r'(?<![\w\u4e00-\u9fa5])(null|None|NaN|undefined)(?![\w\u4e00-\u9fa5])',new))

# h2 段落非空（模拟 module_render_cycle._h2_seg）
def seg(body,a,b):
    i=body.find(a); j=body.find(b,i+1) if b else -1
    return body[i:j] if i>=0 and j>i else (body[i:] if i>=0 and not b else '')
pairs=[('<h2>一','<h2>二'),('<h2>二','<h2>三'),('<h2>三','<h2>四'),('<h2>四','<h2>五'),('<h2>五','<h2>六'),('<h2>六','<h2>七'),('<h2>七',None)]
for a,b in pairs:
    s=seg(new,a,b); print('段 %s len=%d %s'%(a,len(s),'OK' if len(s)>400 else '★过短/缺失'))
head=new[:new.find('<h2>一')]
print('头部区 len=%d  hero=%s stance=%s kpi=%d'%(len(head),'class="hero"' in head,'class="stance"' in head,head.count('class="kpi"')))
print('UTF-8 可解码 =',bool(new.encode('utf-8').decode('utf-8')))
print('bytes =',os.path.getsize(os.path.join(L,'cycle_body_20261023.html')))
# json 校验
j=json.load(open(os.path.join(L,'cycle判断_20261023.json'),encoding='utf-8'))
need=['日期','路','周期阶段','量能台阶','情绪三态','攻防总开关','置信度','五路投票汇总','主判与总审是否一致','证据','可证伪条件','盲区声明']
print('JSON 必备键缺 =',[k for k in need if k not in j])
print('JSON 阶段/三态/攻防/置信 =',j['周期阶段'],j['情绪三态'],j['攻防总开关'],j['置信度'])
print('JSON 裸null =',re.findall(r':\s*null',open(os.path.join(L,'cycle判断_20261023.json'),encoding='utf-8').read()))
