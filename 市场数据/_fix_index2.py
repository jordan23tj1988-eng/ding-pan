# -*- coding: utf-8 -*-
import json,re
J=json.load(open('_学习/judgment_20260708.json',encoding='utf-8'))
b=J['bodies']['index']
# 取观察点表
m=re.search(r'(<table[^>]*>.*?</table>)',b,re.S)
tbl=m.group(1)
# 拆行
rows=re.findall(r'<tr.*?</tr>',tbl,re.S)
out=['<table>']
out.append('<tr><th>标的</th><th>身位 / 逻辑</th><th>明日(07-09)观察点</th></tr>')
for r in rows:
    if 'jjr' in r:              # 今晨竞价子行,原样保留
        out.append(r); continue
    if '<th>' in r: continue    # 旧表头丢弃
    tds=re.findall(r'<td[^>]*>(.*?)</td>',r,re.S)
    if len(tds)<4:
        out.append(r); continue
    biao,shen,guan,zhu=tds[0],tds[1],tds[2],tds[3]
    out.append(f'<tr><td>{biao}</td><td>{shen}</td><td>{guan}</td></tr>')
    # 荐票源·共振·类型 → 通栏子行(br转 · )
    flat=re.sub(r'\s*<br>\s*',' · ',zhu).strip()
    out.append(f'<tr class="jjr"><td colspan="3"><span class="jjtag">荐票·共振·类型</span>{flat}</td></tr>')
out.append('</table>')
newtbl=''.join(out)
b=b[:m.start()]+newtbl+b[m.end():]
J['bodies']['index']=b
json.dump(J,open('_学习/judgment_20260708.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('观察点表重构为3列+荐票通栏子行 | 表内tr数:',len(rows))
