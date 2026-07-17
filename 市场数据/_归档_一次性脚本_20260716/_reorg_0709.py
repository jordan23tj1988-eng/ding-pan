# -*- coding: utf-8 -*-
"""重组07-09 judgment到IA v2结构:只切段重排agent真实内容,零编造。"""
import json,re
L='_学习'
J=json.load(open(f'{L}/judgment_20260709.json',encoding='utf-8'))
b=J['bodies']

def split_sections(html):
    """返回 (preamble, [(h2标题纯文本, 整段html含h2), ...]),段=h2到下一个h2前"""
    idxs=[m.start() for m in re.finditer(r'<h2',html)]
    pre=html[:idxs[0]] if idxs else html
    secs=[]
    for i,s in enumerate(idxs):
        e=idxs[i+1] if i+1<len(idxs) else len(html)
        seg=html[s:e]
        t=re.sub('<[^>]+>','',re.search(r'<h2[^>]*>(.*?)</h2>',seg,re.S).group(1)).strip()
        secs.append((t,seg))
    return pre,secs

def pick(secs,key):
    for t,seg in secs:
        if key in t: return seg
    return ''

# ---------- INDEX:重排为 hero→观察点(07-10)→四维看牌→拐点预警→认知迭代 ----------
pre,secs=split_sections(b['index'])
obs=pick(secs,'明日核心观察点(07-10)')
kanpai=pick(secs,'四维看牌 · 命门温度') or pick(secs,'四维看牌')
guaidian=pick(secs,'拐点预警')
renzhi=pick(secs,'认知迭代')
zongkaiguan=pick(secs,'环境 · 总开关')   # 移到cycle
assert obs and kanpai and guaidian and renzhi, '缺段:'+str([t for t,_ in secs])
b['index']=pre+obs+kanpai+guaidian+renzhi
# ---------- CYCLE:补上攻防总开关(从index移入,放末尾认知迭代前) ----------
if zongkaiguan:
    zn=zongkaiguan.replace('环境 · 总开关','攻防 · 仓位总开关(环境→周期→情绪)')
    b['cycle']=b['cycle']+zn
# ---------- LIMITUP:重组为 Top5→台账(带标记)→训练 ----------
pre2,secs2=split_sections(b['limitup'])
top5=pick(secs2,'Top5')
hebiao=pick(secs2,'全量三层归位表')
hedui=pick(secs2,'题材核对说明')
jiegou=pick(secs2,'主线 vs 散乱')
xunlian=pick(secs2,'训练库') or pick(secs2,'训练')
xunlian=re.sub(r'(<h2[^>]*>)\s*四\s*·?\s*','\\1',xunlian)  # 去编号
# 当日日块额外分析(核对+结构)存进07-09日块,由台账脚本统一格式生成表
extra=hedui+jiegou
json.dump({'extra_html':extra},open(f'{L}/_日块附加_20260709.json','w',encoding='utf-8'),ensure_ascii=False)
b['limitup']=(pre2+top5
 +'<h2>每日涨停归位台账 · 最新在上</h2>'
 +'<div class="hint">每天一个日期块:速览+三层归位表(催化/来源档/质量分T1T2预测)+当日核对与结构判读。最新展开,历史折叠。</div>'
 +'<!--LEDGER--><!--/LEDGER-->'
 +xunlian)
json.dump(J,open(f'{L}/judgment_20260709.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('index段序:',[t for t,_ in split_sections(b['index'])[1]])
print('cycle段序:',[t for t,_ in split_sections(b['cycle'])[1]])
print('limitup段序:',[t for t,_ in split_sections(b['limitup'])[1]])
