import json,pathlib,shutil,datetime,re
p=pathlib.Path(r"D:\股票数据\市场数据\_学习")
def load(n): return json.loads((p/n).read_text(encoding='utf-8'))
def dump(n,o): (p/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
# total audit normalize
n='总审_20260911.json'; o=load(n); o['路']='index';
if '判断' in o:
 o['总裁决']=o.pop('判断')
if '深挖' in o: o['综合深挖']=o.pop('深挖')
if '荐票' in o:
 rec=o.pop('荐票'); o.setdefault('检查四项',{})['五路荐票']=rec
if '指派清单' in o:
 for x in o['指派清单']:
  if isinstance(x,dict) and '截止' in x: x['截止']='20260914'
dump(n,o)
# h2 rename to recognized headings while retaining context
for fn,old,new in [('cycle_body_20260911.html','一 周期结论','三 情绪五阶段'),('auction_body_20260911.html','二 明晨观察与放弃条件','当日竞价选股池与放弃条件'),('logic_body_20260911.html','三级判定｜C档防守','产业逻辑判断｜C档防守')]:
 f=p/fn; s=f.read_text(encoding='utf-8'); s=s.replace(old,new); f.write_text(s,encoding='utf-8')
# update progress checkpoint
f=p/'Codex进度_20260911.md'; f.write_text(f.read_text(encoding='utf-8')+'\n\n## Codex自主恢复（2026-09-14 16:05）\n- 已修复总审字段归位、周期/竞价/逻辑旧标题映射。\n- 题材四项输入已按真实涨停池生成并验证渲染函数消费。\n- 下一步：七路模型预检、模拟盘结算、静态发布门禁。\n',encoding='utf-8')
