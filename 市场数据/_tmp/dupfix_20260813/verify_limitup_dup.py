# -*- coding: utf-8 -*-
"""2026-08-13 limitup 双重渲染修复验收:
1) 6个h2提取长度全<2KB且无块级元素  2) 板块一内荐票表唯一
3) 关键数字(执1 40.7%/-0.52%)全页仅1次(修复前=2)  4) 板块二h2内无温度kv
用法: python verify_limitup_dup.py 20260813
"""
import re, sys

BASE = r'D:\股票数据\市场数据\复盘\盯盘台'
BAD_BLOCK = re.compile(r'<(table|div|ul|ol|p|details|svg|pre)\b')


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '20260813'
    h = open(rf'{BASE}\limitup.html', encoding='utf-8').read()
    fails = []

    # 1) h2 结构
    hs = [(m.group(0), m.start()) for m in re.finditer(r'<h2[^>]*>', h)]
    for seg, pos in hs:
        e = h.find('</h2>', pos)
        full = h[pos:e + 5]
        if len(full) >= 2048:
            fails.append(f'h2@{pos} 长度 {len(full)} >= 2KB')
        if BAD_BLOCK.search(full):
            fails.append(f'h2@{pos} 内嵌块级元素: {BAD_BLOCK.search(full).group(1)}')
    print(f'h2 总数={len(hs)}, 全部<2KB且无块级元素: {"PASS" if not any("h2@" in f for f in fails) else "FAIL"}')

    # 2) 板块一内荐票表唯一
    b1 = h[h.find('<h2>一'):h.find('<h2>二')]
    n_table = b1.count('<table')
    n_th = b1.count('命中规则(规则榜)')
    n_mini = b1.count('执1胜率/均涨')  # 坏h2小表特有表头
    if n_table != 1: fails.append(f'板块一 <table> 出现 {n_table} 次(应1)')
    if n_th != 1: fails.append(f'板块一 荐票表头 {n_th} 次(应1)')
    if n_mini != 0: fails.append(f'板块一 h2小表表头残留 {n_mini} 次(应0)')
    print(f'板块一: table={n_table} 荐票表头={n_th} h2小表表头={n_mini}')

    # 3) 板块一内关键数字仅1次 (修复前: h2小表+荐票卡=2; 台账/深挖引用为合法, 不在此区)
    for key in ['40.7%/-0.52', '42.9%/-0.30', '43.5%/-0.33', '17.8%', '15.9%']:
        c = b1.count(key)
        if c != 1: fails.append(f'板块一关键串[{key}] 出现 {c} 次(应1)')
    print('板块一关键数字出现次数: ', {k: b1.count(k) for k in ['40.7%/-0.52', '42.9%/-0.30', '43.5%/-0.33', '17.8%', '15.9%']})

    # 4) 板块二 h2 内无温度 kv
    b2 = h[h.find('<h2>二'):h.find('<h2>三')]
    i_h2_2_end = h.find('</h2>', h.find('<h2>二'))
    h2_2 = h[h.find('<h2>二'):i_h2_2_end + 5]
    n_kv_h2 = h2_2.count('class="kv"')
    if n_kv_h2 != 0: fails.append(f'h2二内 kv 残留 {n_kv_h2} 个(应0)')
    # 温度数字在机器卡仍在(只应有1处 40.1 带 kv 结构)
    n_kv_b2 = b2.count('class="kv"')
    print(f'板块二: h2内kv={n_kv_h2}, 板块二全区kv={n_kv_b2}(机器温度卡)')

    # 5) 温度数字唯一性: ">40.1<" 之类出现在 h2 二里(kv l/v 结构), 修后 kv 只在机器卡
    c40 = b2.count('40.1')
    print(f'板块二内 "40.1" 出现 {c40} 次')

    if fails:
        print('=== FAIL ===')
        for f in fails:
            print('  ✗', f)
        return 1
    print('=== 全部断言 PASS ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
