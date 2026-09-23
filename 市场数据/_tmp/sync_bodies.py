import json,pathlib
p=pathlib.Path(r'D:\股票数据\市场数据\_学习'); j=json.loads((p/'judgment_20260911.json').read_text(encoding='utf-8'))
for rt in ['index','cycle','auction','lhb','theme','logic','limitup']:
 f=p/(('cycle_body' if rt=='cycle' else rt+'_body')+'_20260911.html');
 if f.exists(): j['bodies'][rt]=f.read_text(encoding='utf-8')
(p/'judgment_20260911.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
