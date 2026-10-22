# -*- coding: utf-8 -*-
"""logic 20261021 产出自检：schema/结构/闸门/零后视镜/HTML合规，任一失败 exit 1"""
import json, os, re, csv, sys, importlib

sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\股票数据\市场数据'
sys.path.insert(0, D)
L = os.path.join(D, '_学习')
d = '20261021'
fails, warns, oks = [], [], []


def ok(m):
    oks.append(m)


def bad(m):
    fails.append(m)


def warn(m):
    warns.append(m)


# ---------- 1 logic判断 ----------
p = os.path.join(L, 'logic判断_%s.json' % d)
raw = open(p, encoding='utf-8').read()
j = json.loads(raw)
ok('logic判断 JSON 解析通过 (%d bytes)' % os.path.getsize(p))
for k in ('日期', '路', '判断', '荐票', '认知迭代', '深挖'):
    (ok if k in j else bad)('logic判断 必需键 %s' % k)
if j.get('日期') != d:
    bad('日期≠%s' % d)
if j.get('路') != 'logic':
    bad('路≠logic')
jd = j['判断']
for k in ('结论', '证据', '档位', '置信度', '可证伪条件', '独立盲区声明'):
    (ok if k in jd else bad)('判断.必需键 %s' % k)
if jd.get('档位') not in ('A', 'B', 'C'):
    bad('档位非法=%s' % jd.get('档位'))
else:
    ok('档位=%s' % jd['档位'])
if not (isinstance(jd.get('置信度'), int) and 0 <= jd['置信度'] <= 100):
    bad('置信度非法=%r' % jd.get('置信度'))
else:
    ok('置信度=%d' % jd['置信度'])
if not (isinstance(jd.get('证据'), list) and len(jd['证据']) >= 3):
    bad('证据条数<3')
else:
    ok('证据 %d 条' % len(jd['证据']))
for k in ('可证伪条件', '独立盲区声明'):
    if not (isinstance(jd.get(k), str) and len(jd[k]) > 50):
        bad('%s 过短' % k)
    else:
        ok('%s %d 字' % (k, len(jd[k])))

# 荐票
rec = j['荐票']
for k in ('结论', '标的'):
    (ok if k in rec else bad)('荐票.必需键 %s' % k)
zt = {r['代码']: r for r in csv.DictReader(open(os.path.join(D, d, 'zt_pool.csv'), encoding='utf-8-sig'))}
items = rec['标的']
if len(items) > 3:
    bad('标的>3 (%d)' % len(items))
ok('标的 %d 只（荐票%d/观察%d）' % (len(items), sum(1 for x in items if x['类型'] == '荐票'),
                                  sum(1 for x in items if x['类型'] == '观察')))
for it in items:
    for k in ('代码', '名称', '类型', '历史对照', '理由'):
        if k not in it:
            bad('标的%s 缺键%s' % (it.get('代码'), k))
    if it.get('类型') not in ('荐票', '观察'):
        bad('标的%s 类型非法=%s' % (it['代码'], it.get('类型')))
    if it['代码'] not in zt:
        bad('标的%s 不在当日涨停池' % it['代码'])
    hc = it.get('历史对照', '')
    for tok in ('n=', '胜率', '均收'):
        if tok not in hc:
            bad('标的%s 历史对照缺「%s」' % (it['代码'], tok))
    if len(it.get('理由', '')) < 120:
        warn('标的%s 理由偏短(%d字)' % (it['代码'], len(it.get('理由', ''))))
ok('标的 5键齐全/类型合法/∈zt_pool/历史对照含n=胜率均收')

if len(j.get('认知迭代') or []) < 1:
    bad('认知迭代为空')
else:
    for c in j['认知迭代']:
        for k in ('标题', '正文', '可证伪条件'):
            if k not in c:
                bad('认知迭代缺键 %s' % k)
    ok('认知迭代 %d 条（标题/正文/可证伪齐全）' % len(j['认知迭代']))
if len(j.get('深挖') or []) < 1:
    bad('深挖为空')
else:
    ok('深挖 %d 条' % len(j['深挖']))
