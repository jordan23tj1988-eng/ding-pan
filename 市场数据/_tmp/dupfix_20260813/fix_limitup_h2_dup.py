# -*- coding: utf-8 -*-
"""2026-08-13 修复 limitup 板块一/二 h2 内嵌大块=双重渲染（用户截图: Top5 表重复）。
修法(8/12 契约修复同款): h2 整坨替换为标准模板; 权威源=judgment_{d}.json bodies.limitup,
同步 _学习/limitup_body_{d}.html(剥台账版)。负注入后重跑生成器+哨兵。
"""
import json, re, os, shutil, sys

L = r'D:\股票数据\市场数据'
XL = os.path.join(L, '_学习')

H2_STD = {
    '一 ': '<h2>一 涨停复盘 · Top5荐票<span class="hint">排序=命中规则数→抓龙率P(执2≥+8%)→质量分(P25负筛);发出版不可覆盖;桶均值非个股预言</span></h2>',
    '二 ': '<h2>二 市场温度 · 涨停生态<span class="hint">温度卡+档位成绩单+龙票规则榜/分板胜率库折叠(脚本产出勿改数)</span></h2>',
}
BAD_BLOCK = re.compile(r'<(table|div|ul|ol|p|details|svg|pre)\b')


def fix_h2(text, kw, tag):
    """把 <h2>{kw}... 到第一个 </h2> 整坨替换为标准模板。返回(新文本, 是否改动)。"""
    i = text.find('<h2>%s' % kw)
    if i < 0:
        return text, False
    e = text.find('</h2>', i)
    if e <= 0:
        return text, False
    seg = text[i:e + 5]
    if len(seg) > 4096:  # 防御: 异常超长不要吞掉后面的内容
        raise RuntimeError('%s h2 %s 超长 %d, 拒绝自动修复' % (tag, kw.strip(), len(seg)))
    return text[:i] + H2_STD[kw] + text[e + 5:], True


def main():
    dates = sys.argv[1:] or ['20260813']
    for d in dates:
        # 1) 权威源 judgment
        jp = os.path.join(XL, 'judgment_%s.json' % d)
        j = json.load(open(jp, encoding='utf-8'))
        b = j['bodies']['limitup']
        changed = []
        for kw in ('一 ', '二 '):
            nb, did = fix_h2(b, kw, 'judgment')
            if did:
                b = nb
                changed.append(kw.strip())
        j['bodies']['limitup'] = b
        json.dump(j, open(jp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('%s judgment bodies.limitup 修复 h2: %s (len %d)' % (d, changed, len(b)))

        # 2) 同步剥台账版 body 文件
        bp = os.path.join(XL, 'limitup_body_%s.html' % d)
        if os.path.exists(bp):
            h = open(bp, encoding='utf-8').read()
            ch2 = []
            for kw in ('一 ', '二 '):
                nh, did = fix_h2(h, kw, 'body文件')
                if did:
                    h = nh
                    ch2.append(kw.strip())
            open(bp, 'w', encoding='utf-8').write(h)
            print('%s limitup_body 修复 h2: %s (len %d)' % (d, ch2, len(h)))

        # 3) 验证: 修复后 h2 一/二 提取长度 < 2KB 且无块级标签
        for kw in ('一 ', '二 '):
            i = b.find('<h2>%s' % kw)
            e = b.find('</h2>', i)
            seg = b[i:e + 5]
            assert len(seg) < 2048, '%s h2 %s 仍 >2KB: %d' % (d, kw.strip(), len(seg))
            assert not BAD_BLOCK.search(seg), '%s h2 %s 仍含块级标签' % (d, kw.strip())
        print('%s 验证 PASS: h2 一/二 均 <2KB 且无块级标签' % d)


if __name__ == '__main__':
    main()
