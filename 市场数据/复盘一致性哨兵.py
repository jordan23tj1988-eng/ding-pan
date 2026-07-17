# -*- coding: utf-8 -*-
"""复盘一致性哨兵.py {d} —— 出页后最后一道自动化检查(2026-07-15晚事故催生)。
动机: 数据补齐后"判断层修了、展示层stale"散在5处逐个被用户抓——人记不住就让机器查。
检查项:
  C1 页面残留缺口叙述词(网络不可达/未刷新/沿用0714式旧标记/null溢价)
  C2 PAPERTRADE头部累计% == _模拟盘/{route}/状态.json 累计pct(数字必须出自引擎)
  C3 看板_{d}.html mtime >= bars_cache最新mtime(旧价看板被inject=07-15事故根因)
  C4 bars_cache当日覆盖率(涨停池+荐票股+持仓股必须100%到{d})
  C5 发出版结算字段非全None(结算跑过且有效)
  C6 HTML结构完好+时间线折叠  C7 脚本产出卡陈旧嵌入
  C8 改动登记核对(正式.py/规格/规范mtime晚于_变更总账.md=改了没登记;2026-07-16改动三合一)
  C9 台账最新日块日期对账(涨停/龙虎榜=d,竞价=dprev;台账脚本--from-data漏日期会静默跳过当日日块=2026-07-16龙虎榜事故)
退出码: 0=全过 1=有FAIL(打印明细,流水线应停下重看)
"""
import os,sys,glob,json,re,datetime

R=None
for g in glob.glob('/sessions/*/mnt/股票数据/市场数据'):
    R=g;break
if R is None and os.path.isdir(r'D:\股票数据\市场数据'): R=r'D:\股票数据\市场数据'
L=os.path.join(R,'_学习');SITE=os.path.join(R,'复盘','盯盘台')
d=sys.argv[1] if len(sys.argv)>1 else datetime.date.today().strftime('%Y%m%d')
dprev_dirs=sorted([x for x in os.listdir(R) if x.isdigit() and len(x)==8 and x<d])
dprev=dprev_dirs[-1] if dprev_dirs else None
FAIL=[];WARN=[]

# ---------- C1 页面残留缺口叙述 ----------
pages=['index','cycle','auction','lhb','theme','logic','limitup']
# ★07-15晚二次事故修正: 必须在**去HTML标签后的纯文本**上匹配(标签夹隔曾漏"溢价 <b>null</b>");
# 词表加"不可达"泛化(曾因文案是"源不可达"而非"网络不可达"漏抓)。
pats=[r'不可达',r'网络未刷新',r'未刷新沿',r'沿用'+ (dprev or '00000000'),
      r'溢价\s*null',r'null\s*[\(（]源',r'结算\s*(全)?None',r'价源\s*null',r'数据缺口待补',r'挂起未重训']
for p in pages:
    f=os.path.join(SITE,p+'.html')
    if not os.path.isfile(f): FAIL.append(f'C1 {p}.html 不存在');continue
    h=open(f,encoding='utf-8').read()
    text=re.sub(r'<[^>]+>',' ',h)   # 去标签再查
    for pat in pats:
        m=re.search(pat,text)
        if m:
            ctx=text[max(0,m.start()-40):m.end()+30]
            FAIL.append(f'C1 {p}.html 残留"{pat}": …{" ".join(ctx.split())[:60]}…')

# ---------- C2 PAPERTRADE累计 vs 状态.json ----------
PAGE={'auction':'auction','lhb':'lhb','theme':'theme','logic':'logic','limitup':'limitup','master':'index'}
for route,pg in PAGE.items():
    sp=os.path.join(L,'_模拟盘',route,'状态.json')
    f=os.path.join(SITE,pg+'.html')
    if not (os.path.isfile(sp) and os.path.isfile(f)): WARN.append(f'C2 {route} 状态/页面缺,跳过');continue
    st=json.load(open(sp,encoding='utf-8'))
    cum=st.get('累计pct')
    if cum is None: WARN.append(f'C2 {route} 状态无累计pct');continue
    h=open(f,encoding='utf-8').read()
    i=h.find('PAPER TRADING')
    if i<0: FAIL.append(f'C2 {pg}.html 无PAPERTRADE段');continue
    seg=re.sub('<[^>]+>',' ',h[i:i+400])
    m=re.search(r'累计\s*([+-]?[0-9.]+)%',seg)
    if not m: FAIL.append(f'C2 {pg}.html 找不到累计%');continue
    page_v=float(m.group(1))
    if abs(page_v-float(cum))>0.005:
        FAIL.append(f'C2 {route} 页面累计{page_v}% != 状态.json {cum}%(旧看板被inject?先dashboard再inject)')

