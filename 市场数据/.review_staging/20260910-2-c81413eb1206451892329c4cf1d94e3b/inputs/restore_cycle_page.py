import re, shutil, sys, json
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
date=sys.argv[1] if len(sys.argv)>1 else '20260910'
# 能力模块从现站/概览取；正文必须从目标日 judgment 取，黄金页只提供壳和样式
cur_evo=evo(cur)
if len(cur_evo)<2:
    idx=SITE.parent/'index.html'
    if idx.exists(): cur_evo=evo(idx.read_text(encoding='utf-8'))
if len(cur_evo)<2: raise RuntimeError('current evolution count='+str(len(cur_evo)))
cur_evo=cur_evo[:2]
# 生产动态 body 必须来自模块化渲染器（机器卡+目标日正文），不直接复制黄金历史正文
import subprocess
render_out=Path(r'C:/Users/66353/AppData/Local/Temp')/('cycle_dynamic_'+date+'.html')
cp=subprocess.run([sys.executable, str(SITE.parent.parent.parent/'module_render_cycle.py'), date, '--out', str(render_out)], cwd=str(SITE.parent.parent.parent), capture_output=True, text=True, encoding='utf-8')
if cp.returncode!=0 or not render_out.exists(): raise RuntimeError('cycle dynamic renderer failed: '+cp.stderr[-1000:])
dynamic=render_out.read_text(encoding='utf-8')
if dynamic.count('<h2>')<7: raise RuntimeError('target cycle body incomplete')
# 黄金版 head 到 wrap 内容起点；动态 body 自带 hero+七段；页脚沿用黄金版
body_start=g.find('<div class="wrap">')
if body_start<0: raise RuntimeError('golden wrap missing')
body_start=g.find('>',body_start)+1
foot=g.rfind('<div class="foot">')
if foot<0: raise RuntimeError('golden foot missing')
head=g[:body_start]
tail=g[foot:]
g=head+dynamic+'\n'+ '\n'.join(cur_evo)+'\n'+tail
# 结构断言: 黄金 CSS + 当日七段 + 两个能力模块
for token in ('class="steps"','class="cols"','class="stages"','class="posmeter"'):
    if token not in g: raise RuntimeError('golden visual token missing '+token)
if len(re.findall(r'<h2>',g))<7: raise RuntimeError('output h2 incomplete')
if len(re.findall(r'<section class="evolution"[^>]*>',g))!=2: raise RuntimeError('output evolution count')
shutil.copy2(SITE, str(SITE)+'.before_cycle_restore_20260912.bak')
OUT.write_text(g,encoding='utf-8',newline='\n')
shutil.move(str(OUT), SITE)
print('restored', SITE, 'bytes', SITE.stat().st_size)
print('golden first5 visual tokens:', all(x in g for x in ('class="steps"','class="cols"','class="stages"','class="posmeter"')))
print('sections', re.findall(r'<section id="([^"]+)"',g))
print('evolution',len(evo(g)))
