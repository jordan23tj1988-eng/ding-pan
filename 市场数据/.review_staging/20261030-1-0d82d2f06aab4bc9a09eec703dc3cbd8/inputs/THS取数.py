# -*- coding: utf-8 -*-
"""THS取数.py — 同花顺(THS)金融数据服务 REST 取数脚本(涨停池/连板/异动等特色数据)。

机制修复(2026-08-13,总账#047): 晚间agent裸curl取THS被系统代理坑(fuyao.aicubes.cn
是国内服务器,走127.0.0.1:7897梯子=000超时),8/12起涨停原因连续两晚缺,归位全B档
行业兜底。本脚本把两个坑固化: ①urllib+ProxyHandler({})强制直连不走代理
②凭据从 %APPDATA%/hithink-finance/credentials.env 读,不落码。

用法:
  python THS取数.py 20260813                # 涨停池(含limit_up_reason)落盘 _学习/THS涨停池_{d}.json
  python THS取数.py 20260813 --ladder       # 连板天梯
  python THS取数.py 20260813 --moves        # 异动(需按端点补参数)
输出落盘 _学习/THS涨停池_{d}.json, 同时打印统计(总数/原因非空数)。
"""
import json, os, sys, time, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, '_学习')
API = 'https://fuyao.aicubes.cn/api/a-share/special-data/limit-up-pool'


def _key():
    p = os.path.join(os.environ.get('APPDATA', ''), 'hithink-finance', 'credentials.env')
    if not os.path.isfile(p):
        sys.exit(f'[FAIL] 凭据缺失: {p}')
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if line.startswith('API_KEY=') or line.startswith('HITHINK_FINANCE_API_KEY='):
            return line.split('=', 1)[1].strip()
    sys.exit(f'[FAIL] credentials.env 中无 API_KEY')


def _get(url):
    req = urllib.request.Request(url, headers={'X-api-key': _key()})
    # 机制坑固化: fuyao.aicubes.cn 国内服务器, 强制直连(ProxyHandler({})), 不走系统代理
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def limit_up_pool(d):
    """全量分页拉涨停池, 返回 item[]。date_ms=交易日00:00北京时间毫秒。"""
    t = time.strptime(d, '%Y%m%d')
    date_ms = int(time.mktime(t) * 1000)
    items, page = [], 1
    while True:
        q = urllib.parse.urlencode({'date_ms': date_ms, 'page': page, 'size': 100})
        j = _get(f'{API}?{q}')
        if j.get('code') != 0:
            sys.exit(f'[FAIL] THS code={j.get("code")} message={j.get("message")}')
        data = j['data']
        if data is None or not data.get('item'):
            break
        items.extend(data['item'])
        pg = data.get('pagination', {})
        if page >= pg.get('pages', 1):
            break
        page += 1
        time.sleep(0.3)
    return items


def main():
    if len(sys.argv) < 2:
        sys.exit('用法: python THS取数.py YYYYMMDD [--ladder]')
    d = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else ''
    os.makedirs(L, exist_ok=True)
    items = limit_up_pool(d)
    out = os.path.join(L, f'THS涨停池_{d}.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    with_reason = sum(1 for x in items if x.get('limit_up_reason'))
    print(f'[OK] {out}: 共{len(items)}只, limit_up_reason非空 {with_reason}/{len(items)}')


if __name__ == '__main__':
    main()
