import sys;sys.path.insert(0,r'D:\股票数据\市场数据')
import importlib.util,pathlib,re,shutil
R=pathlib.Path(r'D:\股票数据\市场数据'); site=R/'复盘/盯盘台/limitup.html'; old=site.read_text(encoding='utf8'); spec=importlib.util.spec_from_file_location('m',R/'module_render_limitup.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m); body=m.build_page_full('20260911'); p=R/'_学习/_模拟盘/limitup/看板_20260911.html'; paper='<!--PAPERTRADE-->\n'+p.read_text(encoding='utf8')+'\n<!--/PAPERTRADE-->\n' if p.exists() else '<!--PAPERTRADE--><!--/PAPERTRADE-->'
body=body.replace('<!--PAPERTRADE-->','').replace('<!--/PAPERTRADE-->',''); body=body+'\n'+paper
w=old.find('<div class="wrap">'); ws=old.find('>',w)+1; foot=old.rfind('<div class="foot">');
if w<0 or foot<0: raise RuntimeError('shell bounds missing')
new=old[:ws]+'\n'+body+'\n'+old[foot:]; shutil.copy2(site,site.with_name(site.name+'.before_limitup_rebuild_20260911.bak')); site.write_text(new,encoding='utf8',newline='\n'); print('rebuilt',len(new), 'body',len(body))



