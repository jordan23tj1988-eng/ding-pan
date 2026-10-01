from pathlib import Path
ls = Path('涨停复盘台账.py').read_text(encoding='utf-8').splitlines()
for i in range(0, 20):
    print(i + 1, ':', ls[i])
print('...')
for i in range(94, min(120, len(ls))):
    print(i + 1, ':', ls[i])
