# -*- coding: utf-8 -*-
"""组件级快照回归 (S3, 2026-08-11)
原理: 结构层(tagsig) 与 内容层(content) 分离哈希
  - tagsig  = 剥离文本节点后的 标签+class+属性 序列哈希 → 结构指纹, 每日应不变
  - content = 文本节点哈希 → 内容指纹, 不参与结构对比(每日注入只改内容)
快照库: _架构/组件快照_limitup.json
用法:
  python 组件级快照回归.py init        # 基准快照落库(覆盖旧库, 显式)
  python 组件级快照回归.py check       # 对比当前渲染 vs 快照
  python 组件级快照回归.py selftest    # 负面自测: 篡改C1.2只变C1.2; 改内容数字不变tagsig
"""
import sys, os, json, hashlib, re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(ROOT, '_架构')
BASE_DATE = '20260716'          # 基准日 = 黄金版同日数据
PAGES_LIMITUP = ['C1.1', 'C1.2', 'C2', 'C3', 'C4.1', 'C5.1', 'C5.2', 'C6.1']
PAGES_LHB = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
PAGES_AUCTION = ['C1', 'C2', 'C3']
PAGES_LOGIC = ['C1', 'C2', 'C3']
# 概览页黄金骨架(2026-09-23 用户拍板): 段序/模板结构冻结, 内容随复盘日变。
# 基准日固定=黄金基准 20260716, 骨架由 module_golden_index 直出, 页面模型来自 review_pages。
PAGES_INDEX = ['recommendations', 'turning', 'routes', 'verdict']
MODS = {
    'index':   ('组件快照_index.json',   PAGES_INDEX,   None),
    'limitup': ('组件快照_limitup.json', PAGES_LIMITUP, 'module_render_limitup'),
    'lhb':     ('组件快照_lhb.json',     PAGES_LHB,     'module_render_lhb'),
    'auction': ('组件快照_auction.json', PAGES_AUCTION, 'module_render_auction'),
    'logic':   ('组件快照_logic.json',   PAGES_LOGIC,   'module_render_logic'),
}

def _cfg():
    """按 --lhb/--limitup/--auction/--logic 参数选配置(默认 limitup)"""
    page = ('index' if '--index' in sys.argv else
            'logic' if '--logic' in sys.argv else
            'auction' if '--auction' in sys.argv else
            'lhb' if '--lhb' in sys.argv else 'limitup')
    snap_f, pages, mod = MODS[page]
    return os.path.join(SNAP_DIR, snap_f), pages, mod, page

def _load_module(mod):
    sys.path.insert(0, ROOT)
    import importlib
    return importlib.import_module(mod)

