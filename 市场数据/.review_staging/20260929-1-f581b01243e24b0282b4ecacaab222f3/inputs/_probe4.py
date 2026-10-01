from pathlib import Path
ls = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
for a, b in [(600, 760)]:
    print('==========', a, b)
    for i in range(a - 1, b):
        print(i + 1, ':', ls[i])
