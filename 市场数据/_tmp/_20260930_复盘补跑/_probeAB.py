import json, re, importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('mrl', 'module_render_lhb.py'); m = importlib.util.module_from_spec(spec); sys.modules['mrl'] = m; spec.loader.exec_module(m)
def labs(b):
    return [re.sub(r'<[^>]+>', '', h).strip()[:44] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', b, re.S)]
cur = json.load(open('_学习/judgment_20260929.json', encoding='utf-8'))['bodies']['lhb']
bak = json.load(open('_学习/judgment_20260929.json.bak_force_cycle_20260930', encoding='utf-8'))['bodies']['lhb']
b28 = json.load(open('_学习/judgment_20260928.json', encoding='utf-8'))['bodies']['lhb']
for name, b in (('20260929 当前', cur), ('20260929 备份(我patch前)', bak), ('20260928', b28)):
    print('==', name, len(b))
    for h in labs(b):
        print('    ', h)
print('=== r_sec2_preserve 结果:')
for name, b in (('29当前', cur), ('29备份', bak), ('28', b28)):
    r = m.r_sec2_preserve(b)
    print('  ', name, '空?', not r, '|', re.sub(r'<[^>]+>', ' ', r)[:120])
