CAPABILITY_ROUTES = ('index', 'cycle', 'auction', 'lhb', 'theme', 'logic', 'limitup')
# 各页"业务段"数；两块标准能力模块顺延为 业务段+1 / +2。与实际页面不符即报错，防编号漂移。
CAPABILITY_BUSINESS_SECTIONS = {'index': 6, 'cycle': 5, 'auction': 4, 'lhb': 4,
                                'theme': 3, 'logic': 5, 'limitup': 4}
CAPABILITY_SYNC_START = '<!--OVERVIEW_EVOLUTION_SYNC_START-->'
CAPABILITY_SYNC_END = '<!--OVERVIEW_EVOLUTION_SYNC_END-->'
_CAPABILITY_CN = '一二三四五六七八九十'
# 展示层历史模块标题(自主深挖/我的认知迭代)；内容保留在判断层与能力库，仅展示层摘除。
_LEGACY_MODULE_RE = re.compile(r'自主深挖|我的认知迭代|认知迭代')
_CAPABILITY_STYLE_RE = re.compile(
    r'<style\b[^>]*\bid=["\'](?:overview-evolution-sync|evolution-style-sync)["\'][^>]*>.*?</style\s*>',
    re.S | re.I)
_CAPABILITY_STYLE_SELFCLOSE_RE = re.compile(
    r'<style\b[^>]*\bid=["\'](?:overview-evolution-sync|evolution-style-sync)["\'][^>]*/>',
    re.S | re.I)


def _capability_module():
    """加载两块标准能力模块的唯一真源(能力进化模块.py)。"""
    import importlib.util
    path = Path(BASE) / '能力进化模块.py'
    if not path.is_file():
        raise RuntimeError('能力进化模块.py 缺失，无法生成标准能力模块')
    spec = importlib.util.spec_from_file_location('capability_module_source', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _legacy_module_headings(html):
    """返回展示层历史『自主深挖 / 我的认知迭代』标题(已排除两块标准能力模块)。"""
    body = re.sub(r'<section class="evolution">.*?</section>', '', html, flags=re.S)
    return [re.sub(r'<[^>]+>', '', m.group(1)).strip()
            for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', body, re.S)
            if _LEGACY_MODULE_RE.search(re.sub(r'<[^>]+>', '', m.group(1)))]


def _strip_legacy_modules(html):
    """摘除展示层历史模块段(从标题到下一标题/foot 之前)，返回 (html, 摘除数)。

    2026-09-22：与主题页/周期页/龙虎榜页同一口径——展示层只留两块标准能力模块，
    旧『六 自主深挖 · …』『七 我的认知迭代 · 最新』不再与标准模块并存。
    这些段落的正文仍在判断层(model)与能力库中，未被删除，只是不再重复展示。
    """
    removed = 0
    while True:
        target = None
        for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.S):
            if _LEGACY_MODULE_RE.search(re.sub(r'<[^>]+>', '', m.group(1))):
                target = m
                break
        if target is None:
            return html, removed
        ends = [x for x in (html.find('<h2', target.end()),
                            html.find('<section class="evolution">', target.end()),
                            html.find('<div class="foot">', target.end())) if x >= 0]
        end = min(ends) if ends else len(html)
        html = html[:target.start()].rstrip('\n') + '\n' + html[end:].lstrip('\n')
        removed += 1


def _sync_capability_blocks(site_dir, date, routes=CAPABILITY_ROUTES):
    """五路 + 概览统一为同一套两块标准能力模块(唯一真源=能力进化模块.py 直出当日能力库)。

    2026-09-22 用户指令修复：「自主拓展 · 能力进化」「认知迭代 · 能力进化」是每一路与概览
    都该有的公共能力，但历史实现只同步主题页 → 概览/竞价/产业逻辑/涨停页长期缺块，
    龙虎榜页与旧模块并存；且搬运的是页面里冻结的旧字节，数字与当日能力库脱节。现改为：
      1) 唯一来源=当日能力库(快照 + 账本)直出，不从任何页面搬运；
      2) 目标=七页全覆盖(index + 五路)，缺页即报错；
      3) 展示层旧模块按主题页已验收口径摘除，不并存；
      4) 编号按各页业务段数顺延，与契约段数不符即报错(防编号漂移)；
      5) 幂等：重跑先清旧块/旧样式，再注入同一份字节。
    """
    site = Path(site_dir).resolve()
    mod = _capability_module()
    payload = mod.build(BASE, date)
    sections, css = payload['sections'], payload['css']
    if len(sections) != 2 or not css:
        raise RuntimeError('能力模块产出异常: sections=%d css=%d' % (len(sections), len(css)))
    style = '<style id="overview-evolution-sync">' + css + '</style>'
    report = []
    for route in routes:
        path = site / (route + '.html')
        if not path.is_file():
            raise RuntimeError('能力模块统一目标缺页: ' + str(path))
        s = path.read_text(encoding='utf-8')
        s = re.sub(r'\n*' + re.escape(CAPABILITY_SYNC_START) + r'.*?' + re.escape(CAPABILITY_SYNC_END) + r'\n*',
                   '\n', s, flags=re.S)
        s = re.sub(r'<section class="evolution">.*?</section>\s*', '', s, flags=re.S)
        s = _CAPABILITY_STYLE_RE.sub('', s)
        s = _CAPABILITY_STYLE_SELFCLOSE_RE.sub('', s)
        s, removed = _strip_legacy_modules(s)
        nums = [_CAPABILITY_CN.index(x) + 1
                for x in re.findall(r'<h2[^>]*>\s*([一二三四五六七八九十])\s', s)]
        expected = CAPABILITY_BUSINESS_SECTIONS[route]
        if not nums or max(nums) != expected:
            raise RuntimeError('页面业务段数与契约不符，拒绝注入能力模块: %s (max=%s expect=%d)'
                               % (path.name, max(nums) if nums else None, expected))
        start = expected + 1
        local = [mod.renumber(sec, start + i) for i, sec in enumerate(sections)]
        s = s.replace('</head>', style + '</head>', 1)
        pos = s.rfind('<div class="foot">')
        if pos < 0:
            raise RuntimeError('page foot anchor missing: ' + str(path))
        block = ('\n\n' + CAPABILITY_SYNC_START + '\n' + local[0] + '\n' + local[1] + '\n'
                 + CAPABILITY_SYNC_END + '\n')
        s = s[:pos].rstrip('\n') + block + s[pos:]
        left = _legacy_module_headings(s)
        if (s.count('<section class="evolution"') != 2
                or s.count(CAPABILITY_SYNC_START) != 1 or s.count(CAPABILITY_SYNC_END) != 1
                or len(re.findall(r'<style\b[^>]*\bid=["\']overview-evolution-sync["\']', s, flags=re.I)) != 1
                or left
                or s.find(CAPABILITY_SYNC_END) > s.find('<div class="foot">')):
            raise RuntimeError('能力模块注入自检失败: %s (残留旧标题=%s)' % (path, left))
        path.write_text(s, encoding='utf-8', newline='\n')
        report.append('%s(%s/%s%s)' % (path.name, _CAPABILITY_CN[start - 1], _CAPABILITY_CN[start],
                                       '，清旧%d' % removed if removed else ''))
    return report
