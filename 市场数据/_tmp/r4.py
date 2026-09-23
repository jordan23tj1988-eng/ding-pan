import json,pathlib
p=pathlib.Path(r'D:\股票数据\市场数据\_学习'); f=p/'cycle_body_20260911.html'; s=f.read_text(encoding='utf8').replace('四 盲区与边界','四 深挖'); f.write_text(s,encoding='utf8'); j=json.loads((p/'judgment_20260911.json').read_text(encoding='utf8')); j['bodies']['cycle']=s; (p/'judgment_20260911.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
