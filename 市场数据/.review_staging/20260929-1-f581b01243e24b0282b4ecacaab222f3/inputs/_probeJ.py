import json, re
j = json.load(open('_学习/judgment_20260929.json', encoding='utf-8'))
b = j['bodies']['limitup']
a = b.find('<!--LEDGER-->')
seg = b[a:a + 12000]
d0 = seg.find('<details')
pos = d0
depth = 0
i = d0
pat = re.compile(r'<details\b|</details>')
end = None
for m in pat.finditer(seg, d0):
    pass
# balanced scan
depth = 0
for m in pat.finditer(seg, d0):
    if m.group(0) == '<details':
        depth += 1
    else:
        depth -= 1
        if depth == 0:
            end = m.end()
            break
print('anchor at', a, 'details end offset', end, 'abs', a + end if end else None)
print('--- 120 before end:', re.sub(r'\s+', ' ', seg[end - 120:end]))
print('--- 400 after end :', re.sub(r'\s+', ' ', seg[end:end + 400]))
print('--- next structural markers after end:')
for m in re.finditer(r'<h[12][^>]*>|<section[^>]*>', b[a + end: a + end + 8000]):
    print('   @+', m.start(), ':', re.sub(r'\s+', ' ', b[a + end + m.start(): a + end + m.start() + 120]))
print('--- body tail 400:', re.sub(r'\s+', ' ', b[-400:]))
