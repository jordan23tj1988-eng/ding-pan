# -*- coding: utf-8 -*-
"""hb-b 10:30 场: 写 临盘决断_20261020_1030.json (发出版, write前 assert 不存在) + 报警 jsonl。"""
import json, os, urllib.request, datetime

ROOT = r'D:\股票数据\市场数据'
D = '20261020'
BASE = os.path.join(ROOT, '盘中', D)
TGT = os.path.join(BASE, '临盘决断_%s_1030.json' % D)
assert not os.path.exists(TGT), '发出版已存在, 禁覆盖'

UA = {'User-Agent': 'Mozilla/5.0'}


def snap(codes):
    u = 'https://qt.gtimg.cn/q=' + ','.join(codes)
    raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=10).read().decode('gbk', 'ignore')
    out = {}
    for line in raw.strip().split('\n'):
        if '="' not in line:
            continue
        f = line.split('="')[1].strip('";').split('~')
        out[f[2]] = dict(code=f[2], name=f[1], px=float(f[3]), pre=float(f[4]), open=float(f[5]),
                         high=float(f[33]), low=float(f[34]), pct=float(f[32]), amt_wan=float(f[37]),
                         t=f[30], bid1=f[9], ask1=f[19])
    return out


tick_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
S = snap(['sh600668', 'sz000823', 'sz000601', 'sz002343', 'sh603286', 'sh603278', 'sh000001', 'sz399006'])
json.dump({'fetch_ts': tick_at, '用途': 'px_exec 定价用决断后首帧快照(不用于方向判断)',
           'url': 'qt.gtimg.cn 逐码', 'rows': S},
          open(os.path.join(BASE, '_hb_b_tick_after_dec.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)


def fill(code, shares, buy_px, buy_date, leg, cls, why, ev, account='master'):
    t = S[code]
    px = round(t['px'] * 0.999 + 1e-9, 2)
    amt = round(px * shares, 2)
    return {"ev": "sell", "d": D, "code": code, "name": t['name'], "shares": shares,
            "px_exec": px, "tick_px": t['px'], "tick_at": tick_at, "slippage_pct": -0.1,
            "amt": amt, "buy_px": buy_px, "buy_date": buy_date,
            "pnl_gross": round((px - buy_px) * shares, 2),
            "ret_pct_gross": round((px / buy_px - 1) * 100, 2),
            "leg": leg, "cls": cls, "account": account, "why": why, "evidence": ev}


fills = [
    fill('600668', 6100, 8.15, '20261016', 'T_open_catchup', 'A',
         '预案 leg=open 机械清仓(10/19 收盘 8.06 < 失效线 8.15), 09:25 未执行 → 本场(10:34)补执行',
         'playbook(盘中/20261019/playbook.json).sells[1]=600668 6100股 leg=open; 今日盘中/20261020/ 无 执行流水.jsonl、无 09:25/09:40 决断件(hb-a 09:40:19 completed 但只落 _hb_a_quote_0941.json) → 漏执行成立'),
    fill('000823', 400, 25.13, '20261015', 'T_partial_defense', 'B',
         '持仓炸板减半锁利: 09:48 触板 27.18(+10.00%) → 10:34 26.37(+6.72%), 46 分钟未回封; 今日 1 小时成交 32.2 亿≈昨日全日(144.1万手)九成 → 巨量分歧',
         '分钟线 0930=24.01(-2.83%)/0948=27.18(涨停价 24.71×1.10)为日内最高/1034=26.37; 原失效条件=收盘跌破 MA20 23.706(未触及) → 不做清仓改判, 仅减半, 余 400 股仍按原收盘判据结算, 不新增盘中止损参数'),
]

doc = {
    "date": D,
    "session": "hb-b",
    "ts": "10:30",
    "write_ts": tick_at,
    "version": 1,
    "发出版": True,
    "场次说明": ("本场=20261020 周二 10:30 趋势确认段心跳(cron aee9c2fb913b, claimed 10:30:19)。"
              "★零后视镜: 方向判断只用 ≤10:30:19 已留档数据(实时帧末帧 10:30:19、池截面、分钟线 ≤10:34、预案原文); "
              "本场唯一『决断后』取数=%s 快照, 仅用于 fills 定价(px_exec), 不用于方向判断。"
              "★发出版不可覆盖: 写前 os.path.exists 判定 NOT-EXISTS(盘中/%s/临盘决断_%s_1030.json 不存在) → 首次占用, 既有 0921 场两件未触碰。"
              "★盘中禁改参数: 本场未修改任何生产脚本/预案/阈值, playbook 原文引用。" % (tick_at, D, D)),
    "交易日校验": {
        "规格命令": "python -c \"from sentiment.core.calendar import is_trading_day,today_str;print(...)\" → FAIL: ModuleNotFoundError: No module named 'sentiment'",
        "备注": "规格漂移连续登记(自 20260917, 见 盘中/20261019/临盘决断_20261019_0921.json#交易日校验), 非本场故障; 本场不因命令失败早退。",
        "本机等效真源": "本日 09:14 管道启动、09:15 起落竞价帧、09:31 起落实时帧 60 帧至 10:30:19, 池内 46 票 pct 真实分化; 交易日判定=是(2026-10-20 星期二)"
    },
    "数据新鲜度": {
        "实时帧": {"来源": "盘中/%s/realtime_ticks.jsonl" % D, "首帧": "2026-10-20 09:31:08",
                 "末帧": "2026-10-20 10:30:19", "帧数": 60, "采样间隔分钟": 1,
                 "断更分钟": 3.7, "判定": "末帧距决断时刻 3.7 分钟 < 10 分钟门槛 → 允许决策"},
        "pulse_json": "缺(今日目录无 pulse.json; 口径同 10/19 hb-c 登记: 新鲜度真源=realtime_ticks 帧龄)",
        "warboard_json": "缺(今日无 warboard.json; 本场决策输入=playbook+master账本+实时帧, 不依赖 warboard)",
        "执行流水_jsonl": "缺(今日无执行流水.jsonl) → 与『09:25 预案 open 腿未执行』互为印证, 属执行层缺环而非数据源故障",
        "报警_jsonl": "本场新增 1 条(见 盘中/%s/报警_%s.jsonl, type=intraday_open_leg_missed)" % (D, D),
        "池": {"pool_date": "20261019", "pool_kind": "zt_pool", "票数": 46, "pool_stale": False}
    },
    "执行层": {
        "09:14": {"job": "b8e2f1f39fd3 sentiment-intraday-pipeline", "status": "completed"},
        "09:21": {"job": "c7f1e0b2e8da sentiment-intraday-preread", "status": "completed", "产物": "临盘决断_20261020_0921.json(+补正1)"},
        "09:40": {"job": "ca64a4e51d42 sentiment-intraday-hb-a", "status": "completed(09:42:10)", "产物": "仅 _hb_a_quote_0941.json, 无 临盘决断_20261020_0940.json、无 fills"},
        "10:30": {"job": "aee9c2fb913b sentiment-intraday-hb-b", "status": "running(本场)"},
        "后果": "预案 open 腿(600668 6100股)自 09:25 起无成交留档, 至本场 10:34 补执行, 延迟约 69 分钟; 成交价 7.81 较开盘 8.11 低 3.70%"
    },
    "环境": {
        "池内截面": {
            "09:31": {"封板": 9, "中位pct": 1.02, "均值pct": 2.23, "上涨": 26, "下跌": 20},
            "10:30": {"封板": 14, "中位pct": 2.57, "均值pct": 3.58, "上涨": 29, "下跌": 16, "高开≥5": 18}
        },
        "炸板": {"触板未封": 3, "名单": ["600148 长春一东(曾触9.99→7.98)", "603693 江苏新能(曾触9.98→0.67)", "002889 东方嘉盛(曾触9.97→2.99)"],
               "盘中炸板率": "3/(14+3)=17.6%(代理口径)"},
        "跌停": "主板 0 只(300798 锦鸡股份 -12.39% 属创业板 20% 板, 不计跌停)",
        "批量跳水": "单帧(1分钟)跌幅≥3pp 家数≥3 的事件 0 次 → 无题材批量跳水(注: 帧间隔 1 分钟, 『2分钟内』口径按 1 分钟代理)",
        "指数": "上证 %s(%+.2f%%) / 创业板 %s(%+.2f%%)" % (S['000001']['px'], S['000001']['pct'], S['399006']['px'], S['399006']['pct']),
        "判读": "池内 09:31→10:30 封板 9→14、中位 1.02→2.57: 冰点次日(昨日温度14.0)修复在推进且无批量跳水; 但指数分化(上证平/创业板+0.6%)、炸板率仍 17.6%, 属『修复初段』不足以上调档位; 本场不因回暖加仓、不因个别炸板改全局。"
    },
    "条件决断": {
        "买入": [{
            "code": "—", "name": "—", "verdict": "零买入(预案 buys=[] + 观察票机械核均不成立)",
            "detail": ("①603278 大业股份: 预案 10:30 闸门『机器人宽度≥6 且 线内3板≥1 且 10:30前首封≥2』→ 实测宽度 5<6(线内9只映射, 封 5: 605488/603626/002164/603278/603119; 未封 4: 301119 +2.65/603040 +1.11/603286 +6.55/003021 +7.75) → 不成立; "
                       "且该票开盘 gap +10.00% 越 buy_gate 上沿 +3%、一字全程未开(open=high=low=11.99) → 预案明令『禁接力一字』, 本场不买、不转荐票。"
                       "②603286 日盈电子: 执1 +6.72%≥+3% ✓、开盘 42.31 vs 昨收 42.74=-1.01% 非一字 ✓, 但『净买占比≤20%』只有收盘后可知 → 2/3 成立, 且预案 confirm 出口是『转荐票』(次日口径)非当日买入 → 只登记不买。"
                       "③002343 慈文传媒: 执1 -0.97%, 距 confirm +3% 未达、距 falsify -3% 未达 → 观察继续。fills=空。")
        }],
        "卖出": fills
    },
    "预案清仓清单核销": [{
        "code": "600693", "name": "东百集团", "shares": 4000, "verdict": "废单·不执行(已于 20261019 11:08 成交)",
        "证据": "报警_20261019.jsonl fills: 600693 4000@8.95 cls=B; _学习/_模拟盘/master/状态.json(date=20261019) 持仓仅 000601/000823/600668 → 本票已不在持",
        "说明": "今日预案(playbook date=20261019 19:31)仍把 600693 列为 leg=open 清仓 → 生成端读旧账本导致重复卖单; 卖出不持有标的=废单, 本场不执行、不改预案文件"
    }, {
        "code": "603968", "name": "醋化股份", "shares": 2100, "verdict": "废单·不执行(已于 20261019 11:08 成交)",
        "证据": "报警_20261019.jsonl fills: 603968 2100@12.73 cls=A; master 状态.json(20261019) 已不含本票",
        "说明": "同上; 本票今日 -8.34%(11.54, 日内低 11.46), 昨日 12.73 出清较今日现价高 9.2% → 昨日补执行有效, 不可因今日走势倒推为错误(零后视镜)"
    }],
    "在持票照会": [{
        "code": "000601", "name": "韶能股份", "shares": 6000, "buy_px": 6.68,
        "action": "继续持有(不下卖单)",
        "detail": "现价 %s(%+.2f%%), 日内低 6.28/高 6.56, 成本 6.68 → 成本起算 -4.79%%。预案失效条件文本『收盘跌破MA10 6.275 / 跌破6.45』对 6.45 是收盘还是盘中口径有歧义 → 本场按收盘口径不从盘中预支(与 10/19 hb-c『intraday.stop_pct=null 无盘中止损授权』一致), 如实登记歧义; 若 14:45/收盘场确认收盘破 6.45/6.275 则次日开盘腿清仓。" % (S['000601']['px'], S['000601']['pct'])
    }, {
        "code": "000823", "name": "超声电子", "shares": 800, "buy_px": 25.13,
        "action": "减半 400 股(B级), 余 400 股按原失效条件(收盘跌破 MA20 23.706)结算",
        "detail": "见 条件决断.卖出[1]; 现价 %s(%+.2f%%), 日内高 27.18(涨停价)、低 23.90。减半理由=炸板不回封+巨量分歧, 不改其趋势判据、不预支收盘结论。" % (S['000823']['px'], S['000823']['pct'])
    }, {
        "code": "600668", "name": "尖峰集团", "shares": 6100, "buy_px": 8.15,
        "action": "清仓 6100 股(A级, 预案 open 腿补执行)",
        "detail": "见 条件决断.卖出[0]; 现价 %s(%+.2f%%), 开盘 8.11、日内低 7.71、成本 8.15。" % (S['600668']['px'], S['600668']['pct'])
    }],
    "观察票照会": [{
        "code": "002343", "name": "慈文传媒", "verdict": "观察继续(不买)",
        "detail": "09:21 场读数 -9.26%%(9.31) → 实际开盘 10.19(-0.68%%), 差 8.58pp; 现价 %s(%+.2f%%), 日高 10.44。★认知登记: 09:21 竞价读数对开盘的外推力被证伪(不可撤单段内价格由 9.31 被撤回/买回至 10.19), 09:21 场『预判除名』属过度外推; 本场不改预案、不改台账, 收盘按实际 执1 与封板率机械结算。" % (S['002343']['px'], S['002343']['pct'])
    }, {
        "code": "603286", "name": "日盈电子", "verdict": "观察(2/3 成立, 差收盘净买占比)",
        "detail": "现价 %s(%+.2f%%), 开 42.31 非一字; confirm 第三腿(净买占比≤20%%)待收盘" % (S['603286']['px'], S['603286']['pct'])
    }, {
        "code": "603278", "name": "大业股份", "verdict": "10:30 闸门未达成(宽度 5<6) → 不转荐票; falsify 未触发(一字未断板)",
        "detail": "一字 +10.00%(11.99) 全天未开; 宽度映射源=_学习/题材归位_20261019.json(仅覆盖昨日涨停池 46 票) → 今日新晋封板若属机器人线则未计入, 宽度 5 为下界, 待收盘全量映射复核"
    }],
    "撮合口径": {
        "px_exec": "决断后首帧实时快照价 × (1-0.10%) 卖出滑点",
        "tick_at": tick_at,
        "整手": "卖出股数均 100 整数倍(6100/400)",
        "费用": "pnl 记毛差价, 未扣佣金/印花税/过户费(沿用 10/19 hb-c 口径, 不猜费用模型)",
        "成交假设": "本场 fills 为纸上撮合(快照价+滑点), 盘口 600668 bid1 %s / 000823 bid1 %s" % (S['600668']['bid1'], S['000823']['bid1'])
    },
    "异常与欠账": [
        "① 执行层缺环(本场主因): 预案 open 腿 600668 自 09:25 无任何成交留档, hb-a(09:40 completed)只落 quote 文件不落决断件/fills → 补执行延迟 69 分钟、少收 3.70%。建议在 hb-a 场加『playbook.sells 全量核销断言』(有腿未核销即 FAIL 报警), 而非依赖后续场次兜底。",
        "② pulse.json / warboard.json / 执行流水.jsonl 三缺(连续第二日) → 执行审计链只能靠账本+fills 自建; 建议管道端补写空壳文件以区分『无内容』与『无产物』。",
        "③ 预案落盘目录错位: 今日 盘中/20261020/ 无 playbook.json, 实件在 盘中/20261019/playbook.json(date=20261019, 19:31) → 执行日目录缺件; 本场按内容认定退化读, 不改文件。",
        "④ 预案清仓清单与账本冲突: 600693/603968 已于 10/19 11:08 成交, 仍列今日 open 腿 → 若不核销会造成重复卖单; 建议生成端以 master 状态.json 现持仓取交集。",
        "⑤ 机器人宽度映射仅覆盖昨日涨停池(46 票), 今日新晋封板不可归属 → 宽度为下界, 闸门判定存在漏计风险(本场 5 vs 门槛 6, 差 1 只, 结论可能翻转); 收盘须用全量映射复核并回填本场判定。",
        "⑥ 000601 失效条件『跌破6.45』口径歧义(收盘/盘中)连续两场未澄清 → 建议在 playbook 字段拆为 close_below / intraday_stop_pct 两键, intraday 为空即禁止盘中卖。",
        "⑦ 交易日校验规格命令连续 FAIL(ModuleNotFoundError: sentiment) → 建议工程侧改 prompt 为本机 trading_calendar.py 或补包。"
    ],
    "权限分级": {
        "A": "1 笔: 600668 6100股 leg=open 预案内机械清仓(catch_up), 未改闸门/未改参数",
        "B": "1 笔: 000823 400股 减半(预案外·持仓炸板防守), 触发证据已写(触板27.18→26.37未回封46分钟+1小时成交≈昨日全日九成); 未新增多头暴露",
        "C": "无。零买入: 603278 宽度5<6 且 gap+10%/一字禁接力, 603286 缺收盘净买占比, 002343 未达 confirm"
    },
    "下一场": {
        "在持": "000601 6000(成本6.68) / 000823 400(成本25.13, 已减半); 600668/600693/603968 已于本场/10-19 出清, 后续场次不得重复下卖单",
        "待办": "11:00 hb-c: ①核 000823 剩余 400 是否回封(≥27.18)否则维持收盘口径 ②000601 vs 6.45/6.275 收盘口径 ③603278 宽度收盘全量复核 ④603286 净买占比",
        "半日收尾": "若 11:00 前出现『池内封板数回落至≤10 且 炸板≥6』则半日档位下调, 需在 hb-c 写防守升级证据"
    }
}

json.dump(doc, open(TGT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('WROTE', TGT, os.path.getsize(TGT))

alarm = os.path.join(BASE, '报警_%s.jsonl' % D)
line = {"ts": tick_at, "session": "hb-b_1030", "level": "ALARM", "type": "intraday_open_leg_missed",
        "scope": "intraday_chain",
        "detail": ("预案 open 腿 600668 6100股(leg=open, 依据 10/19 收盘 8.06<失效线 8.15)自 09:25 起无成交留档: 今日无 执行流水.jsonl, "
                   "hb-a(09:40:19 completed)只落 _hb_a_quote_0941.json, 无 0940 决断件/fills → 漏执行。本场(hb-b 10:34)按 A 级 catch_up 补执行 "
                   "6100@7.81(=决断后首帧 7.82 ×(1-0.10%)), 较开盘 8.11 少收 3.70%(约 1,830 元)。同时核销预案内 600693/603968 两条重复卖单"
                   "(两票已于 20261019 11:08 hb-c 成交, master 账本已不持有)。另: 000823 触板27.18(09:48)→26.37(10:34) 炸板不回封, "
                   "按 B 级减半 400@26.34。数据源: realtime_ticks 60帧至 10:30:19(帧龄3.7分钟, 未断更)。"),
        "decision_file": "盘中/%s/临盘决断_%s_1030.json" % (D, D),
        "fills": [{"code": f['code'], "name": f['name'], "shares": f['shares'], "px": f['px_exec'], "cls": f['cls']} for f in fills],
        "voided": [{"code": "600693", "shares": 4000, "reason": "已于20261019 11:08成交8.95"},
                   {"code": "603968", "shares": 2100, "reason": "已于20261019 11:08成交12.73"}],
        "amount_recap": round(sum(f['amt'] for f in fills), 2)}
with open(alarm, 'a', encoding='utf-8', newline='\n') as fh:
    fh.write(json.dumps(line, ensure_ascii=False) + '\n')
print('ALARM', alarm)
for f in fills:
    print(f['code'], f['shares'], 'px_exec', f['px_exec'], 'tick', f['tick_px'], 'amt', f['amt'], 'pnl', f['pnl_gross'], f['ret_pct_gross'])
