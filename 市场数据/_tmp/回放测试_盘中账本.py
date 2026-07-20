#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回放测试_盘中账本.py(一次性,②B验证):合成三日行情+流水+决断,断言结算全链路。ROOT=/tmp隔离,不碰真实账本。"""
import os, sys, json, shutil, importlib.util

SRC = None
for p in ['/sessions/clever-bold-newton/mnt/股票数据/市场数据/盘中账本结算.py']:
    if os.path.isfile(p): SRC = p
assert SRC, '找不到盘中账本结算.py'
TR = '/tmp/test_intra_root'
if os.path.isdir(TR): shutil.rmtree(TR)
D1,D2,D3,D0 = '99990102','99990103','99990104','99990101'
for d in (D0,D1,D2,D3): os.makedirs(os.path.join(TR,d))
bc = os.path.join(TR,'_学习','_bars_cache'); os.makedirs(bc)

def wbars(code, rows):
    with open(os.path.join(bc,code+'.csv'),'w',encoding='utf-8') as f:
        f.write('date,open,high,low,close,volume\n')
        for r in rows: f.write(','.join(str(x) for x in r)+'\n')
# 甲600001: D1买入 D2卖出
wbars('600001',[('9999-01-01',9.8,10.1,9.7,10.00,1e6),('9999-01-02',10.50,11.00,10.3,10.80,2e6),
                ('9999-01-03',11.00,11.6,10.9,11.50,2e6)])
# 乙600002: D1检查点买入 D2跌停封死defer D3开盘顺延卖
wbars('600002',[('9999-01-01',19.9,20.2,19.8,20.00,1e6),('9999-01-02',20.40,20.6,18.9,19.00,2e6),
                ('9999-01-03',17.10,17.10,17.10,17.10,5e5),('9999-01-04',17.50,17.8,17.2,17.60,1e6)])
# 丙600003: 一字涨停(影子拒单)
wbars('600003',[('9999-01-01',9.9,10.0,9.8,10.00,1e6),('9999-01-02',11.00,11.00,11.00,11.00,1e5),
                ('9999-01-03',12.1,12.1,11.5,12.00,1e5)])
# 丁600004: 高开8%越gate(影子闸门弃单)
wbars('600004',[('9999-01-01',9.9,10.1,9.8,10.00,1e6),('9999-01-02',10.80,11.0,10.5,10.60,1e6),
                ('9999-01-03',10.5,10.7,10.3,10.50,1e6)])
# 指数基准
os.makedirs(os.path.join(TR,'_学习'),exist_ok=True)
json.dump({'asof':D2,'sse_close':{D0:4000.0,D1:4040.0,D2:4020.0,D3:4030.0}},
          open(os.path.join(TR,'_学习','_指数基准.json'),'w',encoding='utf-8'))

def wintra(d, playbook, flows, decisions=None):
    p = os.path.join(TR,'盘中',d); os.makedirs(p,exist_ok=True)
    if playbook is not None:
        json.dump(playbook, open(os.path.join(p,'playbook.json'),'w',encoding='utf-8'), ensure_ascii=False)
    if flows is not None:
        with open(os.path.join(p,'执行流水.jsonl'),'w',encoding='utf-8') as f:
            for r in flows: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    if decisions:
        for name,obj in decisions.items():
            json.dump(obj, open(os.path.join(p,name),'w',encoding='utf-8'), ensure_ascii=False)

# ── D1: playbook(三票) + 引擎流水买甲 + 检查点买乙 + skip一条 ──
pb1 = {'routes':[
  {'route':'theme','buys':[
    {'code':'600001','name':'甲票','weight_pct':20,'reason':'测试主线',
     'trigger':{'type':'open_range','min_gap':-3,'max_gap':5}},
    {'code':'600003','name':'丙票','weight_pct':10,'reason':'一字测试',
     'trigger':{'type':'open_range','min_gap':-3,'max_gap':15}},
    {'code':'600004','name':'丁票','weight_pct':10,'reason':'gate测试',
     'trigger':{'type':'open_range','min_gap':-3,'max_gap':5}}],'sells':[]}]}
