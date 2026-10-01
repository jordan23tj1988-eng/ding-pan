import re, sys, importlib.util, os, json
from pathlib import Path
spec = importlib.util.spec_from_file_location('mrl', 'module_render_lhb.py')
m = importlib.util.module_from_spec(spec)
sys.modules['mrl'] = m
spec.loader.exec_module(m)
d = '20260929'
body = m.load_body(d)
print('body len', len(body))
print('body h2:', [re.sub(r'<[^>]+>', '', h).strip()[:36] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.S)])
print('_body_h2 四 :', repr(m._body_h2(body, '四 '))[:200])
print('_body_h2 六 :', repr(m._body_h2(body, '六 '))[:200])
print('_body_h2 一 :', repr(m._body_h2(body, '一 '))[:200])
print('_body_h2 一二三? ', repr(m._body_h2(body, '四'))[:200])
print('r_lib head:', repr(m.r_lib(d))[:200])
print('席位分档库.html exists:', os.path.isfile('_学习/席位分档库.html'))
p = Path('_学习/席位分档库.html')
if p.is_file():
    s = p.read_text(encoding='utf-8', errors='ignore')
    print('  len', len(s), 'h2:', [re.sub(r'<[^>]+>', '', h).strip()[:30] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', s, re.S)][:6])
    import time
    print('  mtime', time.strftime('%m-%d %H:%M', time.localtime(p.stat().st_mtime)))
print('C1 head:', repr(m.r_judge(body))[:200])
print('C5 head:', repr(m.r_scan(body))[:200])
