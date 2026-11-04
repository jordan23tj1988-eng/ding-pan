import json,io,os,glob
d='20261104'
def st(p): return os.path.exists(p)
print("== 关键产物 ==")
for p in [f'_学习/题材归位_{d}.json',f'_学习/_题材四维.json',f'_学习/主流题材6有.json',
          f'_学习/自主拓展清单_{d}.json',f'_学习/自主拓展应答_{d}.json',f'_学习/fact_{d}.json',
          f'盘中/{d}/playbook.json',f'_学习/推演_{d}.json',f'_学习/总审_{d}.json',
          f'_学习/master结算.jsonl',f'_学习/跨路荐票_{d}.json',f'_学习/能力预加载_{d}.json',
          f'_学习/能力使用回执_{d}.json',f'_学习/周期投票结果_{d}.json']:
    print(("OK  " if st(p) else "MISS"),p)
j=json.load(io.open(f'_学习/judgment_{d}.json',encoding='utf-8-sig'))
print("== judgment keys:",list(j.keys()))
print("bodies:",list((j.get('bodies') or {}).keys()))
print("label:",j.get('更新label'),"| 一句话:",(j.get('一句话') or '')[:80])
for k,v in (j.get('bodies') or {}).items():
    print(f"  {k}: len={len(v)} LEDGER={'<!--LEDGER-->' in v} LHBLEDGER={'<!--LHBLEDGER-->' in v} POOLLEDGER={'<!--POOLLEDGER-->' in v}")
