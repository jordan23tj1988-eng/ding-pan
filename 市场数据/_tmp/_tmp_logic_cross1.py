import json, io, sys, os, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r'D:\股票数据\市场数据'
X = os.path.join(B, '_学习')
D = '20260826'

# ---- zt_pool
zt = {}
with open(os.path.join(B, D, 'zt_pool.csv'), 'r', encoding='utf-8-sig') as f:
    rd = csv.DictReader(f)
    cols = rd.fieldnames
    rows = list(rd)
print('zt cols:', cols)
print('zt rows:', len(rows))
for r in rows:
    zt[r['代码'].strip()] = r
print('sample row:', json.dumps(rows[0], ensure_ascii=False))

# ---- 产业链模板 codes (regex recursive)
raw = open(os.path.join(B, '产业链模板.json'), 'r', encoding='utf-8').read()
tpl = json.loads(raw)
tpl_codes = set(re.findall(r'"(\d{6})"', raw))
print('模板链数:', len(tpl), '模板代码数:', len(tpl_codes))
print('链名:', list(tpl.keys()))

# name map from template
def walk(o, out, path):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, out, path + [k])
    elif isinstance(o, list):
        if len(o) == 2 and all(isinstance(x, str) for x in o) and re.fullmatch(r'\d{6}', o[0] or ''):
            out.append((o[0], o[1], list(path)))
        else:
            for v in o:
                walk(v, out, path)
tplstocks = []
walk(tpl, tplstocks, [])
print('模板个股条目:', len(tplstocks))

# ---- 涨停对链条
zl = json.load(open(os.path.join(X, '涨停对链条_' + D + '.json'), 'r', encoding='utf-8'))
print()
print('涨停对链条 type/keys:', type(zl), (list(zl.keys())[:15] if isinstance(zl, dict) else len(zl)))
print(json.dumps(zl, ensure_ascii=False)[:2500])

out = {'zt_codes': sorted(zt.keys()), 'tpl_codes': sorted(tpl_codes),
       'tpl_stocks': tplstocks}
json.dump(out, open(os.path.join(B, '_tmp_logic_ctx.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print()
print('模板 ∩ 涨停:', sorted(tpl_codes & set(zt.keys())))
for c in sorted(tpl_codes & set(zt.keys())):
    ent = [t for t in tplstocks if t[0] == c]
    print('  ', c, zt[c].get('名称'), zt[c].get('连板数') or zt[c].get('连续板'), ent[0][2] if ent else '?')
