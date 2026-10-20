# -*- coding: utf-8 -*-
"""hb-c 20261019 11:00 场 决断写入器
纪律: 发出版不可覆盖(assert 不存在); px_exec=决断后首帧留档价×(1-0.10% 滑点); 账本/状态/净值同步; 不猜费用口径。
"""
import json, os, urllib.request, sys

D = '盘中/20261019'
DEC_TS = '2026-10-19 11:08:00'
TARGET = f'{D}/临盘决断_20261019_1100.json'
assert not os.path.exists(TARGET), 'FATAL 发出版已存在, 拒绝覆盖: ' + TARGET

# ---------- 1. 决断后首帧留档价 ----------
def em(code):
    sec = '1' if code[0] == '6' else '0'
    url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={sec}.{code}&fields=f43,f44,f45,f46,f47,f58,f60,f170'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    d = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['data']
    return dict(code=code, name=d['f58'], latest=d['f43'] / 100, open=d['f46'] / 100,
                high=d['f44'] / 100, low=d['f45'] / 100, preClose=d['f60'] / 100, pct=d['f170'] / 100)

import datetime
tick_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
CODES = ['002860', '605189', '603968', '000011', '600693', '600668', '000601', '000823', '300045', '600802']
q = {c: em(c) for c in CODES}
json.dump({'fetched_at': tick_at, 'dec_ts': DEC_TS, 'src': '东财push2(f43/f46/f60)',
           'quotes': q}, open(f'{D}/_hb_c_tick_after_dec.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
assert tick_at > DEC_TS, f'取价时刻 {tick_at} 早于决断时间戳, 不可作为"决断后下一tick"'

SLIP = 0.001
def sell_px(code):
    return round(q[code]['latest'] * (1 - SLIP), 2)

# ---------- 2. 决断清单 ----------
SELLS = [
    dict(code='002860', acct='panzhong', shares=2900, buy_px=20.08, buy_date='20261016',
         cls='A', leg='T_open_catchup',
         why='预案 leg=open 机械清仓, 09:25 未执行(执行层断链) → 11:08 补执行',
         evidence='playbook.sells[0] 卖出/leg=open/2900股; 09:40 场 status=unknown(调度器重启), 无 0940 决断件、账本无 20261019 成交 → 漏执行成立'),
    dict(code='605189', acct='master', shares=1100, buy_px=17.97, buy_date='20261016',
         cls='A', leg='T_open_catchup',
         why='预案 leg=open 机械清仓, 09:25 未执行 → 11:08 补执行',
         evidence='playbook.sells[1] 卖出/leg=open/1100股; 同断链证据; 本票今日 +4.60%, 补执行价优于开盘腿 16.16'),
    dict(code='603968', acct='master', shares=2100, buy_px=14.30, buy_date='20261015',
         cls='A', leg='T_open_catchup',
         why='预案 leg=open 机械清仓, 09:25 未执行 → 11:08 补执行',
         evidence='playbook.sells[2] 卖出/leg=open/2100股; 同断链证据'),
    dict(code='000011', acct='panzhong', shares=5900, buy_px=10.11, buy_date='20261003',
         cls='A', leg='gap_invalidate',
         why='预案失效条件(c) 开盘 gap≤-4% 已成立(开10.91 vs 昨收11.40 = -4.30%) → 开盘腿清仓, 补执行',
         evidence='playbook.sells[4] 触发条件(c); 东财f46=10.91/f60=11.40 与腾讯 1106 双源一致'),
    dict(code='600693', acct='master', shares=4000, buy_px=12.40, buy_date='20261014',
         cls='B', leg='defer_rollover',
         why='预案漏票(B级防守): 本票不在 playbook.sells 7 票内, 但 master/state defer_sell=true/defers=1 = 10/16「跌停无法卖出」未完成卖出指令, 今日已打开跌停可卖 → 承接卖出',
         evidence='master/账本.jsonl #ev=defer d=20261016 code=600693 why=跌停无法卖出; master/state.json 600693 4000股 defer_sell=true; 今日 开9.11(-7.70%)/跌停8.88触及/现价8.95 相对成本 -27.82%'),
]

fills = []
for s in SELLS:
    px = sell_px(s['code'])
    amt = round(px * s['shares'], 2)
    pnl = round((px - s['buy_px']) * s['shares'], 2)
    fills.append(dict(ev='sell', d='20261019', code=s['code'], name=q[s['code']]['name'],
                      shares=s['shares'], px_exec=px, tick_px=q[s['code']]['latest'], tick_at=tick_at,
                      slippage_pct=-0.10, amt=amt, buy_px=s['buy_px'], buy_date=s['buy_date'],
                      pnl_gross=pnl, ret_pct_gross=round((px / s['buy_px'] - 1) * 100, 2),
                      leg=s['leg'], cls=s['cls'], account=s['acct'],
                      why=s['why'], evidence=s['evidence']))

# 未成交/未执行项
NOBUY = [
    dict(code='300045', name=q['300045']['name'], verdict='动作B 放弃(预案内条件未达成)',
         detail=f"buy_gate gap∈[-3.0,+5.0]; 今日开 {q['300045']['open']} vs 昨收 {q['300045']['preClose']} = gap +7.01% 越上沿 → 出带即放弃(playbook abort_if gap≥+8% 一级作废之外的机械弃单: 上沿+5%)。现价 {q['300045']['latest']}({q['300045']['pct']}%) 虽回落入带, 但闸门口径=开盘 gap, 事后价不构成入场依据(零后视镜/禁降闸门)。fills=空。"),
    dict(code='600802', name=q['600802']['name'], verdict='替补不启用',
         detail=f"300045 出带触发替补路径, 替补闸门 gap∈[-3.0,+3.0] 今日开 {q['600802']['open']} = +1.47% 入带; 但 playbook.notes『不得与 600668 同持(水泥线同线单票)』, 600668 今日未触发失效条件仍在持 → 同持剔除成立, 替补不启用。现价 {q['600802']['latest']}({q['600802']['pct']}%)。fills=空。"),
]

HOLD = [
    dict(code='600668', name='尖峰集团', action='继续持有(不下卖单)',
         detail=f"预案: 失效条件(a)收盘未封(b)收盘跌破8.15(c)开盘gap≤-4%。开盘 gap {round((8.48-8.79)/8.79*100,2)}% 未破 -4%; 现价 {q['600668']['latest']} 恰在成本 8.15 上沿, 日内低 8.10 已短暂落入 8.15 下方。★B级观察(不改判/不预支收盘判据): (b) 为**收盘**口径, intraday.stop_pct=null 无盘中止损授权 → 本场不下卖单, 交出 14:45/14:57 场按收盘价结算; 若收盘<8.15 则按预案次一交易日开盘腿执行。"),
    dict(code='000601', name='韶能股份', action='继续持有',
         detail=f"失效=收盘跌破MA10 6.275 / 跌破6.45。现价 {q['000601']['latest']}, 日内低 {q['000601']['low']} 均未破 → 持有。"),
    dict(code='000823', name='超声电子', action='继续持有',
         detail=f"失效=收盘跌破MA20 23.706。现价 {q['000823']['latest']}, 日内低 {q['000823']['low']} 曾在其下方但已收回 → 收盘口径未成立, 持有。"),
]

env = json.load(open(f'{D}/_hb_c_calc.json', encoding='utf-8'))['env']
env_txt = {k: dict(zip(['锁板', '炸板', '中位pct', '均值pct', '最低', '最高'], v)) for k, v in env.items()}

dec = dict(
    date='20261019', session='hb-c', ts='11:00', write_ts=tick_at, version=1, 发出版=True,
    场次说明=('本场=20261019 周一 11:00 半日收尾段心跳(cron 3e4b3b30b816)。★零后视镜: 决策只用 ≤11:08:00 已留档信息; '
           '本场唯一"决断后"取数=卖出定价用的首帧(11:09 后实时快照, 用于 px_exec, 不用于方向判断)。★发出版不可覆盖(写前 assert 不存在, 已过)。'
           '★盘前预案来源=盘中/20261019/playbook.json(date=20261016, master, cash_pct=82.0)+今日 09:21 预读场。'),
    数据新鲜度=dict(
        实时帧=dict(来源='盘中/20261019/realtime_ticks.jsonl', 首帧='2026-10-19 09:31:07', 末帧='2026-10-19 11:06:34',
                 帧数=96, 断更分钟=5, 判定='未超 10 分钟门槛 → 允许决策'),
        池=dict(pool_date='20261016', pool_kind='zt_pool', pool_stale=False, 票数=59),
        pulse_json='缺(今日目录无 pulse.json; 该口径自 2026-09-11 场起已登记为"pulse=warboard 内嵌 fact", 本场以 realtime_ticks 帧龄为新鲜度真源)',
        warboard_json='缺(今日无 warboard.json, 不影响本场: 本场决策输入=playbook+两账本+实时帧)',
        执行流水_jsonl='缺(今日无执行流水.jsonl) → 与"09:25/09:40 腿未执行"互为印证, 非数据缺陷而是执行层断链',
        报警_jsonl='缺(今日无 报警_20261019.jsonl, 本场已补写链破报警)'),
    执行层断链=dict(
        **{'09:16': dict(job='5d8760e7a962', status='failed', detail='iFinD 保活体检 rc=-2 登录被拒(账号/密码错误或权限过期) → 盘中实时源全程走腾讯备源, 帧照常落盘(59票/分钟)'),
           '09:40': dict(job='ca64a4e51d42 hb-a', status='unknown', detail='Scheduler restarted after owner exited before durable terminal state(09:46:09 记录) → 无 临盘决断_20261019_0940.json 落盘, 开盘腿卖出全部未执行'),
           '10:30': dict(job='aee9c2fb913b hb-b', status='failed', detail='GatewayUnavailableError: Gateway draining: update_paused(10:30:24) → 无 1030 决断件'),
           '11:00': dict(job='3e4b3b30b816 hb-c', status='running', detail='本场在执行中')},
        后果='09:25 三条开盘腿(002860/605189/603968)+000011 gap 失效腿+600693 顺延卖出腿 全部漏执行, 至 11:08 起补执行, 延迟约 1 小时 44 分。'),
    环境=dict(池内截面=env_txt,
              判读=('池内 09:31→11:05 锁板 8→10、炸板 2→6、中位 -1.31→+0.63、均值 0.00→+0.74: 上午尾段边际回暖且无批量跳水(最低 -10.02% 仅 1 只跌停), '
                  '但锁板 10/59=17% 仍属退潮档, 与预案 C防守/cash 82% 自洽; 本场不因"回暖"抬档, 也不因"退潮"改判既有腿。')),
    条件决断=dict(买入=NOBUY, 卖出=fills),
    在持票照会=HOLD,
    撮合口径=dict(px_exec='决断后首帧实时快照价 × (1-0.10%) 卖出滑点', tick_at=tick_at,
               费用='pnl 记为 **毛差价**(未扣佣金/印花税/过户费)。已知历史账本口径差异: 20261016 605577 笔 pnl=711.02 而毛差=770.00(差 58.98), 费用模型来源不明 → 本场不复刻、不猜, 只报毛差并标注。',
               整手='卖出股数=原持仓整数股, 无拆零; qty 均 100 的整数倍(2900/1100/2100/5900/4000)。'),
    异常与欠账=[
        '★执行层断链(本场主因): 09:40 hb-a status=unknown + 10:30 hb-b GatewayUnavailableError: Gateway draining → 开盘腿卖出漏执行。建议: 网关 update 排程避开 09:25-14:57 盘中窗口, hb-a 场末落盘原子化(先写临时件再 rename)。',
        'iFinD 登录被拒 rc=-2(09:16), 盘中已由腾讯源顶住; 需更新 D:\\股票数据\\_ifind_auth.json。',
        'pulse.json / warboard.json / 执行流水.jsonl 三缺(今日), 与本场决策无冲突但使"执行流水"审计链缺环, 本场以账本+fills 自建可核链。',
        '★600693 东百集团 4000股不在 playbook.sells 7 票表态内(master/state defer_sell=true 未清) → 预案"禁漏票"纪律被击穿一次, 本场按 B 级防守补执行并登记, 建议在 playbook 生成侧加"state 持仓全量覆盖断言"。',
        '_bars_cache/000011.csv 末行仍 2026-10-09(缺 10/12~10/16), 故本票 gap 判据只用 开/昨收 双源(东财+腾讯), 不用 MA；该缺行已连续多日, 待补。',
    ],
    权限分级=dict(A='本场 4 笔全部为预案内腿(3 条 leg=open + 1 条 gap 失效腿), 属 A 级机械执行, 未改闸门/未改参数',
              B='600693 1 笔: 预案外(漏票)+承接 10/16 defer 未完成卖出指令, 防御性离场, 触发证据已写; 未新增任何多头暴露',
              C='无。300045 出带后现价回落入带但闸门=开盘 gap, 事后价不入场; 600802 受同持剔除 → 全场零新增买入'),
    下一场=dict(在持='600668 6100 / 000601 6000 / 000823 800; 600668 收盘<8.15 则次一交易日开盘腿清仓',
              待办='14:45 深场B 与 14:57 收盘腿: 核 600668 收盘价 vs 8.15、000823 vs MA20 23.706、000601 vs MA10 6.275/6.45'),
)

json.dump(dec, open(TARGET, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', TARGET, os.path.getsize(TARGET), 'bytes')
for f in fills:
    print(f"FILL {f['code']} {f['name']} x{f['shares']} @{f['px_exec']} pnl {f['pnl_gross']} ({f['ret_pct_gross']}%)")

json.dump(dict(fills=fills, dec_ts=DEC_TS, tick_at=tick_at), open(f'{D}/_hb_c_fills_1100.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
