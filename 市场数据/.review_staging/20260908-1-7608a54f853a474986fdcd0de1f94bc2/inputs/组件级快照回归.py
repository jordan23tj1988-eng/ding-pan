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
MODS = {
    'limitup': ('组件快照_limitup.json', PAGES_LIMITUP, 'module_render_limitup'),
    'lhb':     ('组件快照_lhb.json',     PAGES_LHB,     'module_render_lhb'),
    'auction': ('组件快照_auction.json', PAGES_AUCTION, 'module_render_auction'),
    'logic':   ('组件快照_logic.json',   PAGES_LOGIC,   'module_render_logic'),
}

def _cfg():
    """按 --lhb/--limitup/--auction/--logic 参数选配置(默认 limitup)"""
    page = ('logic' if '--logic' in sys.argv else
            'auction' if '--auction' in sys.argv else
            'lhb' if '--lhb' in sys.argv else 'limitup')
    snap_f, pages, mod = MODS[page]
    return os.path.join(SNAP_DIR, snap_f), pages, mod, page

def _load_module(mod):
    sys.path.insert(0, ROOT)
    import importlib
    return importlib.import_module(mod)

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
    M = _load_module(mod)
    comps = M.build_components(BASE_DATE)
    out = {'基准日': BASE_DATE, '页面': page, '组件': {}}
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
    M = _load_module(mod)
    comps = M.build_components(BASE_DATE)
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
    assert _content(t) != _content(c1), '负面自测2b失败: 文本数字改应动content'
    print('负面自测2 ✓ 篡改%s文本数字 → tagsig不变 content变' % pages[0])
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
    else: print('用法: init|check|selftest [--lhb|--limitup]')
