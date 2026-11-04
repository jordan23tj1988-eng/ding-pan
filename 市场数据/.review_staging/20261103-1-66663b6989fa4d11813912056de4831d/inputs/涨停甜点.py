# -*- coding: utf-8 -*-
"""涨停甜点.py — 第3板甜点标签构建器 v1.0

作用: 每日涨停复盘时, 对当日「连板数==3」的票自动打甜点标签(零后视镜、机器判定、可验证)。
规则对齐 量价因子库 M28 定稿(26年跨年验证 17/17 年正期望):
  甜点 = 第3板 + 一字开(open≈涨停价) + 盘中炸板(low<涨停价) + 炸开幅度<3%(浅炸/中炸) + 回封(收盘涨停)

标签分档:
  甜点      = 一字开 + 炸板 + 炸开<3%(low/close>0.97)   ← 唯一正期望介入点
  深炸观望  = 一字开 + 炸板 + 炸开>3%(low/close<=0.97)   ← 失败率53%、期望-4.89%, 坚决不碰
  一字买不进 = 一字开 + 未炸板(纯一字封死)               ← 无成交机会
  换手板    = 非一字开(open<涨停价)                      ← 低开/平开拉板, 非甜点(打板-2.09%/低吸-0.77%)
  数据缺失  = _bars_cache 无当日行                        ← 零编造, 标 null

数据源: {d}/zt_pool.csv(连板数/炸板次数) + _学习/_bars_cache/{code}.csv(open/high/low/close)
口径: 涨停价=close(涨停票收盘即涨停价); eps=0.011 与量价因子库 M23/M28 一致; 排除北交所(4/8/9开头)。

用法: python 涨停甜点.py 20260814
输出: _学习/涨停甜点_{d}.json + 控制台摘要
"""
import os, sys, csv, json, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LEARN = os.path.join(BASE, '_学习')
CDIR = os.path.join(LEARN, '_bars_cache')
EPS = 0.011          # 一字开/炸板判定容差(与量价因子库 M23/M28 一致)
DEEP = 0.97          # 炸开深度阈值: <0.97=深炸(炸开>3%), >=0.97=浅/中炸(炸开<3%)


def is_bj(code):
    return code[0] in ('4', '8', '9')


def read_zt_pool(d):
    p = os.path.join(BASE, d, 'zt_pool.csv')
    if not os.path.exists(p):
        return None
    rows = []
    with open(p, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def read_bar(code, d):
    """读 _bars_cache 当日行, 返回 dict(open/high/low/close/volume) 或 None。兼容列数不一致。"""
    p = os.path.join(CDIR, code + '.csv')
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            last = None
            for r in reader:
                date_raw = (r.get('date') or '').strip().replace('-', '')
                if date_raw == d:
                    last = r
        if last is None:
            return None
        def g(k):
            try:
                return float(last.get(k, ''))
            except (TypeError, ValueError):
                return None
        return {'open': g('open'), 'high': g('high'), 'low': g('low'),
                'close': g('close'), 'volume': g('volume')}
    except Exception:
        return None


def classify(bar, zb_cnt):
    """返回 (标签, 炸开深度str)。bar 必含 open/low/close。"""
    o, low, c = bar['open'], bar['low'], bar['close']
    if o is None or low is None or c is None:
        return '数据缺失', None
    one_zi = abs(o - c) < EPS                      # 一字开: 开盘≈涨停价
    zha_ban = low < c - EPS                        # 炸板: 盘中跌破涨停价
    depth = low / c if c else None                 # 炸开深度(越低炸越深)
    if not one_zi:
        return '换手板', depth
    if not zha_ban:
        return '一字买不进', None                  # 纯一字封死, 没炸板
    if depth is not None and depth < DEEP:
        return '深炸观望', depth                   # 炸开>3%
    return '甜点', depth                           # 炸开<3% 回封


def build(d):
    rows = read_zt_pool(d)
    if rows is None:
        print(f'[错误] {d}/zt_pool.csv 不存在')
        sys.exit(2)
    d3 = [r for r in rows if str(r.get('连板数', '')).strip() == '3'
          and not is_bj(str(r.get('代码', '')).strip().zfill(6))]

    buckets = {'甜点': [], '深炸观望': [], '一字买不进': [], '换手板': [], '数据缺失': []}
    order = ['甜点', '深炸观望', '一字买不进', '换手板', '数据缺失']
    for r in d3:
        code = str(r.get('代码', '')).strip().zfill(6)
        name = r.get('名称', '').strip()
        zb = str(r.get('炸板次数', '')).strip()
        bar = read_bar(code, d)
        if bar is None:
            buckets['数据缺失'].append({'代码': code, '名称': name, '炸板次数': zb, '标签': '数据缺失'})
            continue
        tag, depth = classify(bar, zb)
        item = {
            '代码': code, '名称': name,
            'open': bar['open'], 'low': bar['low'], 'close': bar['close'],
            '炸开深度': round(depth, 4) if depth is not None else None,
            '炸板次数': zb, '标签': tag,
        }
        buckets[tag].append(item)

    out = {
        'schema': 'sweetspot-v1',
        'date': d,
        'route': 'limitup',
        'build_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '规则': '第3板一字开炸板<3%回封=甜点(对齐量价因子库M28: 26年471次/胜68%/单笔+4.18%/17-17年正期望); '
                '深炸>3%=观望(失败率53%/期望-4.89%); 换手板=非甜点(打板-2.09%/低吸-0.77%)',
        '第3板票数': len(d3),
        '甜点票数': len(buckets['甜点']),
    }
    for k in order:
        out[k] = buckets[k]

    os.makedirs(LEARN, exist_ok=True)
    out_path = os.path.join(LEARN, f'涨停甜点_{d}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return out, out_path


def main():
    if len(sys.argv) < 2:
        print('用法: python 涨停甜点.py YYYYMMDD')
        sys.exit(2)
    d = sys.argv[1]
    out, out_path = build(d)
    print(f'涨停甜点_{d}.json 已写入: {out_path}')
    print(f'第3板票: {out["第3板票数"]} 只 | 甜点: {out["甜点票数"]} 只')
    for k in ['甜点', '深炸观望', '一字买不进', '换手板', '数据缺失']:
        lst = out[k]
        if lst:
            names = '、'.join(f"{x['名称']}({x['代码']})" for x in lst)
            print(f'  [{k}] {len(lst)}: {names}')
    print('DONE')


if __name__ == '__main__':
    main()
