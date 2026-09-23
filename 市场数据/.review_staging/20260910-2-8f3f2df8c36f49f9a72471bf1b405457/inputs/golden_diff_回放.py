# -*- coding: utf-8 -*-
"""golden diff 回放 —— 模板回归检测(2026-08-12 历史遗留小项4)

原理: 当前盯盘台 limitup.html 与黄金对照版717 对比**壳子部分**(head/CSS/nav/foot 静态模板),
      数据区(bodies body)每日变化不参与对比 —— 壳子逐字节一致 = 模板无回归。
用法: python golden_diff_回放.py           # 对比当前生成 vs 黄金版, 输出报告
      python golden_diff_回放.py --regen   # 先重新生成盯盘台再对比
      python golden_diff_回放.py --quiet   # 一致时静默(供cron/门禁用)
退出码: 0=壳子一致(模板无回归), 1=壳子有差异(模板被改坏), 2=数据缺失/异常
"""
import os, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
GOLD = r'D:\黄金对照版717\limitup.html'
CUR = os.path.join(BASE, '复盘', '盯盘台', 'limitup.html')


def _norm(s):
    """归一化: ①CRLF→LF(防御旧产物) ②nav更新时间戳→占位(每日数据)"""
    s = s.replace('\r\n', '\n')
    import re as _re
    s = _re.sub(r'更新[^<]*</span>', '更新{TS}</span>', s)
    return s


def _shell(html):
    """提取壳子: head到hero前(排除数据区hero) + foot区之后(静态模板, 不含数据)"""
    # 数据区起点=wrap(ticker/hero/body全在wrap内); 壳子head=wrap前(head+CSS+nav静态)
    i_wrap = html.find('<div class="wrap">')
    i_h2 = html.find('<h2>')
    i_hero = html.find('<div class="hero">')
    i_bodystart = html.find('<body')
    i_bodyend = html.find('</body>')
    if i_h2 < 0 or i_bodystart < 0 or i_bodyend < 0:
        return None
    cut = i_wrap if 0 < i_wrap < i_h2 else (i_hero if 0 < i_hero < i_h2 else i_h2)
    head = html[:cut]  # head + CSS + nav(静态模板)
    i_last_h2 = html.rfind('<h2>')
    tail_from = html.find('<div class="foot">', i_last_h2)
    if tail_from < 0:
        tail_from = i_bodyend
    tail = html[tail_from:]  # foot/script/闭合标签
    return head + '\n<<<BODY>>>\n' + tail


def main():
    regen = '--regen' in sys.argv
    quiet = '--quiet' in sys.argv
    if regen:
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(BASE, '生成盯盘台.py')])
        if r.returncode != 0:
            print('[golden diff] 重新生成失败 rc=%d' % r.returncode)
            return 2
    if not os.path.isfile(GOLD):
        print('[golden diff] 黄金版缺失: %s' % GOLD)
        return 2
    if not os.path.isfile(CUR):
        print('[golden diff] 当前页缺失: %s' % CUR)
        return 2
    gold = _norm(open(GOLD, encoding='utf-8', errors='replace').read())
    cur = _norm(open(CUR, encoding='utf-8', errors='replace').read())
    gs, cs = _shell(gold), _shell(cur)
    if gs is None or cs is None:
        print('[golden diff] 壳子提取失败(锚点缺失)')
        return 2
    if gs == cs:
        if not quiet:
            print('[golden diff] PASS 壳子逐字节一致 (模板无回归, %d chars)' % len(gs))
        return 0
    # 逐行定位差异
    gl, cl = gs.split('\n'), cs.split('\n')
    diffs = 0
    for i in range(max(len(gl), len(cl))):
        a = gl[i] if i < len(gl) else '<EOF>'
        b = cl[i] if i < len(cl) else '<EOF>'
        if a != b:
            diffs += 1
            if diffs <= 6:
                print('  L%d:\n    黄金: %s\n    当前: %s' % (i + 1, a[:110], b[:110]))
    print('[golden diff] FAIL 壳子有 %d 处差异 (模板回归! 检查渲染器改动)' % diffs)
    return 1


if __name__ == '__main__':
    sys.exit(main())
