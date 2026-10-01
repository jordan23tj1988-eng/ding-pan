import json, re
from pathlib import Path
learn = Path('_学习')
j = json.load(open(learn / 'judgment_20260929.json', encoding='utf-8'))
b = j['bodies']['auction']
# paragraphs mentioning 温度 or 胜率
paras = re.findall(r'<p[^>]*>(.*?)</p>', b, re.S)
hits = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', p)).strip() for p in paras]
hits = [h for h in hits if ('温度' in h or '胜率' in h) and h]
print('AUCTION 温度/胜率 paras:', len(hits))
for h in hits[:6]:
    print(' -', h[:400])
# heads of each h2 block
print('--- h2 blocks heads:')
for m in re.finditer(r'<h2[^>]*>(.*?)</h2>(.{0,300})', b, re.S):
    head = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    bodyhead = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', m.group(2))).strip()
    print('  ##', head[:80], '||', bodyhead[:200])
