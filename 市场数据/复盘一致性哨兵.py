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
  C10 obs卡×竞价验证对账(竞价验证明细>0但昨judgment index obs-jj全空=obs卡markup漂移,2026-07-17 E3事故)
  C11 ths涨停池新鲜度(最新日<当日=停更静默错数,2026-07-17 #008事故:先行指标日历跳回0710错数一周)
  C12 宿主取数日志新鲜度(傍晚日志缺=当日链路无米下锅;步骤rc非0列警;总账#012注的欠账,2026-07-18补)
  C13 盘中流水完整性(阶段②,#032:playbook有单但执行流水缺=引擎没跑;第七账净值缺当日=结算没跑;sells带stop缺ref_px列警)
  C14 盘中决断json与第七账账本一致性(阶段②,#032:决断fills必带px_exec且必须已入账本,否则结算漏读)
  C15 六账本跨日连续性(上一交易日每笔计划必须有当日账本事件,且执行回执已进页面)
  C16 早盘宿主内部步骤退出码(防计划任务外层返回0掩盖子步骤失败,2026-07-21编码事故)
  C17 竞价分桶库新鲜度(防circ_mv空值使回填异常退出却继续沿用旧库)
  C18 七页输出合同(段序/最低分析深度/职责字段/支持反证确认/未来日期)
  C19 结构化输出合同(judgment/归档/总审/playbook/临盘决断)
  C20 计划任务根漂移(生产日志缺失但runtime同日日志出现=宿主任务仍写迁移镜像)
退出码: 0=全过 1=有FAIL(打印明细,流水线应停下重看)
"""
import os,sys,glob,json,re,datetime,argparse

def _parse_date_arg():
    """Parse the optional review date before any filesystem checks run."""
    parser=argparse.ArgumentParser(
        prog='复盘一致性哨兵.py',
        description='运行指定交易日的情绪复盘一致性检查；不传日期时使用今天。')
    parser.add_argument('date',nargs='?',default=datetime.date.today().strftime('%Y%m%d'),
                        help='交易日 YYYYMMDD，例如 20260724')
    args=parser.parse_args()
    if not re.fullmatch(r'\d{8}',args.date):
        parser.error('date 必须是 YYYYMMDD 八位数字')
    return args.date

d=_parse_date_arg()

R=None
_SCRIPT_DIR=os.path.dirname(os.path.abspath(__file__))
_ENV_ROOT=os.environ.get('SENTIMENT_ROOT')
if _ENV_ROOT and os.path.isdir(_ENV_ROOT): R=os.path.abspath(_ENV_ROOT)
for g in glob.glob('/sessions/*/mnt/股票数据/市场数据'):
    if R is None: R=g
    break
if R is None and os.path.basename(os.path.dirname(_SCRIPT_DIR))!='ding-pan仓库' and os.path.isdir(os.path.join(_SCRIPT_DIR,'复盘')):
    R=_SCRIPT_DIR
if R is None and os.path.isdir(r'D:\股票数据\市场数据'): R=r'D:\股票数据\市场数据'
L=os.path.join(R,'_学习');SITE=os.path.join(R,'复盘','盯盘台')
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

# ---------- C10 obs卡×竞价验证对账(2026-07-17 E3: obs卡markup漂移→晨场脚本静默0/0) ----------
_vf=os.path.join(L,'竞价验证_%s.json'%d)
if dprev and os.path.isfile(_vf):
    try: _vv=json.load(open(_vf,encoding='utf-8'))
    except Exception: _vv={}
    if (_vv.get('观察点数') or 0)>0 or len(_vv.get('明细') or [])>0:
        _jp=os.path.join(L,'judgment_%s.json'%dprev)
        if os.path.isfile(_jp):
            _ib=json.load(open(_jp,encoding='utf-8')).get('bodies',{}).get('index','')
            _blocks=re.findall(r'class="obs-jj".*?</div>',_ib,re.S)
            def _c10_filled(b):
                _t=re.sub(r'<span class="jjtag">.*?</span>','',b)
                _t=re.sub(r'<[^>]+>','',_t)
                return bool(re.search(r'[0-9]',_t)) and ('未采集' not in _t)
            if not _blocks:
                FAIL.append('C10 竞价验证_%s 明细%d条>0 但 judgment_%s index无obs-jj块——晨场注入没跑或obs卡结构漂移(同步 竞价快线.parse_watchlist + 竞价上首页.inject_obs,见链路地图E3)'%(d,len(_vv.get('明细') or []),dprev))
            elif not any(_c10_filled(b) for b in _blocks):
                FAIL.append('C10 竞价验证_%s 明细>0 但 judgment_%s index的obs-jj全为—/未采集——obs卡markup漂移致晨场脚本静默解析0只(E3),修两parser后补注入'%(d,dprev))
        else:
            WARN.append('C10 judgment_%s 缺,obs对账跳过'%dprev)

# ---------- C11 ths涨停池新鲜度(2026-07-17 #008: 停更→先行指标/题材四维/质量训练静默错数) ----------
_tf=os.path.join(L,'_ths_zt_pool.json')
if not os.path.isfile(_tf):
    WARN.append('C11 _ths_zt_pool.json 不存在,新鲜度核对跳过')
else:
    _tmax=None
    try:
        _tk=sorted(json.load(open(_tf,encoding='utf-8')).keys())
        _tmax=_tk[-1] if _tk else None
    except Exception as _e:
        WARN.append('C11 ths池读取异常:%s'%str(_e)[:60])
    if _tmax and _tmax<d:
        FAIL.append('C11 _ths_zt_pool.json 最新=%s < 当日%s——THS池停更(#008静默错数源头):宿主跑 涨停池回填.py 补齐,再重跑 情绪先行指标.py {d}/题材四维/质量训练'%(_tmax,d))

# ---------- C17 竞价分桶库新鲜度(2026-07-21: circ_mv=None导致回填中断但旧库仍可被评分读取) ----------
_bf=os.path.join(L,'_竞价池分桶库.json')
if not os.path.isfile(_bf):
    FAIL.append('C17 _竞价池分桶库.json 不存在——竞价池分桶回填.py 未成功产库')
else:
    try:
        _bfo=json.load(open(_bf,encoding='utf-8'))
        _bend=str(_bfo.get('窗口') or '').split('~')[-1]
        _bupd=str(_bfo.get('更新') or '')[:10].replace('-','')
        if dprev and _bend<dprev:
            FAIL.append('C17 竞价分桶库窗口末日=%s < 前一交易日%s——回填失败或旧库未滚动,修复后重跑分桶→竞价评分'%(_bend,dprev))
        if _bupd<d:
            FAIL.append('C17 竞价分桶库更新时间=%s < 当日%s——当晚回填未成功完成'%(_bupd,d))
    except Exception as _e:
        FAIL.append('C17 竞价分桶库解析异常:%s'%str(_e)[:60])

# ---------- C12 宿主取数日志新鲜度(#012欠账,2026-07-18补;新机沙箱无外网,宿主没跑=无米下锅) ----------
_hl=os.path.join(L,'宿主取数日志_%s.json'%d)
if not os.path.isfile(_hl):
    FAIL.append('C12 _学习/宿主取数日志_%s.json 不存在——宿主傍晚取数(17:40计划任务)当日没跑:请用户双击 宿主取数_傍晚.bat 后重开链路,禁沙箱诊断网络'%d)
else:
    try:
        _hj=json.load(open(_hl,encoding='utf-8'))
        _bad=[s.get('script') for s in (_hj.get('steps') or []) if s.get('rc') not in (0,None)]
        if _bad:
            WARN.append('C12 宿主傍晚取数有失败步骤: %s(查宿主日志steps.rc,涉及数据消费方需核缺口)'%_bad[:6])
    except Exception as _e:
        WARN.append('C12 宿主日志读取异常:%s'%str(_e)[:60])
_ml=os.path.join(L,'宿主取数日志_早盘_%s.json'%d)
if not os.path.isfile(_ml):
    WARN.append('C12 早盘宿主日志缺(%s)——晨场快线/快照/闸门当日未跑或宿主9:24任务未触发(非傍晚链阻断项,列警)'%('宿主取数日志_早盘_%s.json'%d))

# ---------- C16 早盘宿主内部步骤退出码(2026-07-21: 外层返回0掩盖竞价闸门rc=1) ----------
if os.path.isfile(_ml):
    try:
        _mj=json.load(open(_ml,encoding='utf-8'))
        _msteps=_mj.get('steps') or []
        _mbad=[str(s.get('script')) for s in _msteps if s.get('rc') not in (0,None) and s.get('repair_rc') != 0]
        _mrepaired=[str(s.get('script')) for s in _msteps if s.get('rc') not in (0,None) and s.get('repair_rc') == 0]
        if _mbad:
            FAIL.append('C16 宿主早盘取数有失败步骤: %s——计划任务不得外绿内红,查宿主取数控制台.log与steps.rc后补齐晨场产物'%','.join(_mbad[:6]))
        if _mrepaired:
            WARN.append('C16 宿主早盘原失败步骤已有保留原rc的成功修复记录: %s'%','.join(_mrepaired[:6]))
    except Exception as _e:
        FAIL.append('C16 宿主早盘日志解析异常:%s'%str(_e)[:60])

# ---------- C20 计划任务根漂移(2026-07-27:宿主任务写runtime、复盘读生产) ----------
_shadow_root=r'D:\股票数据\codex_workspace\migration_20260722\runtime\市场数据'
if d>='20260727' and os.path.isdir(_shadow_root) and os.path.normcase(os.path.abspath(R))!=os.path.normcase(os.path.abspath(_shadow_root)):
    for _label,_name in (('傍晚','宿主取数日志_%s.json'%d),('早盘','宿主取数日志_早盘_%s.json'%d)):
        _prod_log=os.path.join(L,_name)
        _shadow_log=os.path.join(_shadow_root,'_学习',_name)
        if not os.path.isfile(_prod_log) and os.path.isfile(_shadow_log):
            FAIL.append('C20 %s宿主日志只出现在runtime镜像、生产目录缺失——计划任务Action根路径漂移;把%s任务重绑到D:\\股票数据\\市场数据后重跑'%(_label,_label))

# ---------- C13 盘中流水完整性(阶段②,#032;盘中/{d}/playbook.json在=盘中通道活跃日,缺=未上线跳过) ----------
_pb=os.path.join(R,'盘中',d,'playbook.json')
if os.path.isfile(_pb):
    try:
        _pbo=json.load(open(_pb,encoding='utf-8'))
        if isinstance(_pbo,dict) and isinstance(_pbo.get('routes'),list): _rts=_pbo['routes']
        elif isinstance(_pbo,list): _rts=_pbo
        elif isinstance(_pbo,dict): _rts=[_pbo]
        else: _rts=[]
        _nbuy=sum(len(p.get('buys') or []) for p in _rts if isinstance(p,dict))
        _nsell=sum(len(p.get('sells') or []) for p in _rts if isinstance(p,dict))
        _fl=os.path.join(R,'盘中',d,'执行流水.jsonl')
        if (_nbuy+_nsell)>0 and not os.path.isfile(_fl):
            FAIL.append('C13 盘中/%s/playbook有%d买%d卖但执行流水.jsonl不存在——盘中规则引擎当日没跑(查宿主计划任务),第七账当日成交缺失'%(d,_nbuy,_nsell))
        _noref=[str(o.get('code')) for p in _rts if isinstance(p,dict) for o in (p.get('sells') or [])
                if isinstance(o,dict) and (o.get('intraday') or {}).get('stop_pct') is not None and not o.get('ref_px')]
        if _noref: WARN.append('C13 playbook sells声明stop_pct但缺ref_px(v1.9.1裁定②,引擎将skip留人判;晚间发单prompt要带成本价): %s'%','.join(_noref[:5]))
        _nvp=os.path.join(L,'_模拟盘','intraday','净值.json')
        _nvo=json.load(open(_nvp,encoding='utf-8')) if os.path.isfile(_nvp) else {}
        if d not in _nvo:
            FAIL.append('C13 第七账净值.json缺当日%s——盘中账本结算.py settle %s 没跑(18:00链路步骤10b)'%(d,d))
    except Exception as _e:
        WARN.append('C13 盘中完整性检查异常:%s'%str(_e)[:60])

# ---------- C14 盘中决断json与第七账账本一致性(阶段②,#032) ----------
_decs=sorted(glob.glob(os.path.join(R,'盘中',d,'临盘决断_*.json')))
if _decs:
    _lgp=os.path.join(L,'_模拟盘','intraday','账本.jsonl')
    _seen=set()
    if os.path.isfile(_lgp):
        for _ln in open(_lgp,encoding='utf-8'):
            try:
                _ev=json.loads(_ln)
                if _ev.get('d')==d and _ev.get('acct')=='real': _seen.add(str(_ev.get('code')))
            except Exception: pass
    for _df in _decs:
        try: _do=json.load(open(_df,encoding='utf-8'))
        except Exception:
            FAIL.append('C14 %s 解析失败(决断json必须合法)'%os.path.basename(_df));continue
        for _f2 in (_do.get('fills') or []):
            if not isinstance(_f2,dict): continue
            _c=str(_f2.get('code','')).zfill(6)
            if _f2.get('action') in ('fill_buy','fill_sell'):
                if not _f2.get('px_exec'):
                    FAIL.append('C14 %s fills缺px_exec(决断接口铁律#031): %s'%(os.path.basename(_df),_c))
                if _c not in _seen:
                    FAIL.append('C14 决断成交未入第七账账本: %s(%s)——结算漏读或决断写在settle之后,按数据补齐SOP处理后重跑哨兵'%(_c,os.path.basename(_df)))

# ---------- C18 全系统输出合同(2026-07-26:浅页反复回退事故) ----------
_contract_paths=[os.path.join(R,'_情绪复盘输出合同.json'),
                 os.path.join(os.path.dirname(os.path.abspath(__file__)),'_情绪复盘输出合同.json')]
_contract_path=next((p for p in _contract_paths if os.path.isfile(p)),None)
if not _contract_path:
    FAIL.append('C18 缺 _情绪复盘输出合同.json——无合同不允许出页')
else:
    try:
        _contract=json.load(open(_contract_path,encoding='utf-8'))
        _universal=_contract.get('universal',{}).get('required_reasoning') or []
        for _page,_rule in (_contract.get('pages') or {}).items():
            _fp=os.path.join(SITE,_page+'.html')
            if not os.path.isfile(_fp): FAIL.append('C18 %s.html 不存在'%_page);continue
            _html=open(_fp,encoding='utf-8').read()
            _main=_html[_html.find('<h2'):_html.rfind('<script') if '<script' in _html else len(_html)]
            _plain=re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>',' ',_main,flags=re.I)
            _plain=re.sub(r'<[^>]+>',' ',_plain);_plain=re.sub(r'&nbsp;|\s+','',_plain)
            _heads=[re.sub(r'<[^>]+>','',m).strip() for m in re.findall(r'<h2[^>]*>([\s\S]*?)</h2>',_main,re.I)]
            _expected=_rule.get('headings') or []
            if len(_heads)!=int(_rule.get('h2',len(_expected))): FAIL.append('C18 %s 段数=%d,合同=%s'%(_page,len(_heads),_rule.get('h2')))
            for _i,_prefix in enumerate(_expected):
                if _i>=len(_heads) or not _heads[_i].startswith(_prefix):
                    _got=_heads[_i] if _i<len(_heads) else '缺段'
                    FAIL.append('C18 %s 第%d段应以“%s”开头,实际“%s”'%(_page,_i+1,_prefix,_got[:36]))
            _min=int(_rule.get('min_chars',0))
            if len(_plain)<_min: FAIL.append('C18 %s 可见正文%d字<合同%d字(脚本/样式不计)'%(_page,len(_plain),_min))
            for _term in (_rule.get('required') or []):
                if _term not in _plain: FAIL.append('C18 %s 缺职责字段“%s”'%(_page,_term))
            for _term in _universal:
                if _term not in _plain: FAIL.append('C18 %s 缺通用推理字段“%s”'%(_page,_term))
            for _ymd in re.findall(r'20\d{2}(?:[-/]\d{2}[-/]\d{2}|\d{4})',_plain):
                _norm=re.sub(r'\D','',_ymd)
                try: datetime.datetime.strptime(_norm,'%Y%m%d')
                except ValueError: continue
                if _norm>d: FAIL.append('C18 %s 含未来日期%s>复盘日%s'%(_page,_ymd,d));break
    except Exception as _e: FAIL.append('C18 输出合同读取/检查异常:%s'%str(_e)[:100])

# ---------- C19 结构化输出合同(judgment/归档/总审/盘中作战) ----------
if _contract_path:
    try:
        _structured=(_contract.get('structured_outputs') or {})
        def _plain_text(_value):
            _s=json.dumps(_value,ensure_ascii=False) if not isinstance(_value,str) else _value
            _s=re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>',' ',_s,flags=re.I)
            _s=re.sub(r'<[^>]+>',' ',_s)
            return re.sub(r'&nbsp;|\s+','',_s)
        def _has_any_key(_value,_keys):
            if isinstance(_value,dict):
                return any(_k in _value and _value.get(_k) not in (None,'',[],{}) for _k in _keys) or any(_has_any_key(_v,_keys) for _v in _value.values())
            if isinstance(_value,list): return any(_has_any_key(_v,_keys) for _v in _value)
            return False

        _jr=_structured.get('judgment') or {};_jp=os.path.join(L,'judgment_%s.json'%d)
        if not os.path.isfile(_jp): FAIL.append('C19 缺 judgment_%s.json'%d)
        else:
            _jo=json.load(open(_jp,encoding='utf-8'))
            for _k in (_jr.get('required_top') or []):
                if _k not in _jo: FAIL.append('C19 judgment缺顶层字段“%s”'%_k)
            _bodies=_jo.get('bodies') or {}
            for _page in (_jr.get('body_pages') or []):
                _body=_bodies.get(_page)
                if not _body: FAIL.append('C19 judgment.bodies缺%s'%_page);continue
                if _jr.get('reasoning_in_each_body'):
                    _txt=_plain_text(_body)
                    for _term in _universal:
                        if _term not in _txt: FAIL.append('C19 judgment.%s缺“%s”'%(_page,_term))
            _archive=_plain_text(_jo.get('archive_body',''))
            _amin=int(_jr.get('archive_min_chars',0))
            if len(_archive)<_amin: FAIL.append('C19 archive_body正文%d字<合同%d字'%(len(_archive),_amin))
            if _jr.get('archive_required_reasoning'):
                for _term in _universal:
                    if _term not in _archive: FAIL.append('C19 archive_body缺“%s”'%_term)

        _ar=_structured.get('audit') or {};_ap=os.path.join(L,'总审_%s.json'%d)
        if not os.path.isfile(_ap): FAIL.append('C19 缺 总审_%s.json'%d)
        else:
            _ao=json.load(open(_ap,encoding='utf-8'))
            for _k in (_ar.get('required_top') or []):
                if _k not in _ao: FAIL.append('C19 总审缺顶层字段“%s”'%_k)
            _checks=_ao.get('检查') or {}
            for _k in (_ar.get('required_checks') or []):
                if _k not in _checks: FAIL.append('C19 总审.检查缺“%s”'%_k)

        _pr=_structured.get('playbook') or {};_pb=os.path.join(R,'盘中',d,'playbook.json')
        if os.path.isfile(_pb):
            _po=json.load(open(_pb,encoding='utf-8'))
            for _k in (_pr.get('required_top') or []):
                if _k not in _po: FAIL.append('C19 playbook缺顶层字段“%s”'%_k)
            for _group in ('buys','sells','watch'):
                for _i,_item in enumerate(_po.get(_group) or []):
                    for _label,_keys in (('标识',_pr.get('item_identity_any') or []),('来源',_pr.get('item_source_any') or []),('确认',_pr.get('item_confirm_any') or []),('证伪',_pr.get('item_falsify_any') or [])):
                        if not _has_any_key(_item,_keys): FAIL.append('C19 playbook.%s[%d]缺%s字段'%(_group,_i,_label))

        _dr=_structured.get('decision') or {}
        for _df in glob.glob(os.path.join(R,'盘中',d,'临盘决断_%s_*.json'%d)):
            _do=json.load(open(_df,encoding='utf-8'));_dn=os.path.basename(_df)
            for _k in (_dr.get('required_top') or []):
                if _k not in _do: FAIL.append('C19 %s缺顶层字段“%s”'%(_dn,_k))
            if not _has_any_key(_do,_dr.get('timestamp_any') or []): FAIL.append('C19 %s缺决策时间'%_dn)
            for _label,_keys in (_dr.get('reasoning_anywhere') or {}).items():
                if not _has_any_key(_do,_keys): FAIL.append('C19 %s缺%s字段'%(_dn,_label))
            if _dr.get('fill_px_exec_required'):
                for _i,_fill in enumerate(_do.get('fills') or []):
                    if not isinstance(_fill,dict) or not _fill.get('px_exec'): FAIL.append('C19 %s fills[%d]缺px_exec'%(_dn,_i))
    except Exception as _e: FAIL.append('C19 结构化输出合同读取/检查异常:%s'%str(_e)[:100])

# ---------- C15 六账本跨日计划→执行→页面回执连续性(2026-07-21页面漏拒单事故) ----------
_routes=['auction','lhb','theme','logic','limitup','master']
_pages={'auction':'auction','lhb':'lhb','theme':'theme','logic':'logic','limitup':'limitup','master':'index'}
if dprev:
    for _route in _routes:
        _pp=os.path.join(L,'交易计划_%s_%s.json'%(_route,dprev))
        if not os.path.isfile(_pp): continue
        try: _plan=json.load(open(_pp,encoding='utf-8'))
        except Exception:
            FAIL.append('C15 %s上一交易日计划解析失败: %s'%(_route,os.path.basename(_pp)));continue
        _expected=[]
        for _o in (_plan.get('buys') or _plan.get('positions') or []): _expected.append(('buy',str(_o.get('code','')).zfill(6)))
        for _o in (_plan.get('sells') or []): _expected.append(('sell',str(_o.get('code','')).zfill(6)))
        _events=[];_lp=os.path.join(L,'_模拟盘',_route,'账本.jsonl')
        if os.path.isfile(_lp):
            for _ln in open(_lp,encoding='utf-8'):
                try:
                    _ev=json.loads(_ln)
                    if _ev.get('d')==d: _events.append(_ev)
                except Exception: pass
        _missing=[]
        for _act,_code in _expected:
            _valid=('buy','reject') if _act=='buy' else ('sell','defer')
            if not any(str(_e.get('code','')).zfill(6)==_code and _e.get('ev') in _valid for _e in _events): _missing.append('%s:%s'%(_act,_code))
        if _missing: FAIL.append('C15 %s %s计划→%s账本缺执行事件: %s'%(_route,dprev,d,','.join(_missing)))
        _pg=os.path.join(SITE,_pages[_route]+'.html')
        _html=open(_pg,encoding='utf-8').read() if os.path.isfile(_pg) else ''
        _a=_html.find('<!--EXECRECEIPT-->');_b=_html.find('<!--/EXECRECEIPT-->')
        if _a<0 or _b<_a:
            FAIL.append('C15 %s页面缺上一交易日指令执行回执'%_pages[_route]);continue
        _block=_html[_a:_b]
        _hidden=[_code for _,_code in _expected if _code not in _block]
        if _hidden: FAIL.append('C15 %s页面执行回执漏股票: %s'%(_pages[_route],','.join(_hidden)))

print(f'== 复盘一致性哨兵 {d} ==')
for w in WARN: print('  WARN',w)
if FAIL:
    for x in FAIL: print('  FAIL',x)
    print(f'结论: {len(FAIL)}项FAIL——不要通知完成,先修复再重跑哨兵');sys.exit(1)
print(f'结论: 全过({len(WARN)}警告)');sys.exit(0)
