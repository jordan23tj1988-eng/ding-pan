# -*- coding: utf-8 -*-
import json,os
L='_学习'
J=json.load(open(f'{L}/judgment_20260708.json',encoding='utf-8'))
rd=json.load(open(f'{L}/竞价池初读_20260708.json',encoding='utf-8'))
# 逐只初读判定(基于真实今晨数据)
verdict={
 "000977":("dA","✓强验证","业绩龙盘中封涨停,8只里唯一真封,方向硬度扛住"),
 "603137":("dA","✓验证","续封8板惯性,但高位断层高危,只当情绪温度计"),
 "001208":("dC","✗打脸","电网散点一字,高开-0.9%即走弱,一日游"),
 "000524":("dC","✗打脸","旅游散点竞价冲高+10%→盘中回落+2.4%,未兑现"),
 "001229":("dC","✗打脸","2板梯队票冲高+9.8%→回落+1.1%,减持利空兑现"),
 "301251":("dC","✗✗崩","PCB/AI电源2板票低开-6.4%→杀近跌停-9.5%,全场最差"),
 "603296":("dB","✗走弱","服务器整机洼地扩散票低开熄火,现-0.4%未封"),
 "002841":("dB","◐半中","低开-4.8%盘中拉回+2.8%,异动利空压制,未封"),
}
def cell(d):
    if not d: return "—"
    return f'高开{d["高开"]:+.1f}% · 现{d["现涨"]:+.1f}% · {"封板" if d["封板"] else "未封"}'
rows=''
seal=0
for it in rd['明细']:
    c=it['代码']; cl,tag,why=verdict.get(c,("dB","—",""))
    d=it['今晨']
    if d and d.get('封板'): seal+=1
    rows+=f'<tr><td><b>{it["名称"]}</b><br><span class="mut">{c}</span></td><td>{it["信号"]}<br><span class="mut">{it["题材"]}</span></td><td>{cell(d)}</td><td class="{cl}">{tag}<br><span class="mut" style="font-weight:400">{why}</span></td></tr>'
block=(f'<h2 class="hot">二·今晨初读、07-08选股池 T+1竞价初读(09:39实时)</h2>'
 f'<div class="hint">昨日(07-08)竞价池8只,用今晨(07-09)集合竞价+早盘实时做T+1初读。★成交额09:39已是累计非竞价额,故只用高开/现价定强弱,不引竞价额。完整封板/收益终结算今晚18:00补。</div>'
 f'<div class="card"><table><tr><th>标的</th><th>07-08竞价信号</th><th>今晨(07-09)实况</th><th>初读判定</th></tr>{rows}</table>'
 f'<p class="base" style="margin-top:10px"><b>★初读归因:</b> 8只盘中封板 <b>{seal}/8≈{round(seal/8*100)}%</b>,远低于一字池41.6%/秒板24.5%历史概率。<b>只有业绩龙浪潮(真封)+存储孤峰恒尚(续板)扛住,算力扩散/末端票(华勤/威尔高/视源/魅视)T+1全线走弱</b>——竞价选出强身位(一字/秒板)也救不了缺业绩/缺高度的扩散票。印证昨晚"方向真、高度弱、末端散":竞价维度须与产业逻辑(业绩硬度)+题材身位共振,不能单看竞价强弱。与今晨池信息(算力一字缺席、资金切军工)互证。</p></div>')
a=J['bodies']['auction']
mk=a.find('<h2>二、昨日选股池结算')
if mk<0: mk=a.find('二、昨日选股池结算'); mk=a.rfind('<h2',0,mk)
# 把旧的07-07结算标题降级注明历史
a=a.replace('<h2>二、昨日选股池结算','<h2>附·07-07池结算(历史)',1).replace('<h2 class="hot">二、昨日选股池结算','<h2>附·07-07池结算(历史)',1)
mk=a.find('<h2>附·07-07池结算(历史)')
a=a[:mk]+block+'\n'+a[mk:]
J['bodies']['auction']=a
json.dump(J,open(f'{L}/judgment_20260708.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('injected. auction len',len(a),'| 封板',seal,'/8')
