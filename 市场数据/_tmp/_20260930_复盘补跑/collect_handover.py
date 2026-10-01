# -*- coding: utf-8 -*-
"""导出 20260930 断点交接所需的原始材料: ①daily-review 完整步骤清单 ②9/30 产物存在性。
只读, 输出到 _tmp/_20260930_复盘补跑/handover_material.txt
"""
import json, time
from pathlib import Path

HOME = Path.home()
PROF = HOME / 'AppData/Local/hermes/profiles/a'
SRC = Path(r'D:\股票数据\市场数据')
OUT = SRC / '_tmp/_20260930_复盘补跑/handover_material.txt'

d = json.loads((PROF / 'cron/jobs.json').read_text(encoding='utf-8'))
jobs = d if isinstance(d, list) else d.get('jobs', d)
if isinstance(jobs, dict):
    jobs = list(jobs.values())
job = [j for j in jobs if (j.get('id') or '') == 'c4d23047161f'][0]
prompt = job.get('prompt') or ''

lines = []
lines.append('===== daily-review(c4d23047161f) prompt 全文 =====')
lines.append('model=%s provider=%s schedule=%s' % (job.get('model'), job.get('provider'), job.get('schedule_display')))
for i, l in enumerate(prompt.splitlines(), 1):
    lines.append('%4d | %s' % (i, l))

lines.append('')
lines.append('===== 20260930 产物存在性(按 mtime) =====')
pats = ['judgment_20260930.json', '总审_20260930.json', '推演_20260930.json', '周期投票_*20260930.json',
        '周期主判_20260930.json', 'playbook.json', '风险事件_20260930.json', '风险日历_20260930.json',
        '涨停质量荐票_20260930.json', '席位荐票_20260930.json', '题材归位_20260930.json',
        '市场温度卡_20260930.html', '竞价评分_20260930.json', '质量库折叠_20260930.html',
        '涨停复盘台账_20260930.json', '龙虎榜台账_20260930.json']
for pat in pats:
    hits = sorted(SRC.glob('_学习/' + pat))
    if not hits:
        lines.append('MISSING  %s' % pat)
    for h in hits:
        lines.append('%-9s %s  %s  %dB' % ('OK', time.strftime('%m-%d %H:%M', time.localtime(h.stat().st_mtime)), h.name, h.stat().st_size))

lines.append('')
lines.append('===== 20260930 目录/盘中/模拟盘 =====')
for p in [SRC / '20260930', SRC / '盘中/20260930', SRC / '复盘/盯盘台/_history', SRC / '.review_staging']:
    lines.append('%s exists=%s' % (p, p.exists()))
for sub in ['playbook.json']:
    q = SRC / '盘中/20260930' / sub
    lines.append('盘中/20260930/%s exists=%s' % (sub, q.exists()))
jstub = SRC / '_学习/judgment_20260930.json'
if jstub.exists():
    lines.append('judgment_20260930.json 内容: %s' % jstub.read_text(encoding='utf-8')[:400])

lines.append('')
lines.append('===== 最近一次 9/30 stage(review_staging) =====')
st = sorted(SRC.glob('.review_staging/20260930-*'), key=lambda x: x.stat().st_mtime)
lines.append('staging dirs: %s' % [p.name for p in st[-5:]] if st else 'staging dirs: 无')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('written', OUT, len(lines), 'lines')
# 只打印 9/30 产物段, 便于 ráp 检查
s = '\n'.join(lines)
i = s.find('===== 20260930 产物存在性')
print(s[i:i + 2600])
