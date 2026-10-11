import csv, hashlib, json, re, sys
from pathlib import Path
ROOT=Path('D:/股票数据/市场数据'); L=ROOT/'_学习'; D='20261008'; issues=[]; warnings=[]
def check(ok,msg):
    (print(('PASS ' if ok else 'FAIL ')+msg))
    if not ok: issues.append(msg)
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
# Files and parse
paths={k:L/v for k,v in {'judgment':f'lhb判断_{D}.json','body':f'lhb_body_{D}.html','plan':f'交易计划_lhb_{D}.json','receipt':f'能力使用回执_{D}.json','run':f'lhb运行状态_{D}.json'}.items()}
for k,p in paths.items(): check(p.is_file(),f'{k} exists')
if issues: sys.exit(1)
j=load(paths['judgment']); plan=load(paths['plan']); receipt=load(paths['receipt']); run=load(paths['run']); body=paths['body'].read_text(encoding='utf-8')
check(j.get('日期')==D and j.get('路')=='lhb','判断日期/路标识')
check(j.get('判断',{}).get('档位') in ('A','B','C') and bool(j['判断'].get('置信度')) and len(j['判断'].get('可证伪条件',[]))>=1 and bool(j['判断'].get('独立盲区声明')),'判断档位/置信度/可证伪/盲区')
items=j.get('荐票',{}).get('标的',[]);check(len(items)<=3 and all(re.fullmatch(r'\d{6}',x.get('代码','')) and x.get('名称') and x.get('理由') and x.get('类型') for x in items),'荐票≤3且结构完整')
# Code and numeric evidence checks: same-day official source rows, excluding interval/cumulative rows, no double sum.
source=rows(ROOT/D/'lhb.csv'); clean={}
for x in source:
    if any(t in x['上榜原因'] for t in ('连续','累计','严重异常')) or '转债' in x['名称'] or not re.fullmatch(r'\d{6}',x['代码']): continue
    clean.setdefault(x['代码'],x)
for x in items:
    r=clean.get(x['代码']); check(bool(r and r['名称']==x['名称']),f"荐票/观察 {x['代码']} 回源当日榜/证券名")
    check(all(s in x['理由'] for s in ('源1当日净买','源2判定','S/A有效出手','位置门禁','来源：')),f"{x['代码']}定量证据及来源")
# Validate machine dual snapshot status and metric keys against judgment evidence.
dual=load(L/f'龙虎榜双源校验_{D}.json'); m=dual['metrics']; blob=json.dumps(j,ensure_ascii=False)
dual_rows={x['代码']:x for x in dual.get('全量',[])}
check(dual.get('status')=='pass' and dual.get('date')==D,'双源状态/日期')
check(str(m['强矛盾']) in blob and str(m['可比数']) in blob,'双源数字回源存在')
for item in items:
    row=clean[item['代码']]; dr=dual_rows.get(item['代码'],{})
    src1=round(float(row['龙虎榜净买额'])/1e8,4)
    src2=dr.get('源2买侧净额亿')
    match1=re.search(r'源1当日净买([-+]?\d+(?:\.\d+)?)亿元',item['理由'])
    match2=re.search(r'买侧净额=([-+]?\d+(?:\.\d+)?)亿元',item['理由'])
    check(bool(match1 and float(match1.group(1))==src1),f"{item['代码']}源1净买数字逐项回源({src1})")
    check(bool(match2 and src2 is not None and float(match2.group(1))==float(src2)),f"{item['代码']}源2金额逐项回源({src2})")
    check(item['代码'] in dual_rows and item['理由'].find('源2判定='+str(dr.get('判定')))>=0,f"{item['代码']}双源分类逐项回源")
check(len(re.findall(r'<h2>',body))==6,'HTML六段h2')
check(body.count('<div')==body.count('</div>'),'HTML div 配平')
for anchor in ('FUNDTEMP','LHBLEDGER','SEATCARD'):
    check(body.count(f'<!--{anchor}-->')==1 and body.count(f'<!--/{anchor}-->')==1,f'{anchor}锚成对唯一')
