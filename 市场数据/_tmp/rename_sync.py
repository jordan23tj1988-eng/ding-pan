import json,pathlib
p=pathlib.Path(r'D:\股票数据\市场数据\_学习')
repls={'index_body_20260911.html':[('总审','总判断')],'cycle_body_20260911.html':[('二 五路投票','周期投票')],'auction_body_20260911.html':[('三 独立盲区','三 深挖')]}
for fn,rs in repls.items():
 f=p/fn; s=f.read_text(encoding='utf-8')
 for a,b in rs:s=s.replace(a,b)
 f.write_text(s,encoding='utf-8')
j=json.loads((p/'judgment_20260911.json').read_text(encoding='utf-8'))
for rt in ['index','cycle','auction']:
 fn=('cycle_body' if rt=='cycle' else rt+'_body')+'_20260911.html'; j['bodies'][rt]=(p/fn).read_text(encoding='utf-8')
(p/'judgment_20260911.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