def _fixture_model():
    """概览黄金骨架合成样本(固定假数据, 覆盖 .obs/.rt/.hb/裁决卡全分支)。

    目的: 快照只锁"模板结构", 与当日真实数据完全解耦——数据天天变(候选数/档位/数值),
    模板结构必须一变就报。真实数据侧的漂移由哨兵 C15 每日在实页上兜。
    """
    ROUTES = ['竞价·时机', '席位·资金', '题材·情绪', '产业·逻辑', '质量·高度']
    GRADES = ['A', 'B', 'C', 'B', 'A']
    claims = []
    for i, (rn, g) in enumerate(zip(ROUTES, GRADES)):
        for k, v in (('路', rn), ('档位', g), ('置信度', str(50 + i)),
                     ('裁决理由', '样本裁决理由第%d路' % i), ('裁决', '采纳'),
                     ('荐票核验', '样本核对第%d路' % i)):
            claims.append({'id': 'fx-r%d-%s' % (i, k), 'role': 'verdict', 'section': 'routes',
                           'source_pointer': '/五路裁决/%d/%s' % (i, k), 'text': v})
    for k, v in (('档位', 'B'), ('结论', '样本总裁决结论'), ('置信度', '66'), ('分歧裁决', '样本分歧裁决')):
        claims.append({'id': 'fx-v-' + k, 'role': 'verdict', 'section': 'verdict',
                       'source_pointer': '/总裁决/' + k, 'text': v})
    for i in range(3):
        claims.append({'id': 'fx-vp%d' % i, 'role': 'verdict', 'section': 'verdict',
                       'source_pointer': '/总裁决/次日验证点/%d' % i, 'text': '样本次日验证点%d' % i})
    claims.append({'id': 'fx-env', 'role': 'env', 'section': 'turning',
                   'source_pointer': '/环境加权依据', 'text': '样本环境加权依据'})
    rows = ''
    for i in range(5):
        rows += ('<tr><td>%d</td><td style="white-space:nowrap"><b>样本股%d</b><br><span class="mut">00000%d</span></td>'
                 '<td style="white-space:nowrap"><b>%d</b><br><span class="mut">位置分%d</span></td>'
                 '<td>①竞价 #%d 竞价分5%d.0 · 高开·2板 · 首封09:2%d</td>'
                 '<td>①竞价 高开0~5%% +0.5%d%%/5%d%%(n=30)</td><td>样本题材·样本细分</td></tr>'
                 % (i + 1, i + 1, i + 1, 5 - i, 10 - i, i + 1, i, i, i, i))
    crosspick = ('<div class="hint">★筛选口径: 样本(合成)</div><div class="card"><table>'
                 '<tr><th>#</th><th>个股</th><th>共振</th><th>来源路核心指标与判据</th><th>执行口径</th><th>题材/归位</th></tr>'
                 + rows + '</table></div>')
    return {'d': '20990101', 'route': 'index', 'status': 'ok', 'errors': [], 'sections': [],
            'kpis': [], 'hero': {}, 'claims': claims,
            'components': [
                {'id': 'CROSSPICK', 'status': 'ok', 'html': crosspick, 'sources': []},
                {'id': 'IDXLEAD', 'status': 'ok', 'html': '<span class="pill">样本先行指标</span>', 'sources': []},
                {'id': 'ENGINEBOOKS', 'status': 'ok', 'html': '<div class="rowE"><div class="card"><h3>六账本 · 当日引擎净值</h3>'
                 + ''.join('<div class="hb"><span class="hbl">%s</span><div class="hbt"><i class="hbi" style="width:50%%"></i></div>'
                           '<b class="hbv">+1.0%%</b></div>' % n for n in ['竞价', '席位', '题材', '产业', '质量', '综合'])
                 + '</div></div>', 'sources': []},
            ]}


def _components(page, mod, date):
    """取当日组件集: 概览页=黄金骨架四段(module_golden_index); 其余页=module_render_*。"""
    if page == 'index':
        import importlib
        sys.path.insert(0, ROOT)
        gi = importlib.import_module('module_golden_index')
        return {k: v.replace('<!--GOLDEN-INDEX:%s-->' % k, '').replace('<!--/GOLDEN-INDEX:%s-->' % k, '')
                for k, v in gi.build(_fixture_model(), date).items()}
    M = _load_module(mod)
    return M.build_components(date)

