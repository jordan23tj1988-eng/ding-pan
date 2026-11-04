# -*- coding: utf-8 -*-
"""全池 118 只涨停 2026 三季报四档分类（东财 RPT_LICO_FN_CPD，REPORTDATE=2026-09-30 + 基期 2025-09-30）"""
import json, io, sys, csv, os, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(r'D:\股票数据\市场数据')

zt = list(csv.DictReader(open('20261104/zt_pool.csv', encoding='utf-8-sig')))
URL = ('https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_LICO_FN_CPD'
       '&columns=SECURITY_CODE,SECURITY_NAME_ABBR,REPORTDATE,NOTICE_DATE,TOTAL_OPERATE_INCOME,YSTZ,'
       'PARENT_NETPROFIT,SJLTZ,WEIGHTAVG_ROE&filter=(SECURITY_CODE%3D%22__CODE__%22)'
       '&pageNumber=1&pageSize=12&sortColumns=REPORTDATE&sortTypes=-1')

res = {}
fail = []
for r in zt:
    c = r['代码']
    try:
        req = urllib.request.Request(URL.replace('__CODE__', c), headers={'User-Agent': 'Mozilla/5.0'})
        d = json.load(urllib.request.urlopen(req, timeout=20))
        rows = (d.get('result') or {}).get('data') or []
        k = {}
        for x in rows:
            rd = x['REPORTDATE'][:10]
            if rd in ('2026-09-30', '2025-09-30'):
                k[rd] = x
        res[c] = k
    except Exception as e:
        fail.append((c, str(e)[:80]))
    time.sleep(0.12)

def cls(c):
    k = res.get(c) or {}
    a = k.get('2026-09-30'); b = k.get('2025-09-30')
    if not a:
        return dict(档='无报表', 细节='')
    ystz = a.get('YSTZ'); sjl = a.get('SJLTZ'); pn = a.get('PARENT_NETPROFIT')
    base = b.get('PARENT_NETPROFIT') if b else None
    if pn is None or ystz is None or sjl is None:
        return dict(档='缺字段', 细节='')
    pn_y = pn / 1e8
    if pn_y > 0 and sjl > 0 and ystz > 0 and base is not None and base > 0:
        d = '真增长'
    elif pn_y > 0 and base is not None and base <= 0:
        d = '扭亏'
    elif pn_y < 0 and base is not None and base < 0 and sjl > 0:
        d = '减亏假阳'
    else:
        d = '同比≤0/亏损'
    return dict(档=d, 营收按年=round(ystz, 2), 归母亿=round(pn_y, 2), 净利同比=round(sjl, 2),
                基期归母亿=(round(base / 1e8, 2) if base is not None else None),
                公告日=(a['NOTICE_DATE'][:10]), ROE=(round(a.get('WEIGHTAVG_ROE') or 0, 2)))

out = []
for r in zt:
    c = r['代码']
    d = cls(c)
    d.update(代码=c, 名称=r['名称'], 连板=int(r['连板数']), 封单亿=round(float(r['封板资金']) / 1e8, 2),
             封单比=round(float(r['封板资金']) / float(r['流通市值']) * 100, 2),
             首封=r['首次封板时间'], 炸=int(r['炸板次数']), 换手=round(float(r['换手率']), 2),
             流通亿=round(float(r['流通市值']) / 1e8, 1))
    out.append(d)

from collections import Counter
print('取数失败:', fail)
print('档位分布:', Counter(x['档'] for x in out))
print('\n--- 真增长 ---')
for x in out:
    if x['档'] == '真增长':
        print('%-6s %-6s %d板 营收%7.2f%% 归母%7.2f亿(%+.1f%%) 基期%6.2f亿 公告%s' % (
            x['代码'], x['名称'], x['连板'], x['营收按年'], x['归母亿'], x['净利同比'], x['基期归母亿'], x['公告日']))
print('\n--- 扭亏 ---')
for x in out:
    if x['档'] == '扭亏':
        print('%-6s %-6s %d板 营收%7.2f%% 归母%7.2f亿 基期%6.2f亿 公告%s' % (
            x['代码'], x['名称'], x['连板'], x['营收按年'], x['归母亿'], x['基期归母亿'], x['公告日']))
print('\n--- 减亏假阳 ---')
for x in out:
    if x['档'] == '减亏假阳':
        print('%-6s %-6s %d板 归母%7.2f亿 同比%+.1f%% 公告%s' % (
            x['代码'], x['名称'], x['连板'], x['归母亿'], x['净利同比'], x['公告日']))
print('\n--- 同比≤0/亏损 (前20) ---')
n = 0
for x in out:
    if x['档'] == '同比≤0/亏损':
        n += 1
        if n <= 20:
            print('%-6s %-6s %d板 营收%7.2f%% 归母%7.2f亿 同比%+.1f%%' % (
                x['代码'], x['名称'], x['连板'], x['营收按年'] or 0, x['归母亿'] or 0, x['净利同比'] or 0))
print('同比≤0/亏损 合计', n)
json.dump(out, open('_学习/_q3full_logic_20261104.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote')