if not any('MA-20261020-05' in s for s in j['深挖']):
    bad('深挖未承接 MA-20261020-05')

# ---------- 2 交易计划 ----------
tp = json.load(open(os.path.join(L, '交易计划_logic_%s.json' % d), encoding='utf-8'))
ok('交易计划 JSON 解析通过')
for k in ('日期', '路', 'buys', 'sells', 'notes'):
    (ok if k in tp else bad)('交易计划 必需键 %s' % k)
if not (0 <= len(tp['buys']) <= 5):
    bad('buys 条数 %d 不在 0~5' % len(tp['buys']))
else:
    ok('buys %d 条' % len(tp['buys']))
for b in tp['buys']:
    for k in ('代码', '名称', '权重%', '理由'):
        if k not in b:
            bad('buys %s 缺键 %s' % (b.get('代码'), k))
state = json.load(open(os.path.join(L, '_模拟盘', 'logic', '状态.json'), encoding='utf-8'))
held = [x for x in (state.get('持仓') or []) if isinstance(x, dict)]
held_codes = [str(x.get('代码') or x.get('code')) for x in held]
blob = json.dumps(tp, ensure_ascii=False)
for c in held_codes:
    if c not in blob:
        bad('在持 %s 未在交易计划中表态（漏票）' % c)
    else:
        ok('在持 %s 已表态' % c)
if len(tp['buys']) == 0 and len(tp.get('notes', '')) < 100:
    bad('空仓但 notes 理由过短')
ok('空仓理由 %d 字' % len(tp.get('notes', '')))

# ---------- 3 能力回执 ----------
rc = json.load(open(os.path.join(L, '能力回执_logic_%s.json' % d), encoding='utf-8'))
ref = json.load(open(os.path.join(L, '能力回执_auction_%s.json' % d), encoding='utf-8'))
if list(rc.keys()) != list(ref.keys()):
    bad('回执键与auction不一致: %s vs %s' % (list(rc.keys()), list(ref.keys())))
else:
    ok('回执键与auction完全一致(8键)')
pre = json.load(open(os.path.join(L, '能力预加载_%s.json' % d), encoding='utf-8'))
lg = pre['routes']['logic']
n_elig = lg.get('eligible_count', 0)
if n_elig == 0:
    if rc['considered_ids'] or rc['applied'] or rc['rejected']:
        bad('eligible=0 但回执非空')
    if rc['status'] != 'no_eligible_capabilities':
        bad('eligible=0 但 status=%s' % rc['status'])
    else:
        ok('eligible=0 → status=no_eligible_capabilities，considered/applied/rejected 均空')
else:
    if len(rc['considered_ids']) != n_elig:
        bad('considered_ids(%d)≠eligible(%d)' % (len(rc['considered_ids']), n_elig))
    else:
        ok('considered_ids 覆盖全部 eligible(%d)' % n_elig)

# ---------- 4 HTML ----------
hp = os.path.join(L, 'logic_body_%s.html' % d)
h = open(hp, encoding='utf-8').read()
ok('body HTML 读取 %d bytes' % os.path.getsize(hp))
rp = importlib.import_module('review_pages')
kw = [k for k, _ in rp.HEADING_MAP['logic']]
h2s = re.findall(r'<h2>(.*?)</h2>', h, re.S)
if len(h2s) != 6:
    bad('h2 段数=%d ≠6' % len(h2s))
else:
    ok('h2 段数=6')
for t in h2s:
    txt = re.sub(r'<[^>]+>', '', t).strip()
    hit = [k for k in kw if k in txt]
    if not hit:
        bad('h2「%s」无 HEADING_MAP 关键词' % txt)
    else:
        ok('h2「%s」→ 关键词 %s' % (txt, hit[0]))
# div 配平
opens = len(re.findall(r'<div\b', h))
closes = len(re.findall(r'</div>', h))
(ok if opens == closes else bad)('div 配平 open=%d close=%d' % (opens, closes))
# 裸 null / None
for tok in ('>null<', '>None<', ' null ', ' None ', 'NaN', 'undefined'):
    if tok in h:
        bad('HTML 含裸标记 %r' % tok)
