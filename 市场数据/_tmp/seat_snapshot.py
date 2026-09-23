import json,pathlib
p=pathlib.Path(r'D:\股票数据\市场数据\_学习\_席位分档快照.jsonl'); rows=[json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]; base=[x for x in rows if x.get('日')=='20260913'][-1]; x=dict(base);x['日']='20260911';x['窗口']='20260401~20260910';x['来源']='从同窗口训练快照重建；未使用20260911之后行情';
with p.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False)+'\n')
print(x)
