# -*- coding: utf-8 -*-
"""竞价池结算归档.py [--inject] —— auction页段二台账化(2026-07-12用户拍板,照limitup台账做法:最新展开,历史折叠)。
★扫描 _学习/竞价池结算_*.json + 竞价池结算卡_*.html → 产 _学习/竞价池结算档.html:
  每天都是可折叠日期条:最新default open+chip最新,其余收起+chip存档;均可点击开合 <details class="chain">(summary=日期+池N只+封板+胜率+均收速览)。
★--inject: 幂等注入最新judgment的auction段二 <!--POOLLEDGER-->...<!--/POOLLEDGER--> 标记区。
★链路铁律(防新旧双卡):本脚本只动POOLLEDGER标记区;评分卡=SCORECARD标记区(竞价评分.py产,agent嵌);
  洞察card=agent手写在标记区外;三者互不越界。段一禁再写trow池表(老展示卡2026-07-12废除,评分卡取代)。
用法: python3 竞价池结算归档.py --inject   (每晚竞价池结算.py之后跑)"""
import os,sys,json,glob,re
BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")

def build():
    ds=sorted([re.search(r'竞价池结算_(\d{8})\.json',p).group(1)
               for p in glob.glob(os.path.join(L,"竞价池结算_*.json"))],reverse=True)
    if not ds:
        return "<!--POOLLEDGER--><div class=\"hint\">暂无结算记录</div><!--/POOLLEDGER-->"
    blocks=[('<div class="hint">台账式归档:最新结算展开,历史折叠(只加不删);数据=竞价池结算_{d}.json(脚本产出,agent不改数)。'
             '池=发出版冻结名单,执行口径=T+1开→T+1收。</div>')]
    for i,d in enumerate(ds):
        disp=d[4:6]+"-"+d[6:8]
        cp=os.path.join(L,f"竞价池结算卡_{d}.html")
        card=open(cp,encoding="utf-8").read() if os.path.isfile(cp) else '<div class="hint">结算卡缺失</div>'
        ip=os.path.join(L,f"竞价池洞察_{d}.html")  # agent按日洞察card,自动嵌该日折叠内(跟着当天走)
        if os.path.isfile(ip): card+=open(ip,encoding="utf-8").read()
        z=json.load(open(os.path.join(L,f"竞价池结算_{d}.json"),encoding="utf-8")).get("汇总",{})
        brief=f'池{z.get("池家数","?")}只 · 封板{z.get("次日封板","?")} · 胜率{z.get("执行胜率","?")} · 均收{z.get("执行均收","?")}%'
        op=' open' if i==0 else ''
        tag='最新' if i==0 else '存档'
        blocks.append(f'<details class="chain"{op}><summary><b>{disp}池终结算</b> <span class="chip">{tag}</span> '
                      f'<span class="mut">{brief}</span></summary><div class="inner">{card}</div></details>')
    return "<!--POOLLEDGER-->"+"".join(blocks)+"<!--/POOLLEDGER-->"

def inject(block):
    js=sorted(glob.glob(os.path.join(L,"judgment_*.json")))
    if not js: print("无judgment"); return
    jp=js[-1]; J=json.load(open(jp,encoding="utf-8")); a=J["bodies"]["auction"]
    if "<!--POOLLEDGER-->" in a:
        a=re.sub(r'<!--POOLLEDGER-->.*?<!--/POOLLEDGER-->',lambda m:block,a,flags=re.S)
    else:
        m=re.search(r'<h2[^>]*>(?:三|二) 昨日[^<]*</h2>',a)
        if not m: print("段二锚未找到,未注入"); return
        a=a[:m.end()]+block+a[m.end():]
    J["bodies"]["auction"]=a
    json.dump(J,open(jp,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("已注入",os.path.basename(jp),"POOLLEDGER区(记得重跑生成盯盘台.py)")

if __name__=="__main__":
    block=build()
    open(os.path.join(L,"竞价池结算档.html"),"w",encoding="utf-8").write(block)
    print("竞价池结算档.html 已生成")
    if "--inject" in sys.argv: inject(block)