ok('无裸 null/None/NaN/undefined')
# 标签白名单
allowed = {"div", "span", "p", "b", "strong", "i", "em", "small", "br", "hr", "ul", "ol", "li", "table",
           "thead", "tbody", "tfoot", "tr", "th", "td", "details", "summary", "h1", "h2", "h3", "h4",
           "a", "pre", "code", "sup", "sub", "dl", "dt", "dd", "section", "article"}
used = set(x.lower() for x in re.findall(r'<\s*/?\s*([a-zA-Z0-9]+)', h))
bad_tags = used - allowed
(ok if not bad_tags else bad)('标签白名单检查 %s' % (('违规=' + str(bad_tags)) if bad_tags else 'passed'))
# 自闭合/未闭合粗检
for t in ('table', 'tr', 'td', 'th', 'p', 'b'):
    o = len(re.findall(r'<%s\b' % t, h))
    c = len(re.findall(r'</%s>' % t, h))
    if o != c:
        bad('标签 <%s> 未配平 %d/%d' % (t, o, c))
ok('table/tr/td/th/p/b 逐类配平')

# ---------- 4b 真实渲染器解析 ----------
from review_pages import _Tree
try:
    tree = _Tree(h).root
    cnt = [0]
    def _cnt(n):
        cnt[0] += 1
        for c in getattr(n, 'children', []):
            if not isinstance(c, str):
                _cnt(c)
    _cnt(tree)
    ok('review_pages._Tree 解析通过（%d 节点）' % cnt[0])
except Exception as exc:
    bad('review_pages._Tree 解析失败: %r' % exc)
# 标题归位（与 _body_import 同逻辑，None 即 raise）
secs = []
for t in h2s:
    label = re.sub(r'<[^>]+>', '', t).strip()
    m = next((sid for kw2, sid in rp.HEADING_MAP['logic'] if kw2 in label), None)
    if m is None:
        bad('标题未归位: %s' % label)
    secs.append(m)
if len(set(secs)) != len(secs):
    bad('六段归位有重复栏目: %s' % secs)
else:
    ok('六段归位唯一: %s' % ' → '.join(secs))

# ---------- 5 零后视镜 ----------
pat = re.compile(r'2026-1[12]-\d\d|20261[12]\d\d|2027')
for f in (p, os.path.join(L, '交易计划_logic_%s.json' % d), hp, os.path.join(L, '三季报临时池_%s.json' % d)):
    txt = open(f, encoding='utf-8').read()
    m = [x.group(0) for x in pat.finditer(txt)]
    if m:
        bad('%s 含未来日期 %s' % (os.path.basename(f), set(m[:5])))
ok('零后视镜：无 202612+ / 2027 日期')
if '2026-10-22' in open(os.path.join(L, '三季报临时池_%s.json' % d), encoding='utf-8').read():
    bad('三季报池含公告日 2026-10-22（后视镜）')

# ---------- 6 三季报池文件 ----------
q3 = json.load(open(os.path.join(L, '三季报临时池_%s.json' % d), encoding='utf-8'))
for k in ('池大小', '∩当日涨停_只数', '与中报池差异', '代码名单'):
    (ok if k in q3 else bad)('三季报池 键存在 %s' % k)
if q3['池大小'] != len(q3['代码名单']):
    bad('池大小与代码名单长度不一致')
ok('三季报池 池大小=%d ∩涨停=%d' % (q3['池大小'], q3['∩当日涨停_只数']))
mx = max([x['公告日期'] for x in q3['全部明细']])
if mx > '2026-10-21':
    bad('三季报池最新公告日 %s > 20261021' % mx)
else:
    ok('三季报池最新公告日=%s ≤20261021' % mx)

# ---------- 输出 ----------
print('=' * 62)
print('OK  %d 项' % len(oks))
for m in oks:
    print('  ✓', m)
if warns:
    print('WARN %d 项' % len(warns))
    for m in warns:
        print('  !', m)
print('FAIL %d 项' % len(fails))
for m in fails:
    print('  ✗', m)
print('=' * 62)
print('RESULT:', 'PASS' if not fails else 'FAIL')
sys.exit(0 if not fails else 1)