fl1 = [
 {'ts':'09:30:25','code':'600001','name':'甲票','action':'confirm','px':10.50,'rule':'trigger:open_range[-3,5]','route':'theme','note':'竞价确认'},
 {'ts':'09:30:55','code':'600001','name':'甲票','action':'fill_buy','px':10.52,'rule':'trigger:open_range[-3,5]','route':'theme',
  'note':'下一tick价成交;滑点0.10%→exec10.5305;费双边0.15%由模拟盘结算侧计;整手18900股(weight20%/本金100万)','px_exec':10.5305,'qty':18900},
 {'ts':'09:31:00','code':'600009','name':'戊票','action':'skip','px':None,'rule':'unparsed_skip','route':'lhb','note':'trigger不可机读,留人判'},
]
dec1 = {'临盘决断_%s_1000.json'%D1: {'date':D1,'session':'heartbeat_1000','ts':'10:00:00',
  'fills':[{'ts':'10:00:30','code':'600002','name':'乙票','action':'fill_buy','px':20.40,
            'px_exec':20.4204,'qty':4800,'rule':'watch_upgrade','route':'master','note':'watch升级买入 weight10%'}]}}
wintra(D1, pb1, fl1, dec1)

# ── D2: playbook卖甲(leg open);流水=盘中卖甲成交+乙跌停封死defer ──
pb2 = {'routes':[{'route':'theme','buys':[],'sells':[{'code':'600001','name':'甲票','leg':'open',
        'intraday':{'stop_pct':None,'take_zt':None}}]}]}
fl2 = [
 {'ts':'10:15:00','code':'600001','name':'甲票','action':'confirm','px':11.22,'rule':'sells:take_zt','route':'theme','note':'触发'},
 {'ts':'10:15:30','code':'600001','name':'甲票','action':'fill_sell','px':11.21,'rule':'sells:take_zt','route':'theme',
  'note':'下一tick成交;滑点0.10%','px_exec':11.1988},
 {'ts':'14:59:00','code':'600002','name':'乙票','action':'defer','px':17.10,'rule':'sells:stop_pct','route':'master',
  'note':'跌停封死(≈17.10),卖单顺延'},
]
wintra(D2, pb2, fl2)
# ── D3: 空playbook空流水,只做顺延+盯市 ──
wintra(D3, {'routes':[]}, [])

# ── 载入被测模块,指向测试ROOT ──
spec = importlib.util.spec_from_file_location('js', SRC)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.ROOT = TR; m._bcache.clear()

P=[];F=[]
def ck(name,cond,detail=''):
    (P if cond else F).append(name)
    print(('PASS ' if cond else '★FAIL ')+name+((' | '+detail) if detail and not cond else ''))

r = m.settle(D1); ck('S0 D1结算返回0', r==0)
nav = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','净值.json'),encoding='utf-8'))
st  = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','state.json'),encoding='utf-8'))
shs = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','shadow_state.json'),encoding='utf-8'))
zt  = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','状态.json'),encoding='utf-8'))

# 手算真腿D1: 买甲18900@10.5305 + 乙4800@20.4204,费0.05%
c1 = 18900*10.5305*1.0005; c2 = 4800*20.4204*1.0005
cash1 = 1_000_000 - c1 - c2
mv1 = 18900*10.80 + 4800*19.00
ck('S1 D1真腿两笔成交入账', len(st['positions'])==2 and st['positions'][0]['shares']==18900)
ck('S2 D1真腿现金精确(费0.05%)', abs(st['cash']-round(cash1,2))<0.02, '%s vs %s'%(st['cash'],round(cash1,2)))
ck('S3 D1真腿nav=盯市收盘', abs(nav[D1]['nav']-round((cash1+mv1)/1e6,6))<1e-6, str(nav[D1]['nav']))
# 影子D1: 甲gap+5%过gate买19000@10.50;丙一字拒;丁gap+8%闸门弃
sc1 = 19000*10.50*1.0005; scash1 = 1_000_000-sc1; smv1 = 19000*10.80
ck('S4 D1影子只成甲19000股', len(shs['positions'])==1 and shs['positions'][0]['shares']==19000, json.dumps(shs['positions'],ensure_ascii=False)[:200])
ck('S5 D1影子nav精确', abs(nav[D1]['sh_nav']-round((scash1+smv1)/1e6,6))<1e-6, str(nav[D1]['sh_nav']))
ck('S6 D1临盘增益pp对账', abs(nav[D1]['gain_pp']-round((nav[D1]['nav']-nav[D1]['sh_nav'])*100,2))<0.01)
ck('S7 skip进待人判', len(zt['待人判'])==1 and zt['待人判'][0]['code']=='600009')
ck('S8 weight从note解析', st['positions'][0].get('weight')==20.0, str(st['positions'][0].get('weight')))

