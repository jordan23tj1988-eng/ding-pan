import json,pathlib
p=pathlib.Path(r'D:\股票数据\市场数据\_学习'); j=json.loads((p/'judgment_20260911.json').read_text(encoding='utf-8'))
j['bodies']['index']=j['bodies']['index'].replace('总审','总判断')
for rt,fn,rs in [('cycle','cycle_body_20260911.html',[('二 五路投票','周期投票')]),('auction','auction_body_20260911.html',[('三 独立盲区','三 深挖')])]:
 f=p/fn; s=f.read_text(encoding='utf-8')
 for a,b in rs:s=s.replace(a,b)
 f.write_text(s,encoding='utf-8'); j['bodies'][rt]=s
(p/'judgment_20260911.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
