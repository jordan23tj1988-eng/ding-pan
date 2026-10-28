import csv, json, collections

rows = list(csv.DictReader(open('20261027/zt_pool.csv', encoding='utf-8-sig')))
m = json.load(open('_学习/题材归位_20261027.json', encoding='utf-8'))['映射']
by = collections.defaultdict(list)
for r in rows:
    k = m.get(r['代码'], {}).get('大方向') or '未归位'
    by[k].append((int(float(r['连板数'])), r['代码'], r['名称']))
for k, v in sorted(by.items(), key=lambda x: -len(x[1])):
    v.sort(reverse=True)
    print('%-10s n=%2d 最高%d板 %s' % (k, len(v), v[0][0], [x[1] + x[2] + '(%d板)' % x[0] for x in v[:4]]))