r = m.settle(D2); ck('S9 D2结算返回0', r==0)
nav = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','净值.json'),encoding='utf-8'))
st  = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','state.json'),encoding='utf-8'))
shs = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','shadow_state.json'),encoding='utf-8'))
# 真腿D2: 卖甲18900@11.1988费0.10%;乙defer_sell待顺延,盯市@17.10
pro = 18900*11.1988*0.999
cash2 = cash1 + pro; mv2 = 4800*17.10
ck('S10 D2真腿甲平仓pnl正确', st['closed'] and abs(st['closed'][-1]['pnl']-round(pro-c1,2))<0.02, json.dumps(st['closed'][-1],ensure_ascii=False)[:150] if st['closed'] else 'empty')
ck('S11 D2乙defer_sell标记', len(st['positions'])==1 and st['positions'][0].get('defer_sell')==True)
ck('S12 D2真腿nav', abs(nav[D2]['nav']-round((cash2+mv2)/1e6,6))<1e-6, str(nav[D2]['nav']))
# 影子D2: 卖甲19000@开盘11.00
spro = 19000*11.00*0.999; scash2 = scash1+spro
ck('S13 D2影子按开盘卖出', len(shs['positions'])==0 and abs(nav[D2]['sh_nav']-round(scash2/1e6,6))<1e-6, str(nav[D2]['sh_nav']))
ck('S14 D2增益=口径差可见', abs(nav[D2]['gain_pp']-round((nav[D2]['nav']-nav[D2]['sh_nav'])*100,2))<0.01)

r = m.settle(D3); ck('S15 D3结算返回0', r==0)
nav = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','净值.json'),encoding='utf-8'))
st  = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','state.json'),encoding='utf-8'))
# D3: 乙顺延单开盘17.50成交
pro2 = 4800*17.50*0.999; cash3 = cash2 + pro2
ck('S16 D3顺延单开盘成交', len(st['positions'])==0 and st['closed'][-1]['code']=='600002' and st['closed'][-1]['sell_px']==17.50, json.dumps(st['closed'][-1],ensure_ascii=False)[:150])
ck('S17 D3真腿nav空仓=现金', abs(nav[D3]['nav']-round(cash3/1e6,6))<1e-6, str(nav[D3]['nav']))
ck('S18 D3乙defers计数=1', st['closed'][-1]['defers']==1)

# 幂等: 重跑D2不重复记账
nav_before = json.dumps(nav, sort_keys=True)
r = m.settle(D2)
nav2 = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','净值.json'),encoding='utf-8'))
ck('S19 幂等重跑净值不变', json.dumps(nav2,sort_keys=True)==nav_before)
st2 = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','state.json'),encoding='utf-8'))
ck('S20 幂等重跑closed笔数不变', len(st2['closed'])==len(st['closed']))
# 状态卡结构
zt = json.load(open(os.path.join(TR,'_学习','_模拟盘','intraday','状态.json'),encoding='utf-8'))
ck('S21 状态卡关键字段齐(nav/基准/增益/上证)', all(k in zt for k in ('nav','基准本周pct','临盘增益pp_累计','上证本周pct','胜率pct')), json.dumps(list(zt.keys()),ensure_ascii=False))

print('\n===== %d PASS / %d FAIL ====='%(len(P),len(F)))
sys.exit(1 if F else 0)
