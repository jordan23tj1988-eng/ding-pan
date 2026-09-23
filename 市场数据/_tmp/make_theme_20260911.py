import csv,json
from pathlib import Path
root=Path(r"D:\股票数据\市场数据"); d='20260911'; rows=list(csv.DictReader(open(root/d/'zt_pool.csv',encoding='utf-8-sig'))); mp={}
for x in rows:
 c=x['代码'].zfill(6); ind=x.get('所属行业','').strip() or '未分类'; mp[c]={'名称':x['名称'],'大方向':f'待归位·{ind}','环节':ind,'催化':f'{d}无可用THS涨停原因，按所属行业兜底；不据此编造催化','来源档':'B','数据依据':f'{d}/zt_pool.csv所属行业','连板数':int(float(x['连板数'] or 1)),'首次封板时间':x['首次封板时间'],'所属行业':ind,'来源证据':{'文件':f'{d}/zt_pool.csv','字段':'所属行业'}}
out={'日期':d,'映射':mp,'来源':f'缺THS涨停原因文件; 按 {d}/zt_pool.csv 所属行业兜底(非催化确认)','口径':f'逐只覆盖{d} zt_pool.csv的{len(rows)}只；缺原因全部标注B行业兜底，禁止将行业视为公告催化。','A':0,'B':len(rows),'C':0,'档计数':{'A':0,'B':len(rows),'C':0}}; json.dump(out,open(root/'_学习'/f'题材归位_{d}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1); print('wrote',len(rows))
