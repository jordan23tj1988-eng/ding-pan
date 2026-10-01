from pathlib import Path
ls = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
for a, b in [(238, 300), (1385, 1460)]:
    print('==========', a, b)
    for i in range(a - 1, b):
        print(i + 1, ':', ls[i])
