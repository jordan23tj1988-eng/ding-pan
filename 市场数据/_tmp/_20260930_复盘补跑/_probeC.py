from pathlib import Path
ls = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
for i in range(539, 660):
    print(i + 1, ':', ls[i])
