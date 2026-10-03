# -*- coding: utf-8 -*-
"""为自主拓展与认知迭代生成可持续承接的能力账本。
只从既有事实文件派生；缺少验证/命中证据时保持 null，不推断为成功。

★闭环关键：重建时**必须原样承接**上一版账本里的验证/能力化字段
（validation / hit_count / capitalized / reused_count / capability_rule /
boundary / validation_spec / review_log …）。若在重建时把它们重置为 None，
下游能力验证器的晋升会在下一次日链重建时被抹掉，能力进化闭环就断了。
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LEARN=ROOT/'_学习'

# 只由验证器/消费器写入；重建时只能承接，不允许重置为 None。
CARRY_FIELDS=('validation','validation_evidence','validated_at','refuted_at',
              'hit_count','capitalized','reused_count','reuse_log','last_reused_at',
              'feedback_routes','review_log','review_status','last_reviewed_at',
              'capability_rule','boundary','validation_spec','last_validated_at')
# 终态证据：不允许被条目原始文本重新降级
TERMINAL_STATES=('capability','refuted')

def load(p, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError): return default

def save(p, obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def norm_status(s):
    s=str(s or '')
    if '固化成脚本' in s or '能力化' in s: return 'capability'
    if '已证伪' in s or s in ('false','refuted'): return 'refuted'
    if s in ('true','validated') or '验证通过' in s: return 'validated'
    if s in ('探索','小样本验证','提请拍板','追踪中','pending'): return 'tracking'
    if s in ('搁置','shelved'): return 'shelved'
    return 'experience'

def carry(prev, row):
    """把上一版账本里的验证/能力化证据与规则字段原样并回重建行。

    缺证据时保持既有值；绝不因为“重建”把已验证/已能力化降级为 None。
    """
    if not isinstance(prev, dict): prev={}
    for k in CARRY_FIELDS:
        if prev.get(k) is not None: row[k]=prev[k]
        elif k not in row: row[k]=None
    if prev.get('state') in TERMINAL_STATES:
        row['state']=prev['state']
    return row

def build(d):
    incub=load(LEARN/'孵化区.json',{})
    logic_ledger=load(LEARN/'深挖专题台账.json',{})
    old_ext=load(LEARN/'能力进化库_自主拓展.json',{'version':1,'records':[]})
    old_cog=load(LEARN/'能力进化库_认知迭代.json',{'version':1,'records':[]})
    ext={r.get('id'):r for r in old_ext.get('records',[]) if r.get('id')}
    for route, rows in incub.items():
        for x in rows if isinstance(rows,list) else []:
            ident=f"extension:{x.get('id')}"
            logs=x.get('log') or []
            prev=ext.get(ident) or {}
            ext[ident]=carry(prev,{
              'id':ident,'kind':'自主拓展','route':route,'title':x.get('题'),'discovered_at':logs[0].get('d') if logs and isinstance(logs[0],dict) else None,
              'last_tracked_at':logs[-1].get('d') if logs and isinstance(logs[-1],dict) else None,
              'tracking_log':logs,'falsifiable_rule':x.get('判据'),'due':x.get('截止'),
              'state':prev['state'] if prev.get('state') in TERMINAL_STATES else norm_status(x.get('状态')),
              'source':'_学习/孵化区.json'
            })
    # logic 由横切面扫描.py维护深挖专题台账；这里统一归档为自主拓展，避免能力库缺失该路。
    for title, x in logic_ledger.items():
        if title == '_说明' or not isinstance(x, dict) or '产逻' not in str(x.get('路', '')):
            continue
        logs=[]
        for k, v in x.items():
            m=__import__('re').search(r'(?:应答|推进log|进展)[_·]?(\d{8})$', str(k))
            if m:
                logs.append({'d':m.group(1), '进展':v})
        if not logs and x.get('立项日'):
            logs=[{'d':x.get('立项日'), '进展':x.get('结论')}]
        logs.sort(key=lambda z: str(z.get('d','')))
        ident=f"extension:logic-{title}"
        prev=ext.get(ident) or {}
        ext[ident]=carry(prev,{
          'id':ident,'kind':'自主拓展','route':'logic','title':title,
          'discovered_at':x.get('立项日') or (logs[0].get('d') if logs else None),
          'last_tracked_at':logs[-1].get('d') if logs else x.get('立项日'),
          'tracking_log':logs,'falsifiable_rule':x.get('下一步') or x.get('结论'),
          'due':None,'state':prev['state'] if prev.get('state') in TERMINAL_STATES else norm_status(x.get('状态')),
          'source':'_学习/深挖专题台账.json'
        })
    # 认知库是事实经验来源；只有明确固化标记+验证证据才计入能力，其他仍经验/待验证。
    # ★由账本自身重建（不再向旧账本 append），避免每次日链把同一记录无限重复堆积。
    cr={r.get('fingerprint'):r for r in old_cog.get('records',[]) if r.get('fingerprint')}
    seen=set()
    for p in LEARN.glob('_认知库_*.json'):
        data=load(p,{})
        route=data.get('route',p.stem.replace('_认知库_',''))
        for i,x in enumerate(data.get('条目',[]) or []):
            ident=f"cognition:{route}:{x.get('日期')}:{i}:{x.get('标题','')[:32]}"
            if ident in seen:
                continue
            seen.add(ident)
            prev=cr.get(ident) or {}
            cr[ident]=carry(prev,{
              'id':ident,'fingerprint':ident,'kind':'认知迭代','route':route,
              'date':x.get('日期'),'title':x.get('标题'),'body':x.get('正文'),
              'falsifiable_rule':x.get('可证伪条件'),
              # 结构化能力字段由认知路在判断时给出，重建只做承接，不自行编造
              'capability_rule':x.get('能力规则') or prev.get('capability_rule'),
              'boundary':x.get('适用边界') or prev.get('boundary'),
              'validation_spec':x.get('验证规格') or prev.get('validation_spec'),
              'review_log':x.get('复核日志') or prev.get('review_log') or [],
              'state':prev['state'] if prev.get('state') in TERMINAL_STATES else norm_status(x.get('状态')),
              'source':x.get('来源') or p.name})
    out_cog={'version':2,'as_of':d,'updated':d,'source':'既有各路认知库 + 能力账本历史；缺证据不推断；验证/能力化字段原样承接','records':list(cr.values())}
    out_ext={'version':2,'as_of':d,'updated':d,'source':'既有孵化区 + 能力账本历史；缺证据不推断；验证/能力化字段原样承接','records':list(ext.values())}
    save(LEARN/'能力进化库_自主拓展.json',out_ext); save(LEARN/'能力进化库_认知迭代.json',out_cog)
    def stats(rows):
        return {'total':len(rows),'inherited':len(rows),'experiences':sum(r.get('kind')=='认知迭代' or r.get('state')=='experience' for r in rows),'tracking':sum(r.get('state')=='tracking' for r in rows),'shelved':sum(r.get('state')=='shelved' for r in rows),'validated':sum(r.get('validation')=='validated' or r.get('state')=='validated' for r in rows),'refuted':sum(r.get('validation')=='refuted' or r.get('state')=='refuted' for r in rows),'capabilities':sum(r.get('capitalized') is True or r.get('state')=='capability' for r in rows),
                # eligible = 真正进入次日判断层的能力（能力进化接线.py 的同一条门槛）
                'eligible_capabilities':sum(r.get('validation')=='validated' and r.get('capitalized') is True and bool(r.get('capability_rule') or r.get('falsifiable_rule')) for r in rows),
                'hits':sum((r.get('hit_count') or 0) for r in rows),'reused':sum((r.get('reused_count') or 0) for r in rows),'tracking_events':sum(len(r.get('tracking_log') or []) for r in rows),'review_events':sum(len(r.get('review_log') or []) for r in rows)}
    snap={'as_of':d,'自主拓展':stats(out_ext['records']),'认知迭代':stats(out_cog['records']),'规则':'只有存在明确验证、命中、能力化字段时才计数；null表示既有数据没有证据'}
    save(LEARN/f'能力进化快照_{d}.json',snap)
    print(json.dumps(snap,ensure_ascii=False,indent=2))

if __name__=='__main__': build(sys.argv[1] if len(sys.argv)>1 else 'unknown')
