import json,pathlib
p=pathlib.Path(r'D:\股票数据\市场数据\_学习\judgment_20260911.json');j=json.loads(p.read_text(encoding='utf8'));b=j['bodies']['lhb'];
if '<h2>五 ' not in b:
 b=b.replace('<h2>六 我的认知迭代','<h2>五 自主深挖</h2><div class="card"><p>[实证] 目标日上榜58只、机构在场28只、S/A出手9笔；席位荐票仅作为观察，T+1结算待后续交易日验证。</p></div>\n<h2>六 我的认知迭代')
j['bodies']['lhb']=b;p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8');(p.parent/'lhb_body_20260911.html').write_text(b,encoding='utf8');print('inserted h2 five')
