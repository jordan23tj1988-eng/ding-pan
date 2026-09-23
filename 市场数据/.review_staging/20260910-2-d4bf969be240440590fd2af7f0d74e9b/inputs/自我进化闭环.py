# -*- coding: utf-8 -*-
"""为自主拓展与认知迭代生成可持续承接的能力账本。
只从既有事实文件派生；缺少验证/命中证据时保持 null，不推断为成功。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LEARN=ROOT/'_学习'

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
            ext[ident]={
              'id':ident,'kind':'自主拓展','route':route,'title':x.get('题'),'discovered_at':logs[0].get('d') if logs and isinstance(logs[0],dict) else None,
              'last_tracked_at':logs[-1].get('d') if logs and isinstance(logs[-1],dict) else None,
              'tracking_log':logs,'falsifiable_rule':x.get('判据'),'due':x.get('截止'),'state':norm_status(x.get('状态')),
              'validation': None,'hit_count':None,'capitalized':None,'reused_count':None,
              'source':'_学习/孵化区.json'
            }
    # logic 由横切面扫描.py维护深挖专题台账；这里统一归档为自主拓展，避免能力库缺失该路。
    for title, x in logic_ledger.items():
        if title == '_说明' or not isinstance(x, dict) or '产逻' not in str(x.get('路', '')):
            continue
        logs=[]
        for k, v in x.items():
            m=__import__('re').search(r'(?:应答|推进log|进展)[_·]?(\\d{8})$', str(k))
            if m:
                logs.append({'d':m.group(1), '进展':v})
        if not logs and x.get('立项日'):
            logs=[{'d':x.get('立项日'), '进展':x.get('结论')}]
        logs.sort(key=lambda z: str(z.get('d','')))
        ident=f"extension:logic-{title}"
        ext[ident]={
          'id':ident,'kind':'自主拓展','route':'logic','title':title,
          'discovered_at':x.get('立项日') or (logs[0].get('d') if logs else None),
          'last_tracked_at':logs[-1].get('d') if logs else x.get('立项日'),
          'tracking_log':logs,'falsifiable_rule':x.get('下一步') or x.get('结论'),
          'due':None,'state':norm_status(x.get('状态')),
          'validation':None,'hit_count':None,'capitalized':None,'reused_count':None,
          'source':'_学习/深挖专题台账.json'
        }
    # 认知库是事实经验来源；只有明确固化标记才计入能力，其他仍是经验/待验证
    for p in LEARN.glob('_认知库_*.json'):
        data=load(p,{})
        route=data.get('route',p.stem.replace('_认知库_',''))
        for i,x in enumerate(data.get('条目',[]) or []):
            ident=f"cognition:{route}:{x.get('日期')}:{i}:{x.get('标题','')[:32]}"
            state=norm_status(x.get('状态'))
            old=next((r for r in old_cog.get('records',[]) if r.get('fingerprint')==ident),{})
            old.update({'id':ident,'fingerprint':ident,'kind':'认知迭代','route':route,'date':x.get('日期'),'title':x.get('标题'),'body':x.get('正文'),'falsifiable_rule':x.get('可证伪条件'),'state':state,'validation':old.get('validation'),'hit_count':old.get('hit_count'),'capitalized':old.get('capitalized'),'reused_count':old.get('reused_count'),'source':x.get('来源') or p.name})
            old_cog.setdefault('records',[]).append(old)
    # 去重，保留最新一份；不把缺失证据升级为能力
    cr={r.get('fingerprint'):r for r in old_cog.get('records',[]) if r.get('fingerprint')}
    out_cog={'version':2,'as_of':d,'updated':d,'source':'既有各路认知库 + 能力账本历史；缺证据不推断','records':list(cr.values())}
    out_ext={'version':2,'as_of':d,'updated':d,'source':'既有孵化区 + 能力账本历史；缺证据不推断','records':list(ext.values())}
    save(LEARN/'能力进化库_自主拓展.json',out_ext); save(LEARN/'能力进化库_认知迭代.json',out_cog)
    def stats(rows):
        return {'total':len(rows),'inherited':len(rows),'experiences':sum(r.get('kind')=='认知迭代' or r.get('state')=='experience' for r in rows),'tracking':sum(r.get('state')=='tracking' for r in rows),'shelved':sum(r.get('state')=='shelved' for r in rows),'validated':sum(r.get('validation')=='validated' or r.get('state')=='validated' for r in rows),'refuted':sum(r.get('validation')=='refuted' or r.get('state')=='refuted' for r in rows),'capabilities':sum(r.get('capitalized') is True or r.get('state')=='capability' for r in rows),'hits':sum((r.get('hit_count') or 0) for r in rows),'reused':sum((r.get('reused_count') or 0) for r in rows),'tracking_events':sum(len(r.get('tracking_log') or []) for r in rows)}
    snap={'as_of':d,'自主拓展':stats(out_ext['records']),'认知迭代':stats(out_cog['records']),'规则':'只有存在明确验证、命中、能力化字段时才计数；null表示既有数据没有证据'}
    save(LEARN/f'能力进化快照_{d}.json',snap)
    print(json.dumps(snap,ensure_ascii=False,indent=2))

if __name__=='__main__': build(sys.argv[1] if len(sys.argv)>1 else 'unknown')
