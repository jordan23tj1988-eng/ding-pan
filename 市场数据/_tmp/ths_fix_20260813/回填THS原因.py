# -*- coding: utf-8 -*-
"""回填THS涨停原因(通用版): 题材归位里"XX(THS原因缺,行业兜底)"催化字段
→ "{THS limit_up_reason}(THS)"。大方向/环节/来源档=agent判断保留不动。
北交所票(THS涨停池不含30%涨停制)改口径标注"THS池不含北交所", 不编造原因。
用法: python 回填THS原因.py YYYYMMDD  (改前自动备份)
"""
import json, os, sys, shutil

BASE = r'D:\股票数据\市场数据'
L = os.path.join(BASE, '_学习')

sys.stdout.reconfigure(encoding='utf-8')

def main():
    D = sys.argv[1]
    pool = json.load(open(os.path.join(L, f'THS涨停池_{D}.json'), encoding='utf-8'))
    reason = {x['ticker']: (x.get('limit_up_reason') or '').strip() for x in pool}

    rp = os.path.join(L, f'题材归位_{D}.json')
    bak = rp + '.bak_th前'
    shutil.copy(rp, bak)
    j = json.load(open(rp, encoding='utf-8'))
    m = j['映射']

    done, bj_no_th, no_match, unchanged = [], [], [], []
    for code, v in m.items():
        cat = v.get('催化', '')
        if 'THS原因缺' not in cat:
            unchanged.append(code)
            continue
        r = reason.get(code)
        if not r:
            if code.startswith(('92', '83', '43', '87', '82')):
                # 北交所: THS涨停池口径不含, 诚实标注
                v['催化'] = cat.replace('THS原因缺,行业兜底', 'THS池不含北交所,行业兜底')
                bj_no_th.append((code, v.get('大方向', '?')))
                continue
            no_match.append((code, cat[:40]))
            continue
        v['催化'] = r + '(THS)'
        done.append((code, v.get('大方向', '?'), r))

    json.dump(j, open(rp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print(f'回填 {len(done)} 只 | 北交所改口径 {len(bj_no_th)} | 无匹配 {len(no_match)} | 不动 {len(unchanged)}')
    for code, d, r in done[:5]:
        print(f'  {code} [{d}] → {r}')
    if len(done) > 5:
        print(f'  ... 共{len(done)}只')
    for code, d in bj_no_th:
        print(f'  [北交所] {code} [{d}] 改口径标注')
    for code, c in no_match:
        print(f'  [无匹配] {code}: {c}')
    print(f'备份: {bak}')

if __name__ == '__main__':
    main()