check('class="card"' in body and body.find('席位路洞察')>body.find('<h2>一、') and body.find('席位路洞察')<body.find('<!--LHBLEDGER-->'),'洞察卡位置与组件')
check(all(f'class="{c}"' in body for c in ('obs obs-watch','obs-head','obs-rec')),'观察卡obs/obs-head/obs-watch/obs-rec组件')
classes={c for m in re.finditer(r'class="([a-z][^"]*)"',body) for c in m.group(1).split()}
gen=(ROOT/'生成盯盘台.py').read_text(encoding='utf-8-sig')
css=set(re.findall(r'\.([A-Za-z][\w-]*)\b(?=[\s{,>\.:])',gen))
check(classes<=css,f'使用类均由生成盯盘台.py定义（未定义={sorted(classes-css)}）')
check('.panel' not in body and 'rec-card' not in body and 'rec-title' not in body and 'rec-his' not in body and 'rec-why' not in body,'未使用禁用类')
check('hint：' in body and D in body,'HTML hint/as-of')
check(plan.get('日期')==D and plan.get('as_of')==D and plan.get('路')=='lhb','计划日期/路标识')
# The specified actual portfolio file may be stale; refuse to call coverage complete if so.
state=load(L/'_模拟盘/lhb/状态.json'); holdings=state.get('持仓') or []
covered=(state.get('date')==D)
if not covered:
    warnings.append('当前持仓状态已过期，计划空仓不构成对目标日真实持仓的完整覆盖；未虚构买卖。')
    print('BLOCK 模拟盘状态日期覆盖目标日('+str(state.get('date'))+')')
else:
    check(True,f"模拟盘状态日期覆盖目标日({state.get('date')})")
# On a current state date, every position would need an explicit BUY/SELL/hold decision; stale state blocks that claim.
if covered:
    plan_codes={x.get('code') for x in plan.get('buys',[])+plan.get('sells',[])}
    check(all(x.get('code') in plan_codes for x in holdings),'所有实际持仓均在交易计划逐票表态')
# Capability receipt contract.
preload=load(L/f'能力预加载_{D}.json'); expected=hashlib.sha256((L/f'能力预加载_{D}.json').read_bytes()).hexdigest()
check(receipt.get('schema_version')==1 and receipt.get('as_of')==D and receipt.get('preload',{}).get('sha256')==expected,'能力回执schema/as_of/preload哈希')
check(set(receipt.get('routes',{}))=={'auction','lhb','theme','logic','limitup','cycle','master'},'能力回执覆盖七路')
for route,block in preload.get('routes',{}).items():
    rr=receipt['routes'][route]; ids=[x['id'] for x in block.get('records') or []]
    check(set(rr.get('considered_ids',[]))==set(ids),f'{route} capability逐条回应')
    if not ids: check(rr.get('status')=='no_eligible_capabilities',f'{route}无能力显式no_eligible_capabilities')
    elif route=='lhb': check(rr.get('status')=='applied' and bool(rr.get('applied')),'lhb可用能力被实际采纳')
# A bounded result: no fabricated sentinel assertion.
run['self_checks']={'acceptance_script':'lhb验收_20261008.py','hard_checks':'pass' if not issues else 'fail','portfolio_coverage':'pass' if covered else 'blocked_stale_state','warnings':warnings,'official_sentinel':'not_run'}
run['status']='completed_with_gaps' if (issues or warnings) else 'completed'
paths['run'].write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'hard_checks':'pass' if not issues else 'fail','formal_sentinel':'not_run','portfolio_coverage':'pass' if covered else 'blocked_stale_state','failures':issues,'warnings':warnings},ensure_ascii=False,indent=2))
sys.exit(1 if issues else (2 if warnings else 0))
