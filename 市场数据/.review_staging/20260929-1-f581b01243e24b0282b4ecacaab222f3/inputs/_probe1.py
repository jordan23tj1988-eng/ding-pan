import re
from pathlib import Path
ls = Path('review_pages.py').read_text(encoding='utf-8').splitlines()
pats = ["complete']", 'judgment_complete', '_paper(', '_finish(', 'def build_page_model', "errors'].append", 'model[', 'data_conflicts']
for i, l in enumerate(ls):
    if 'def build_page_model' in l or '_paper(' in l or '_finish(' in l or 'judgment_complete' in l or 'data_conflicts' in l:
        print(i + 1, ':', l.strip()[:180])
