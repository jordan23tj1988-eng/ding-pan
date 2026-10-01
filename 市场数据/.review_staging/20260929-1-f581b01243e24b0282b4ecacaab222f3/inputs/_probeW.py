from pathlib import Path
s = Path('生成盯盘台.py').read_text(encoding='utf-8').splitlines()
for i in range(780, 840):
    if i < len(s):
        print(i + 1, ':', s[i])
print('==== restore_lhb_page.py 前 40 行')
r = Path('restore_lhb_page.py').read_text(encoding='utf-8').splitlines()
for i in range(min(40, len(r))):
    print(i + 1, ':', r[i])
print('==== 行数', len(r), len(s))
