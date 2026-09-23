import sys,pathlib
sys.path.insert(0,r'D:\股票数据\市场数据')
import review_pages
root=pathlib.Path(r'D:\股票数据\市场数据'); d='20260911'
for rt in ['index','cycle','auction','lhb','theme','logic','limitup']:
 m=review_pages.build_page_model(root,d,rt); print(rt,m.get('status'),m.get('errors',[])[:6])