# ---------- C3 看板新鲜度 vs bars_cache ----------
bc=os.path.join(L,'_bars_cache')
try:
    cache_mtime=max(os.path.getmtime(os.path.join(bc,x)) for x in os.listdir(bc)[:400] if x.endswith('.csv'))
except Exception:
    cache_mtime=None
if cache_mtime:
    for route in PAGE:
        kb=os.path.join(L,'_模拟盘',route,f'看板_{d}.html')
        if os.path.isfile(kb) and os.path.getmtime(kb) < cache_mtime - 60:
            FAIL.append(f'C3 {route} 看板_{d}.html 早于bars_cache最新写入→旧价看板,须重跑 模拟盘引擎 dashboard {d} + inject {d}')

# ---------- C4 关键股当日bar覆盖 ----------
need=set()
zp=os.path.join(R,d,'zt_pool.csv')
if os.path.isfile(zp):
    import csv as _csv
    for row in _csv.DictReader(open(zp,encoding='utf-8-sig')):
        need.add(str(row.get('代码','')).zfill(6))
for f in glob.glob(os.path.join(L,f'*荐票_{d}.json'))+[os.path.join(L,f'竞价池发出_{d}.json')]:
    try:
        j=json.load(open(f,encoding='utf-8'))
        for it in (j.get('荐票') or j.get('池') or []):
            if isinstance(it,dict) and it.get('代码'): need.add(str(it['代码']).zfill(6))
    except Exception: pass
for route in PAGE:
    sp=os.path.join(L,'_模拟盘',route,'state.json')
    if os.path.isfile(sp):
        try:
            for pos in json.load(open(sp,encoding='utf-8')).get('positions',[]): need.add(pos['code'])
        except Exception: pass
dd=f'{d[:4]}-{d[4:6]}-{d[6:]}';miss=[]
for c in sorted(need):
    f=os.path.join(bc,c+'.csv')
    ok=False
    if os.path.isfile(f):
        try:
            with open(f,'rb') as fh:
                fh.seek(max(0,os.path.getsize(f)-200));t=fh.read().decode('utf-8','ignore')
            last=[l for l in t.strip().split('\n') if l][-1]
            ok=last.split(',')[0] in (dd,d)
        except Exception: pass
    if not ok: miss.append(c)
if miss:
    lvl=FAIL if len(miss)>max(3,len(need)*0.05) else WARN
    lvl.append(f'C4 关键股{len(need)}只中{len(miss)}只bars未到{d}: {miss[:8]}{"…" if len(miss)>8 else ""}')

# ---------- C5 昨日结算有效性 ----------
if dprev:
    empty=[]
    for name in ['质量荐票结算','题材荐票结算','逻辑荐票结算','席位荐票结算']:
        f=os.path.join(L,f'{name}_{dprev}.json')
        if not os.path.isfile(f): empty.append(name+':缺文件');continue
        try:
            j=json.load(open(f,encoding='utf-8'));s=json.dumps(j.get('汇总',{}),ensure_ascii=False)
            if re.search(r'\"执行均收\":\s*null',s) and '0/0' in s: empty.append(name+':0/0全None')
        except Exception as e: empty.append(name+':读失败')
    if empty: FAIL.append(f'C5 {dprev}结算无效: {empty}(bars_cache没补齐就跑了结算?)')

# ---------- C6 HTML结构完好+时间线折叠(07-15晚: 孤立<与折叠失效事故) ----------
for p in pages:
    f=os.path.join(SITE,p+'.html')
    if not os.path.isfile(f): continue
    h=open(f,encoding='utf-8').read()
    if '<</' in h or '><<' in h:
        FAIL.append(f'C6 {p}.html 存在孤立<(HTML被切坏,查_rt/_fold_tl不平衡守卫)')
    # 认知迭代tl条目>=2却没有tlfold=折叠失效
    for m in re.finditer(r'<div class="tl">',h):
        seg=h[m.start():m.start()+6000]
        nitems=len(re.findall(r'<div class="tli[^"]*">',seg[:seg.find('</details>') if '</details>' in seg else len(seg)]))
        if nitems>=2 and 'tlfold' not in h[max(0,m.start()-300):m.start()+6000]:
            FAIL.append(f'C6 {p}.html 时间线{nitems}条未折叠(应最新1条外露+其余进tlfold)')
        break

