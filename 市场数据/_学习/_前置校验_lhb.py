# -*- coding: utf-8 -*-
"""lhb 判断前置文件存在性校验（承接 Master 指派 MA-20261104-05 ③）

背景：20261104 的判断里报过「战绩画像_lhb_20261104.json 缺件」，实测该文件存在
（5821 字节、mtime 11-04），属误报。此后写判断前必须先跑本脚本，缺件只允许
以本脚本的输出为依据声明，不得凭印象写「缺件」。

用法：python _学习/_前置校验_lhb.py 20261105
输出：_学习/_前置校验_lhb_{d}.json（存在性/大小/mtime/sha256/可解析）
"""
import hashlib
import json
import os
import sys

ROOT = r'D:/股票数据/市场数据'
os.chdir(ROOT)

TEMPLATE = [
    ('五件套清单', '_学习/子agent增强/_五件套清单_{d}.md'),
    ('战绩画像', '_学习/子agent增强/战绩画像_lhb_{d}.json'),
    ('认知库', '_学习/_认知库_lhb.json'),
    ('方法底座', '_agent规格/09_席位命门agent.md'),
    ('席位动向', '_学习/_席位动向/{d}.csv'),
    ('机器荐票卡', '_学习/席位荐票_{d}.json'),
    ('资金结构分', '_学习/资金结构分_{d}.json'),
    ('当日龙虎榜', '{d}/lhb.csv'),
    ('涨停池', '{d}/zt_pool.csv'),
    ('双源校验', '_学习/龙虎榜双源校验_{d}.json'),
    ('席位分档', '_学习/_席位分档.json'),
    ('席位胜率快照', '_学习/席位胜率快照.jsonl'),
    ('昨日总审', '_学习/总审_{prev}.json'),
    ('能力预加载', '_学习/能力预加载_{d}.json'),
    ('模拟盘状态', '_学习/_模拟盘/lhb/状态.json'),
    ('昨日判断', '_学习/lhb判断_{prev}.json'),
]


def main():
    d = sys.argv[1]
    prev = sys.argv[2] if len(sys.argv) > 2 else None
    if prev is None:
        # 上一交易日：从 _学习/_席位动向 里取小于 d 的最大日期，退化为自然日-1
        cands = sorted(x[:-4] for x in os.listdir('_学习/_席位动向') if x.endswith('.csv'))
        cands = [c for c in cands if c < d]
        prev = cands[-1] if cands else ''
    rows, miss = [], []
    for name, tpl in TEMPLATE:
        p = tpl.format(d=d, prev=prev)
        e = os.path.exists(p)
        rec = {'项': name, '路径': p, '存在': e}
        if e:
            b = open(p, 'rb').read()
            rec.update({'字节': len(b), 'mtime': __import__('time').strftime(
                '%Y-%m-%d %H:%M', __import__('time').localtime(os.path.getmtime(p))),
                'sha256': hashlib.sha256(b).hexdigest()[:16]})
            if p.endswith(('.json', '.jsonl')):
                try:
                    if p.endswith('.jsonl'):
                        [json.loads(x) for x in b.decode('utf-8').splitlines() if x.strip()]
                    else:
                        json.loads(b.decode('utf-8-sig'))
                    rec['可解析'] = True
                except Exception as ex:
                    rec['可解析'] = False
                    rec['解析错误'] = str(ex)[:120]
        else:
            miss.append(name)
        rows.append(rec)
    out = {'日': d, '上一交易日': prev, '缺件': miss, '条目': rows}
    json.dump(out, open(f'_学习/_前置校验_lhb_{d}.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    for r in rows:
        flag = 'OK ' if r['存在'] else 'MISS'
        print(f"{flag} {r['项']:<8} {r['路径']:<48} {r.get('字节', '')} {r.get('mtime', '')}")
    print('缺件:', miss if miss else '无')


if __name__ == '__main__':
    main()
