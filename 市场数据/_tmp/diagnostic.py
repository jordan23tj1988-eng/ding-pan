import sys,pathlib,json
root=pathlib.Path(r'D:\股票数据\市场数据');sys.path.insert(0,str(root));import review_pages
for rt in ['index','cycle','auction','lhb','theme','logic','limitup']:
 m=review_pages.build_page_model(root,'20260911',rt)
 print(json.dumps({'route':rt,'status':m.get('status'),'empty':[(s['id'],s.get('title')) for s in m['sections'] if not s['claim_refs']], 'paper':m.get('paper_complete'),'components':[(c['id'],c['status'],c.get('issue')) for c in m.get('components',[])], 'errors':m['errors'],'conflicts':m.get('data_conflicts')},ensure_ascii=False))
