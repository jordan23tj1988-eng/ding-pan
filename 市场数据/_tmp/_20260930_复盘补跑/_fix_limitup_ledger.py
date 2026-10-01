# -*- coding: utf-8 -*-
"""一次性修复：把 20260929 的 limitup 正文恢复为路由标准正文(6段)+补齐 <!--/LEDGER--> 闭合锚。
根因：涨停复盘台账.py::inject 用 b[find('<!--/LEDGER-->'):] 取续接点，body 缺闭合锚时 find=-1 → 丢弃锚后全部正文。
本脚本只还原磁盘产物，不改生产脚本；恢复后由 涨停复盘台账.py 正常重注入。"""
import json, re, shutil
from pathlib import Path

L = Path('_学习')
jp = L / 'judgment_20260929.json'
bodyf = L / 'limitup_body_20260929.html'
ANCH, CLOSE = '<!--LEDGER-->', '<!--/LEDGER-->'

bodyM = bodyf.read_text(encoding='utf-8')
J = json.load(open(jp, encoding='utf-8'))
old = J['bodies']['limitup']

assert bodyM.count(ANCH) == 1 and bodyM.count(CLOSE) == 0, ('src anchors', bodyM.count(ANCH), bodyM.count(CLOSE))
a = bodyM.find(ANCH)
assert old.count(ANCH) == 1 and old.count(CLOSE) == 0, ('cur anchors', old.count(ANCH), old.count(CLOSE))
a_old = old.find(ANCH)
same_prefix = bodyM[:a] == old[:a_old]
print('prefix identical (锚前正文一致):', same_prefix, len(bodyM[:a]), len(old[:a_old]))
assert same_prefix, '预取校验失败：标准正文与judgment锚前内容不一致，停止'
h4 = bodyM.find('<h2', a)
tail = bodyM.rfind('</div>', a, h4)
print('h2四@', h4, 'tail@', tail, 'tail..h4=', repr(bodyM[tail:h4]))
assert bodyM[tail:h4].strip() == '</div>', 'card 闭合位置校验失败'
print('原judgment锚后(丢失前)内容头 160:', re.sub(r'\s+', ' ', old[a_old:a_old + 160]))
print('标准正文 h2:', [re.sub(r'<[^>]+>', '', h)[:28] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', bodyM, re.S)])
print('原judgment h2:', [re.sub(r'<[^>]+>', '', h)[:28] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', old, re.S)])

shutil.copy2(str(jp), str(jp) + '.bak_limitup_restore_20260930')
newM = bodyM[:tail] + CLOSE + bodyM[tail:]
J['bodies']['limitup'] = newM
json.dump(J, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

J2 = json.load(open(jp, encoding='utf-8'))
b = J2['bodies']['limitup']
print('恢复后 len', len(b), 'anchors', b.count(ANCH), b.count(CLOSE))
print('恢复后 h2:', [re.sub(r'<[^>]+>', '', h)[:28] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', b, re.S)])
print('恢复后 尾部160:', re.sub(r'\s+', ' ', b[-160:]))
print('其他路 body 长度完好:', {k: len(v) for k, v in J2['bodies'].items()})