class _TagSig(HTMLParser):
    """收集标签+属性签名序列(忽略文本节点)"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sig = []
    def handle_starttag(self, tag, attrs):
        a = ' '.join('%s=%s' % (k, v) for k, v in attrs)
        self.sig.append('<%s %s>' % (tag, a))
    def handle_endtag(self, tag):
        self.sig.append('</%s>' % tag)
    def handle_startendtag(self, tag, attrs):
        a = ' '.join('%s=%s' % (k, v) for k, v in attrs)
        self.sig.append('<%s %s/>' % (tag, a))

def _tagsig(html):
    p = _TagSig()
    try:
        p.feed(html)
    except Exception:
        pass
    return hashlib.sha256('|'.join(p.sig).encode('utf-8')).hexdigest()

def _content(html):
    """文本节点(去标签后) — 内容指纹"""
    txt = re.sub(r'<[^>]+>', '', html)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return hashlib.sha256(txt.encode('utf-8')).hexdigest()

def _snapshot():
    snap, pages, mod, page = _cfg()
    comps = _components(page, mod, BASE_DATE)
    out = {'基准日': BASE_DATE, '页面': page, '说明': 'tagsig=模板结构指纹(结构变了必报); content=内容指纹(随复盘日变)',
           '组件': {}}
    for k in pages:
        v = comps.get(k, '')
        out['组件'][k] = {'tagsig': _tagsig(v), 'content': _content(v), 'bytes': len(v)}
    return out

def init():
    os.makedirs(SNAP_DIR, exist_ok=True)
    snap, pages, mod, page = _cfg()
    s = _snapshot()
    with open(snap, 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    print('快照已落库: %s (%s)' % (snap, page))
    for k, v in s['组件'].items():
        print('  %s tagsig=%s.. content=%s.. (%d B)' % (k, v['tagsig'][:12], v['content'][:12], v['bytes']))
    return s

def check(verbose=True):
    snap, pages, mod, page = _cfg()
    if not os.path.exists(snap):
        print('!无快照库(%s), 先跑 init --%s' % (snap, page)); return 1
    old = json.load(open(snap, encoding='utf-8'))
    cur = _snapshot()
    bad = []
    for k in pages:
        o, c = old['组件'].get(k), cur['组件'].get(k)
        if o is None or c is None:
            bad.append((k, '缺组件')); continue
        if o['tagsig'] != c['tagsig']:
            bad.append((k, 'STRUCTURE 变了'))
        elif verbose:
            print('  %s 结构稳定 ✓ (content %s)' % (k, '变' if o['content'] != c['content'] else '不变'))
    if bad:
        print('!!结构变化组件:'); 
        for k, why in bad: print('   %s: %s' % (k, why))
        return 1
    print('全部组件结构稳定 ✓ 隔离性成立 (%s)' % page)
    return 0

class _TextOnlyReplace(HTMLParser):
    """仅替换文本节点中的数据(不碰标签/属性) — 属性数字(如 style="left:68.5%")不算结构变"""
    def __init__(self, pat, repl):
        super().__init__(convert_charrefs=True)
        self.pat, self.repl, self.out = pat, repl, []
    def handle_data(self, data):
        self.out.append(re.sub(self.pat, self.repl, data))
    def _tag(self, tag, attrs, selfclose):
        a = ' '.join('%s="%s"' % (k, v) for k, v in attrs)
        return '<%s %s%s>' % (tag, a, '/>' if selfclose else '')
    def handle_starttag(self, tag, attrs):
        self.out.append(self._tag(tag, attrs, False))
    def handle_endtag(self, tag):
        self.out.append('</%s>' % tag)
    def handle_startendtag(self, tag, attrs):
        self.out.append(self._tag(tag, attrs, True))

def selftest():
    """负面自测: 篡改 C4 → 只 C4 变; 篡改 C1 文本数字 → tagsig 不变 content 变"""
    snap, pages, mod, page = _cfg()
    comps = _components(page, mod, BASE_DATE)
    orig = {k: comps.get(k, '') for k in pages}
    # 1) 篡改最后一个组件结构(加真实元素, 注释不收集故不用<!--X-->)
    last_k = pages[-1]
    comps[last_k] = comps[last_k] + '<b>X</b>'
    changed = [k for k in pages if _tagsig(comps[k]) != _tagsig(orig[k])]
    assert changed == [last_k], '负面自测1失败: 应只%s变, 实际 %s' % (last_k, changed)
    print('负面自测1 ✓ 篡改%s结构 → 仅%s变 (%s)' % (last_k, last_k, changed))
    # 2) 篡改首个组件文本数字(不改标签/属性) — 属性内数字(style="left:..%")不算结构变
    c1 = orig[pages[0]]
    rp = _TextOnlyReplace(r'\d+\.\d+%', '9.99%')
    rp.feed(c1)
    t = ''.join(rp.out)
    assert _tagsig(t) == _tagsig(c1), '负面自测2a失败: 文本数字改不应动tagsig'
    txt = re.sub(r'<[^>]+>', '', c1)
    if re.search(r'\d+\.\d+%', txt):
        assert _content(t) != _content(c1), '负面自测2b失败: 文本数字改应动content'
        print('负面自测2 ✓ 篡改%s文本数字 → tagsig不变 content变' % pages[0])
    else:
        print('负面自测2 - %s样本无百分比文本, 跳过内容指纹断言' % pages[0])
    # 3) 空白/换行变化不影响结构
    w = re.sub(r'\n+', '\n', c1)
    assert _tagsig(w) == _tagsig(c1), '负面自测3失败: 空白归并不应动tagsig'
    print('负面自测3 ✓ 换行归并 → tagsig不变')
    print('全部负面自测通过 ✓ (%s)' % page)

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'check'
    if cmd == 'init': init()
    elif cmd == 'check': sys.exit(check())
    elif cmd == 'selftest': selftest()
    else: print('用法: init|check|selftest [--index|--lhb|--limitup|--auction|--logic]')
