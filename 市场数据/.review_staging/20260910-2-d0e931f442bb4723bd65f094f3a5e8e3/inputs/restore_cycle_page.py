import re, shutil
from pathlib import Path

G=Path(r'D:/黄金对照版717/cycle.html')
SITE=Path(r'D:/股票数据/市场数据/复盘/盯盘台/cycle.html')
BAK=Path(r'D:/股票数据/市场数据/复盘/盯盘台/cycle.html.before_evolution_sync_20260912.bak')
OUT=SITE.with_suffix('.html.cycle_restore_tmp')

def sec(s, sid):
    m=re.search(r'<section id="'+re.escape(sid)+r'"[^>]*>.*?</section>',s,re.S)
    if not m: raise RuntimeError('missing '+sid)
    return m.group(0)
def evo(s):
    return re.findall(r'<section class="evolution"[^>]*>.*?</section>',s,re.S)

g=G.read_text(encoding='utf-8'); old=BAK.read_text(encoding='utf-8'); cur=SITE.read_text(encoding='utf-8')
# 部署时 cycle 可能已被 release 覆盖；能力模块优先从现站备份/概览页取，保证实时重生成不丢
cur_evo=evo(cur)
if len(cur_evo)<2:
    idx=SITE.parent/'index.html'
    if idx.exists(): cur_evo=evo(idx.read_text(encoding='utf-8'))
if len(cur_evo)<2: raise RuntimeError('current evolution count='+str(len(cur_evo)))
cur_evo=cur_evo[:2]
# 黄金版六、七段从“六”标题到页尾内容；替换为当前两个能力模块
m6=re.search(r'<h2>六 ', g)
if not m6: raise RuntimeError('golden section six missing')
foot=g.rfind('<div class="foot">')
if foot<0: raise RuntimeError('golden foot missing')
# 保留黄金五段结束至 footer 的页框；能力模块作为六/七展示内容
head=g[:m6.start()]
tail=g[foot:]
body='\n'.join(cur_evo)
g=head+body+'\n'+tail
# 结构断言: 黄金前五视觉锚点 + 两个能力模块
for token in ('class="steps"','class="cols"','class="stages"','class="posmeter"'):
    if token not in g: raise RuntimeError('golden visual token missing '+token)
if len(re.findall(r'<section class="evolution"[^>]*>',g))!=2: raise RuntimeError('output evolution count')
shutil.copy2(SITE, str(SITE)+'.before_cycle_restore_20260912.bak')
OUT.write_text(g,encoding='utf-8',newline='\n')
shutil.move(str(OUT), SITE)
print('restored', SITE, 'bytes', SITE.stat().st_size)
print('golden first5 visual tokens:', all(x in g for x in ('class="steps"','class="cols"','class="stages"','class="posmeter"')))
print('sections', re.findall(r'<section id="([^"]+)"',g))
print('evolution',len(evo(g)))