# ---------- C7 脚本产出卡陈旧嵌入(07-15晚: 先行指标卡重生成但页面嵌旧版,溢价柱显∅) ----------
_card=os.path.join(L,f'先行指标卡_{d}.html')
_cyc=os.path.join(SITE,'cycle.html')
if os.path.isfile(_card) and os.path.isfile(_cyc):
    _cc=open(_card,encoding='utf-8').read()
    _ph=open(_cyc,encoding='utf-8').read()
    if _cc not in _ph:
        FAIL.append('C7 cycle.html 嵌的先行指标卡≠最新卡文件(重跑过 情绪先行指标.py 后须把新卡整块替换回judgment cycle body)')

# ---------- C8 改动登记核对(2026-07-16 改动三合一: 改了不登记=FAIL) ----------
# 规则见 _链路地图.md 〇节: 正式.py/agent规格/四份规范 的mtime 不得晚于 _变更总账.md
_ledger=os.path.join(R,'_变更总账.md')
if not os.path.isfile(_ledger):
    WARN.append('C8 _变更总账.md 不存在,登记核对跳过')
else:
    _lm=os.path.getmtime(_ledger)+60  # 60s宽限
    _watch=[]
    for _f in os.listdir(R):
        _fp=os.path.join(R,_f)
        if _f.endswith('.py') and os.path.isfile(_fp) and not _f.endswith('.bak'):
            if _f.startswith('_'):
                WARN.append(f'C8 R根目录临时脚本残留 {_f}(规矩: 一次性脚本进 _tmp/,用完即弃)')
            else:
                _watch.append(_fp)
    for _pat in ('_agent规格/*.md',):
        _watch+=glob.glob(os.path.join(R,_pat))
    for _sf in ('_多agent重构_设计规范.md','_盯盘台组件规范.md','_模拟盘设计.md','_链路地图.md'):
        _fp=os.path.join(R,_sf)
        if os.path.isfile(_fp): _watch.append(_fp)
    _dirty=[os.path.basename(x) for x in _watch if os.path.getmtime(x)>_lm]
    if _dirty:
        FAIL.append(f'C8 改了没登记: {_dirty[:10]}{"…" if len(_dirty)>10 else ""} mtime晚于_变更总账.md——按改动三合一SOP补登记(_链路地图.md 〇节)后重跑哨兵')

# ---------- C9 台账最新日块日期对账(2026-07-16 龙虎榜台账漏当日荐票卡事故) ----------
# 根因: 台账脚本 --from-data 缺日期参数会静默跳过当日日块→页面停在昨日,肉眼难察。机器核对最新<summary>日块日期。
_jf=os.path.join(L,'judgment_%s.json'%d)
if not os.path.isfile(_jf):
    WARN.append('C9 judgment缺,台账日块核对跳过')
else:
    _bd=json.load(open(_jf,encoding='utf-8')).get('bodies',{})
    _md=d[4:6]+'-'+d[6:8]; _mp=(dprev[4:6]+'-'+dprev[6:8]) if dprev else None
    # (页面,锚,应等于的MM-DD,口径说明): 涨停/龙虎榜=当日荐票卡口径→d; 竞价=昨日池今日结算口径→dprev
    for _pg,_an,_exp,_ku in [('limitup','LEDGER',_md,'当日涨停归位'),('lhb','LHBLEDGER',_md,'当日席位荐票卡'),('auction','POOLLEDGER',_mp,'昨日池今日结算')]:
        if _exp is None: continue
        _b=_bd.get(_pg,''); _s=_b[_b.find('<!--%s-->'%_an):_b.find('<!--/%s-->'%_an)]
        _ds=re.findall(r'<summary><b>(\d\d-\d\d)',_s); _new=_ds[0] if _ds else None
        if _new!=_exp:
            FAIL.append('C9 %s %s 最新日块=%s 应=%s(%s)——台账脚本 --from-data 可能漏了日期参数,当日日块没建;补跑"台账脚本 %s --from-data"+dashboard+生成盯盘台+inject'%(_pg,_an,_new,_exp,_ku,d))

print(f'== 复盘一致性哨兵 {d} ==')
for w in WARN: print('  WARN',w)
if FAIL:
    for x in FAIL: print('  FAIL',x)
    print(f'结论: {len(FAIL)}项FAIL——不要通知完成,先修复再重跑哨兵');sys.exit(1)
print(f'结论: 全过({len(WARN)}警告)');sys.exit(0)
