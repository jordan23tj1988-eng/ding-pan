from pathlib import Path
p=Path(r'D:\股票数据\市场数据\restore_lhb_page.py');x=p.read_text(encoding='utf8');a=x.index('    # Deduplicate fifth/sixth headings');b=x.index('    if page.count("<h2>") < 6',a);blk='''    # Deduplicate fifth/sixth headings when current head already contains them.
    _seen_h = set()
    def _dedup(m):
        title = m.group(1)
        if title[:1] in ("五", "六"):
            if title[:1] in _seen_h:
                return ""
            _seen_h.add(title[:1])
        return m.group(0)
    page = re.sub(r"<h2>([^<]+)</h2>", _dedup, page)
''';x=x[:a]+blk+x[b:];p.write_text(x,encoding='utf8');compile(x,str(p),'exec');print('fixed literal block')
