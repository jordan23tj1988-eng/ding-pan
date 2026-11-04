import json,io,os,glob
d='20261104'; pd_='20261103'
def L(p):
    try: return json.load(io.open(p,encoding='utf-8-sig'))
    except Exception as e: return {'_err':str(e)}
out=[]
def P(*a): out.append(' '.join(str(x) for x in a))
# 五路
for r in ['auction','lhb','theme','logic','limitup']:
    j=L(f'_学习/{r}判断_{d}.json'); p=j.get('判断',{})
    sk=j.get('荐票',{}).get('标的') or []
    types={}
    for s in sk: types[s.get('类型','?')]=types.get(s.get('类型','?'),0)+1
    P(f"[路] {r}: 档位={p.get('档位')} 置信={p.get('置信度')} 标的={len(sk)} {types} 结论={str(p.get('结论'))[:110]}")
# 总审
t=L(f'_学习/总审_{d}.json'); nc=t.get('总裁决',{})
P("[总审] 档位=",nc.get('档位'),"置信=",nc.get('置信度'),"结论=",str(nc.get('结论'))[:200])
P("[总审] 分歧数=",len(t.get('分歧点') or []),"检查四项=",json.dumps(t.get('检查四项'),ensure_ascii=False)[:300])
P("[总审] 指派=",len(t.get('指派清单') or []),"环境加权=",str(t.get('环境加权依据'))[:160])
# 推演
y=L(f'_学习/推演_{d}.json')
P("[推演] 情绪几度=",y.get('情绪几度'),"攻防=",str(y.get('明日攻防'))[:120],"主线=",str(y.get('主线站队'))[:120])
P("[推演] 龙头接力=",str(y.get('龙头接力'))[:100],"竞价预判=",str(y.get('竞价强弱预判'))[:100],"预测数=",len(y.get('次日可证伪预测') or []))
# 结算
s=L(f'_学习/五路判断结算_{pd_}.json')
P("[昨日结算] keys=",list(s.keys())[:8])
# 校准
c=L(f'_学习/校准_{pd_}.json')
P("[昨日预判结算] ",json.dumps({k:v for k,v in c.items() if k in ('判定','命中','命中率','条目','逐条','汇总')},ensure_ascii=False)[:500])

print("
".join(out))
