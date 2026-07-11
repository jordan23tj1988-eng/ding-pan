# -*- coding: utf-8 -*-
"""
米开朗基瑞体系·A档可回测规则 —— 指数量能择时 + 个股过滤
================================================================
只实现"能用日线历史因果回测"的 A 档规则(见 米开朗基瑞_量化规则清单.md):
  A1 指数量能台阶      —— 主升/滞涨择时
  A2 放量下杀/缩量回拉  —— 危险背离降水位
  A3 回撤支撑位(0.618) —— 低吸位
  A7 个股位置过滤      —— 高位不追

★ 严格零后视镜:每个信号在第 t 日只用 <= t 日的数据。
★ 依赖 data_link.py(需挂载 BaiduNetdiskDownload + new_tdx 数据盘才能取数)。
★ 不实现 C 档(量化第一式/竞价/盘口)——那些需实时竞价+逐笔大单,历史数据跑不了,
  只能实盘按 checklist 手动执行(见清单 C 档)。

用法:
  python 米开朗基瑞_A档筛选.py            # 跑指数择时(默认上证)
  python 米开朗基瑞_A档筛选.py 600519     # 附带个股位置过滤
"""
import sys, os
import pandas as pd

# ---- 接入数据链路 ----
DL_DIR = r"D:\股票数据\数据链路"
for cand in (DL_DIR, "/tmp/dl", os.path.join(os.path.dirname(__file__), "..", "数据链路")):
    if os.path.isdir(cand):
        sys.path.insert(0, cand); break
import data_link as dl  # noqa: E402

# 参数(可按盘感调) --------------------------------------------------------------
MARKET_STEP_YI   = 35000     # A1 主升量能门槛:两市成交额(亿) >= 3.5万亿
STEP_UP_YI       = 3000      # A1 台阶放量增量(亿):额 >= MA5 + 3000亿
RETRACE_RATIO    = 0.618     # A3 回撤支撑比例(备选0.713)
SWING_WIN        = 20        # A3 摆动高低点回看窗口
POS_HIGH_PCT     = 0.15      # A7 距60日高回撤<15%视为高位,不追


def _to_yi(amount_series):
    """把 amount(元)换算成亿元。若数据本身已是亿或手,按需在此调整。"""
    return amount_series / 1e8


def index_timing(index_code="sh000001"):
    """A1/A2/A3 指数量能择时。返回带信号列的 DataFrame。
    注意:data_link 的 amount 是该指数(单市场)成交额;若要"两市合计"需另取深证相加。
    这里用单市场额演示口径,阈值 MARKET_STEP_YI 需按实际口径校准。
    """
    df = dl.get(index_code, "1D", adjust="raw").copy()
    df["amt_yi"] = _to_yi(df["amount"])
    df["amt_ma5"] = df["amt_yi"].rolling(5).mean()

    # A1 量能台阶:额>=门槛 且 >=MA5+增量 → 主升;额跌破门槛 → 滞涨
    df["A1_main_up"] = (df["amt_yi"] >= MARKET_STEP_YI) & (df["amt_yi"] >= df["amt_ma5"] + STEP_UP_YI)
    df["A1_stall"]   = df["amt_yi"] < MARKET_STEP_YI

    # A2 危险背离:下跌日额 > 前一上涨日额,连续>=2次 → 放量杀缩量拉
    df["ret"] = df["close"].pct_change()
    down_vol_gt = []
    for i in range(len(df)):
        if i < 2:
            down_vol_gt.append(False); continue
        # 当日下跌且成交额高于最近一个上涨日的额
        if df["ret"].iat[i] < 0:
            prev_up = df.iloc[max(0, i-5):i]
            prev_up = prev_up[prev_up["ret"] > 0]
            cond = (not prev_up.empty) and (df["amt_yi"].iat[i] > prev_up["amt_yi"].iloc[-1])
            down_vol_gt.append(bool(cond))
        else:
            down_vol_gt.append(False)
    df["_dvg"] = down_vol_gt
    df["A2_danger"] = df["_dvg"] & df["_dvg"].shift(1).fillna(False)  # 连续2日

    # A3 回撤支撑位:用滚动窗口的前高/前低算 0.618 回撤,当日触及且当日止跌放量 → 低吸位
    df["swing_hi"] = df["high"].rolling(SWING_WIN).max()
    df["swing_lo"] = df["low"].rolling(SWING_WIN).min()
    df["support_618"] = df["swing_hi"] - (df["swing_hi"] - df["swing_lo"]) * RETRACE_RATIO
    touched = df["low"] <= df["support_618"]
    stop_fall = df["close"] > df["close"].shift(1)          # 当日收阳(止跌)
    vol_up = df["amt_yi"] > df["amt_yi"].shift(1)           # 放量
    df["A3_dip_buy"] = touched & stop_fall & vol_up

    return df[["time", "close", "amt_yi", "amt_ma5",
               "A1_main_up", "A1_stall", "A2_danger", "support_618", "A3_dip_buy"]]


def stock_position_filter(code):
    """A7 个股位置过滤:距60日高点回撤 < POS_HIGH_PCT → 高位,不追。"""
    df = dl.get(code, "1D", adjust="qfq").copy()   # 位置用前复权
    df["hi60"] = df["high"].rolling(60).max()
    df["draw_from_hi"] = (df["hi60"] - df["close"]) / df["hi60"]
    df["A7_too_high"] = df["draw_from_hi"] < POS_HIGH_PCT
    return df[["time", "close", "hi60", "draw_from_hi", "A7_too_high"]]


# --- A4/A5/A9 需全A循环统计,留接口 ---------------------------------------------
def market_breadth_TODO():
    """A4情绪温度/A5连板天花板/A9题材梯队:需遍历全A日线算涨停/连板/板块统计。
    工程量大,且'涨停'判定要用 raw 价+涨跌幅规则(注意ST/科创/北交所不同幅度、
    2026-07-06起ST恢复±10%)。此处留空,后续接全A清单实现。"""
    raise NotImplementedError("需全A数据循环,见清单A4/A5/A9")


if __name__ == "__main__":
    print("=" * 60)
    print("A档·指数量能择时(最近15日)")
    print("=" * 60)
    try:
        idx = index_timing("sh000001")
        with pd.option_context("display.width", 160, "display.max_columns", 20):
            print(idx.tail(15).to_string(index=False))
        last = idx.iloc[-1]
        print("\n【今日态度】",
              "主升攻" if last["A1_main_up"] else ("滞涨守" if last["A1_stall"] else "中性"),
              "| 危险背离!" if last["A2_danger"] else "",
              "| 到618低吸位!" if last["A3_dip_buy"] else "")
    except Exception as e:
        print("指数取数失败(多半是数据盘未挂载):", e)
        print("→ 挂载 BaiduNetdiskDownload + new_tdx 后重跑;或先 cp 数据链路到 /tmp")

    if len(sys.argv) > 1:
        code = sys.argv[1]
        print("\n" + "=" * 60); print(f"A7·个股位置过滤 {code}(最近10日)"); print("=" * 60)
        try:
            pf = stock_position_filter(code)
            print(pf.tail(10).to_string(index=False))
        except Exception as e:
            print("个股取数失败:", e)
