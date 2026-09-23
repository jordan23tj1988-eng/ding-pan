from pathlib import Path
import re
site=Path(r'D:/股票数据/市场数据/复盘/盯盘台/cycle.html')
idx=Path(r'D:/股票数据/市场数据/复盘/盯盘台/index.html')
s=site.read_text(encoding='utf-8'); i=idx.read_text(encoding='utf-8')
css=re.search(r'(\.evolution\{.*?)(?=\.chart-title\{)',i,re.S)
if not css: raise RuntimeError('evolution css not found in index')
block=css.group(1)
# 概览页模块使用 --mut，黄金周期页使用 --sub；补同义变量但不改变模块样式
if '--mut' not in s:
    block=':root{--mut:var(--sub)}'+block
s=re.sub(r'\n?<!--EVOLUTION_STYLE_SYNC_START-->.*?<!--EVOLUTION_STYLE_SYNC_END-->\n?','\n',s,flags=re.S)
style='\n<!--EVOLUTION_STYLE_SYNC_START-->\n<style id="evolution-style-sync">'+block+'</style>\n<!--EVOLUTION_STYLE_SYNC_END-->\n'
pos=s.find('</head>')
if pos<0: raise RuntimeError('head missing')
s=s[:pos]+style+s[pos:]
site.write_text(s,encoding='utf-8',newline='\n')
print('injected evolution css chars',len(block),'page bytes',site.stat().st_size)
