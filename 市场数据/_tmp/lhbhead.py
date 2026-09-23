import json,pathlib
p=pathlib.Path(r'D:\股票数据\市场数据\_学习');f=p/'judgment_20260911.json';j=json.loads(f.read_text(encoding='utf8'));b=j['bodies']['lhb']
for a,z in [('席位综合判断','一 今日S/A动向与席位判断'),('资金温度','二 资金温度'),('龙虎榜台账','三 龙虎榜台账'),('席位分档','四 席位分档库'),('荐票','五 自主深挖'),('三级判定','五 自主深挖'),('生命周期','六 我的认知迭代')]:b=b.replace('<h2>'+a+'</h2>','<h2>'+z+'</h2>')
j['bodies']['lhb']=b
f.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8');(p/'lhb_body_20260911.html').write_text(b,encoding='utf8')
