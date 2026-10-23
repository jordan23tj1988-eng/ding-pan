import csv,json,io
from collections import defaultdict,Counter
D='20261023'
rows=list(csv.DictReader(open(f'{D}/lhb.csv',encoding='utf-8-sig')))
print('总行',len(rows))
# 口径
def is_interval(r):
    return any(k in r['上榜原因'] for k in ['连续','累计','严重异常'])
ded=[r for r in rows if not is_interval(r)]
itv=[r for r in rows if is_interval(r)]
print('当日榜行',len(ded),'区间榜行',len(itv))
codes=defaultdict(list)
for r in ded: codes[r['代码']].append(r)
print('当日榜唯一代码',len(codes))
# 双上榜原因重复码
dup={k:len(v) for k,v in codes.items() if len(v)>1}
print('同码多行(去重后)',dup)
A=sum(float(r['龙虎榜净买额']) for r in ded)
B=sum(float(r['龙虎榜净买额']) for r in rows)
print(f'值A 当日榜净额合计 {A/1e8:.4f}亿  正数{sum(1 for r in ded if float(r["龙虎榜净买额"])>0)}/{len(ded)}')
print(f'值B 含区间榜合计 {B/1e8:.4f}亿  正数{sum(1 for r in rows if float(r["龙虎榜净买额"])>0)}/{len(rows)}')
buy=sum(float(r['龙虎榜买入额']) for r in ded); sell=sum(float(r['龙虎榜卖出额']) for r in ded)
print(f'买侧 {buy/1e8:.2f}亿 卖侧 {sell/1e8:.2f}亿')
# 上榜原因分布
print(Counter(r['上榜原因'] for r in rows).most_common())
# 涨跌分布
up=sum(1 for r in ded if float(r['涨跌幅'])>0)
print('当日榜收涨',up,'收跌',len(ded)-up)
print('涨幅>=9.8%只数',sum(1 for r in ded if float(r['涨跌幅'])>=9.8))
