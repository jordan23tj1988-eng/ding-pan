# -*- coding: utf-8 -*-
"""决断后校验帧(仅登记, 不参与成交) + 报警件追加"""
import json, urllib.request, datetime, os

D = r"D:\股票数据\市场数据\盘中\20261021"
url = "https://qt.gtimg.cn/q=sz000601,sz000823,sh000001,sz399006"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "replace")
rows = {}
for seg in raw.strip().split(";"):
    seg = seg.strip()
    if not seg.startswith("v_"):
        continue
    k, _, b = seg.partition("=")
    f = b.strip().strip('"').split("~")
    if len(f) < 40:
        continue
    rows[f[2]] = {"name": f[1], "px": float(f[3]), "pct": float(f[32]), "high": float(f[33]),
                  "low": float(f[34]), "bid1": f[9], "ask1": f[19], "t": f[30]}
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json.dump({"fetched": now, "note": "决断后校验帧, 仅登记漂移, 不参与成交", "rows": rows},
          open(os.path.join(D, "_hb_f_quote_postcheck.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("postcheck", now, json.dumps(rows, ensure_ascii=False))

alarm = {
  "ts": now,
  "session": "hb-f_1445",
  "level": "ALARM",
  "type": "intraday_leg_declared_not_booked_4th_statement",
  "scope": "intraday_chain",
  "detail": ("hb-f(14:45深场B)对账：master/账本.jsonl 今日仍 0 条、状态 date=20261020、执行流水.jsonl 不存在(连续第3个交易日 1019/1020/1021)。"
             f"本场第4次(也是当日最后一次盘中)重声明清仓：000601 6000@6.35(毛 -1980元/-4.94%)、000823 800@23.92(毛 -968元/-4.81%；自0940声明价累计工程损耗 -892元)；"
             "600668 已核销废单(20261020 sell@8.11)。预案 leg=close/take_zt = 0 条 → 尾盘无时点性卖单，本场两笔均为 leg=open 补偿执行；买入 0 笔(今日 002076 gap+8.07%、603278 一字已作废，两票今收 +9.87%/+10.01%，作废成本登记为明日结算项)。"
             "截面：昨涨停池 52 票，末帧 14:47:08 中位 +3.74%(14:15 峰 +5.36%→尾盘 -1.62pp)、36涨/16跌、封板16只、未回封炸板3只(率15.8%)；指数上证 3704.82(-0.82%)、创业板 2684.67(-1.99%) 双双击穿日内低点收盘 = 池内惯性溢价与指数退潮背离。量化判读：情绪惯性尾段+指数退潮，非修复延续亦非崩塌；无主线(16只封板散在13行业、最大宽度2只)；空间龙003029吉大正元5板未成(-2.97%断板大阴)。"
             "数据源：realtime_ticks 316帧 09:31:09~14:47:08(帧龄0.4min) + qt.gtimg.cn 帧 20261021144715。"),
  "ref": "临盘决断_20261021_1445.json"
}
p = os.path.join(D, "报警_20261021.jsonl")
before = sum(1 for l in open(p, encoding="utf-8") if l.strip())
with open(p, "a", encoding="utf-8") as f:
    f.write(json.dumps(alarm, ensure_ascii=False) + "\n")
after = sum(1 for l in open(p, encoding="utf-8") if l.strip())
print("alarm appended:", before, "->", after)
