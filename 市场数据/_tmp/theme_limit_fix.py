import json,pathlib,re
p=pathlib.Path(r'D:\股票数据\市场数据\_学习\judgment_20260911.json');j=json.loads(p.read_text(encoding='utf8'))
# Fill theme five standard business headings with truthful source-backed text.
b=j['bodies']['theme']
for h,t in [('一 题材荐票','[实证] 正式荐票0只，观察候选0只；22条行业线全部为B档兜底，未核验催化，保持空仓。'),('二 三级判定','[实证] 40只涨停全部B行业兜底；元件9只但最高2板，瑞尔特4板为孤高标，不确认主线。'),('四 生命周期','[实证] 题材生命周期机器统计覆盖22条线；电力/通信设备/元件仅作分支观察，不把行业聚集升级为主线。'),('五 自主深挖','[实证] 需公告/订单/业绩双源与跨环节承载同步出现，才复议题材档位。')]:
 if '<h2>'+h not in b:b+=f'\n<h2>{h}</h2><div class="card"><p>{t}</p></div>'
j['bodies']['theme']=b
# Fill limitup hand-written summary fields required by sentinel.
b=j['bodies']['limitup']
if '首板33' not in b:b=b.replace('</article>','<p>梯队提炼：1板33、2板4、3板2、4板1；最高4板瑞尔特。</p><p>归位档：A0、B40、C0（来源档计数）。</p></article>')
j['bodies']['limitup']=b
p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8');(p.parent/'theme_body_20260911.html').write_text(j['bodies']['theme'],encoding='utf8');(p.parent/'limitup_body_20260911.html').write_text(b,encoding='utf8');print('theme/limitup body fields added')
