from pathlib import Path
ls = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
for i, l in enumerate(ls):
    s = l.strip()
    if "complete']" in s or s.startswith('def _legacy') or s.startswith('def _structured') or "['status']=" in s:
        print(i + 1, ':', s[:200])
