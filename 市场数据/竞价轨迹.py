# -*- coding: utf-8 -*-
"""
竞价轨迹.py —— 9:15-9:25 逐分钟抓「集合竞价演变轨迹」(米氏第一式真原料)
=======================================================================
为什么需要它: 现有 竞价快照.py 只在 9:26 抓一帧(最终价), 丢了 9:15-9:25 的
演变过程。本脚本在集合竞价时段内每 60s 轮询一次, 存时间序列, 才能回答
"什么竞价变化预示 T日涨停 / 隔日溢价"。

抓取字段(每只票每帧):
  时刻, 代码, 名称, 竞价价(=最新), 昨收, 高开幅度%, 竞价成交额(万),
  竞价成交量(手), 匹配量, 未匹配量, 量比。
★ 撤单效应: 9:20 前可撤单, 9:20 后不可撤。对比 9:20 前后涨幅位移 =
  真强(9:20后上移) vs 诱多(9:20前拉、后回落)。
★ 免费源无历史逐笔, 此库需日积月累(数周起)才有统计意义。量比非免费竞价
  字段, 用「竞价额换手率(额/流通市值) + 匹配量/未匹配量比(买卖盘博弈)」替代。

用法: python 竞价轨迹.py   （建议自动化 交易日 9:15 触发, 自带循环到 9:25）
依赖: akshare(用户真机环境可用; 沙箱网络墙仅能有限连通, 带重试兜底)
"""
import sys, os, json, glob, time, datetime
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q"); import akshare as ak
import pandas as pd

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

def prev_dir(today):
    for dd in range(1, 8):
        d = (today - datetime.timedelta(days=dd)).strftime("%Y%m%d")
        if os.path.isfile(os.path.join(BASE, d, "zt_pool.csv")):
            return d
    return None

def build_watchlist(pd_dir):
    wl = {}
    try:
        zt = pd.read_csv(os.path.join(BASE, pd_dir, "zt_pool.csv"), dtype={"代码": str})
        zt["代码"] = zt["代码"].str.zfill(6)
        for _, r in zt[zt["连板数"] >= 1].iterrows():
            wl[r["代码"]] = r["名称"]
    except Exception:
        pass
    ana = os.path.join(BASE, pd_dir, "analysis.json")
    if os.path.isfile(ana):
        try:
            a = json.load(open(ana, encoding="utf-8"))
            for c in a.get("核心标的", []):
                wl[str(c["代码"]).zfill(6)] = c["名称"]
        except Exception:
            pass
    return wl

def bid_of(code):
    """返回 (竞价价,昨收,竞价额,竞价量,匹配量,未匹配量,量比) 或全None。带重试。"""
    for _ in range(3):
        try:
            df = ak.stock_bid_ask_em(symbol=code)
            m = dict(zip(df["item"], df["value"])) if "item" in df.columns else {}
            price = float(m.get("最新", m.get("今开", 0) or 0))
            prevc = float(m.get("昨收", 0) or 0)
            amt = float(m.get("金额", 0) or 0)
            vol = float(m.get("成交量", 0) or 0)
            matched = float(m.get("买一", 0) or 0)   # 近似: 买一挂单量
            unmatched = float(m.get("卖一", 0) or 0)  # 近似: 卖一挂单量
            ratio = float(m.get("量比", 0) or 0)
            return price, prevc, amt, vol, matched, unmatched, ratio
        except Exception:
            time.sleep(1)
    return (None,)*7

def main():
    now = datetime.datetime.now()
    # 仅交易日 9:15-9:26 区间有效; 非交易时段直接退出(留痕)
    if now.hour < 9 or (now.hour == 9 and now.minute < 15) or (now.hour == 9 and now.minute > 26) or now.hour > 9:
        # 允许 9:15-9:26
        if not (now.hour == 9 and 15 <= now.minute <= 26):
            print("非集合竞价时段(需在 9:15-9:26 运行), 退出"); return
    today = now.date()
    d = today.strftime("%Y%m%d")
    pdir = prev_dir(today)
    if not pdir:
        print("无昨日数据, 无法建清单"); return
    wl = build_watchlist(pdir)
    print(f"盯盘清单 {len(wl)} 只 (来自 {pdir}), 开始抓 9:15-9:25 轨迹")

    outdir = os.path.join(BASE, d); os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "竞价轨迹.csv")
    rows = []
    # 从当前分钟抓到 9:25:30
    end = now.replace(hour=9, minute=25, second=30, microsecond=0)
    t = now
    while t <= end:
        ts = t.strftime("%H:%M:%S")
        for code, name in wl.items():
            price, prevc, amt, vol, matched, unmatched, ratio = bid_of(code)
            if price:
                hi = round((price/prevc - 1)*100, 2) if prevc else None
                rows.append(dict(时刻=ts, 代码=code, 名称=name,
                                 竞价价=price, 昨收=prevc, 高开幅度=hi,
                                 竞价成交额万=round(amt/1e4, 1), 竞价成交量手=vol,
                                 匹配量=matched, 未匹配量=unmatched, 量比=ratio))
        # 下一分钟
        t = t + datetime.timedelta(minutes=1)
        if t <= end:
            time.sleep(max(0, (t - datetime.datetime.now()).total_seconds()))
    if not rows:
        print("竞价接口全失败(网络), 本日轨迹未存"); return
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"完成 → {out}  ({len(rows)} 帧 / {len(wl)} 只)")

if __name__ == "__main__":
    main()
