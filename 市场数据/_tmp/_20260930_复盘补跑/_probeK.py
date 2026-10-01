import json, re
j = json.load(open('_学习/judgment_20260929.json', encoding='utf-8'))
b = j['bodies']['limitup']
a = b.find('<!--LEDGER-->')
pat = re.compile(r'<details\b|</details>')
depth = 0
end = None
for m in pat.finditer(b, a):
    if m.group(0).startswith('<details'):
        depth += 1
    else:
        depth -= 1
        if depth == 0:
            end = m.end()
            break
print('anchor', a, 'end', end, 'gap', (end - a) if end else None)
print('--- before end:', re.sub(r'\s+', ' ', b[end - 150:end]))
print('--- after end :', re.sub(r'\s+', ' ', b[end:end + 500]))
print('--- next markers after end:')
for m in re.finditer(r'<h[12][^>]*>|<section[^>]*>', b[end:end + 20000]):
    print('   @+', m.start(), ':', re.sub(r'\s+', ' ', b[end + m.start(): end + m.start() + 130]))
print('--- tail:', re.sub(r'\s+', ' ', b[-500:]))
