import json, re, shutil
from pathlib import Path
p = Path('_学习/judgment_20260929.json')
d = json.loads(p.read_text(encoding='utf-8'))
body = d['bodies']['lhb']
STUB = '<h2>二 资金温度 · 日度统计(买侧席位明细)</h2>'
target = '<h2>二、今日S/A动向：双源席位状态</h2>'
assert body.count('<h2>二') == 1, body.count('<h2>二')
assert body.count(target) == 1, body.count(target)
i = body.find(target)
shutil.copy(p, str(p) + '.bak_seat2_20260930')
d['bodies']['lhb'] = body[:i] + STUB + '\n' + body[i:]
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
# 回读核验
d2 = json.loads(p.read_text(encoding='utf-8'))
b2 = d2['bodies']['lhb']
print('len', len(b2), '| <h2>二 计数', b2.count('<h2>二'), '| stub 存在', STUB in b2)
print('h2 列表:', [re.sub(r'<[^>]+>', '', h).strip()[:40] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', b2, re.S)])
# 渲染器侧验证
import importlib.util, sys
spec = importlib.util.spec_from_file_location('mrl', 'module_render_lhb.py'); m = importlib.util.module_from_spec(spec); sys.modules['mrl'] = m; spec.loader.exec_module(m)
print('r_sec2_preserve 空?', not m.r_sec2_preserve(b2))
print('a以上其余 body 未变:', all(d2['bodies'][k] == json.loads(Path(str(p) + '.bak_seat2_20260930').read_text(encoding='utf-8'))['bodies'][k] for k in d2['bodies'].keys() - {'lhb'} if k in d2['bodies']))
