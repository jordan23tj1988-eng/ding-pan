# -*- coding: utf-8 -*-
r"""测试iFind接口3.py — 第三轮批量探测: 设计稿v2.0第8.5节全部待探测项(2026-07-18 #034)
双击 测试iFind接口3.bat。产物: _学习/ifind_测试报告3_{d}.json (全部记原始repr,沙箱照实修)。
探测面: ①API能力扫描(hasattr) ②THS_HF高频分钟K(1/5分钟,含北交所) ③RQ五档字段名候选
       ④iwencai问询批量(涨停池切源/龙虎榜/业绩预告/解禁/减持/两融/大宗/竞价额/股东户数)
       ⑤外围指数码(A50/恒指/纳指/汇率) ⑥THS_BD基础数据指标候选(概念/股东户数/解禁)
配额注意: HF探测约几千格(150万池内九牛一毛); iwencai零配额; RQ/BD探测均<千格。
"""
import os, sys, json, datetime, traceback
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
import ifind_source as ifs

today = datetime.date.today()
d = today
while d.weekday() >= 5:  # 周末回退到最近工作日(节假日误差可接受,探测目的只要拿到某交易日数据)
    d -= datetime.timedelta(days=1)
ds = d.strftime("%Y-%m-%d")
dcn = "%d年%d月%d日" % (d.year, d.month, d.day)
dprev = d - datetime.timedelta(days=7)
while dprev.weekday() >= 5:
    dprev -= datetime.timedelta(days=1)
dprevcn = "%d年%d月%d日" % (dprev.year, dprev.month, dprev.day)
rep = {"d": today.strftime("%Y%m%d"), "probe_day": ds, "start": str(datetime.datetime.now()), "probes": {}}

if not ifs.login():
    rep["probes"]["登录"] = {"ok": False}
else:
    THS = ifs._mod()

    def raw(name, fn):
        try:
            v = fn()
            r = {"repr": repr(v)[:1500]}
            df = ifs._to_df(v)
            if df is not None and len(df):
                r["df_cols"] = [str(c) for c in df.columns]; r["df_shape"] = list(df.shape)
                r["df_head"] = json.loads(df.head(6).to_json(orient="records", force_ascii=False))
                # 非空列统计: 字段名候选探测的关键读数
                r["notna"] = {str(c): int(df[c].notna().sum()) for c in df.columns}
        except Exception as e:
            r = {"exc": "%s\n%s" % (e, traceback.format_exc()[-400:])}
        rep["probes"][name] = r
        ok = "exc" not in r and r.get("df_shape", [0])[0] > 0
        print(("PASS " if ok else "---- ") + name, "->",
              ("EXC " + r["exc"][:100]) if "exc" in r else r["repr"][:110].replace("\n", " "))

    # ===== ① API能力扫描(零调用) =====
    apis = ["THS_HQ", "THS_RQ", "THS_HF", "THS_DP", "THS_BD", "THS_iwencai", "THS_Snapshot",
            "THS_DR", "THS_EDB", "THS_DateQuery", "THS_DateSerial", "THS_toTHSCODE",
            "THS_HighFrequenceSequence", "THS_RealtimeQuotes", "THS_HistoryQuotes", "THS_DataPool",
            "THS_QuotesPushing", "THS_RealtimeQuotesPushing"]
    rep["probes"]["0_API能力扫描"] = {k: bool(getattr(THS, k, None)) for k in apis}
    print("API能力:", json.dumps(rep["probes"]["0_API能力扫描"], ensure_ascii=False))

    # ===== ② THS_HF 高频分钟K(8.5-①: 权限/interval/字段) =====
    t0, t1 = ds + " 09:15:00", ds + " 15:15:00"
    raw("HF_1分钟_默认参数", lambda: THS.THS_HF("300033.SZ", "open;high;low;close;volume", "", t0, t1))
    raw("HF_1分钟_Interval1", lambda: THS.THS_HF("300033.SZ", "close;volume", "Interval:1", t0, t1))
    raw("HF_5分钟_Interval5", lambda: THS.THS_HF("300033.SZ", "close;volume", "Interval:5", t0, t1))
    raw("HF_北交所920305", lambda: THS.THS_HF("920305.BJ", "close;volume", "Interval:5", t0, t1))
    raw("HF_老API_HighFrequenceSequence", lambda: THS.THS_HighFrequenceSequence("300033.SZ", "close;volume", "Interval:1", t0, t1))
    raw("HF_历史一年前", lambda: THS.THS_HF("300033.SZ", "close;volume", "Interval:5",
        (d - datetime.timedelta(days=360)).strftime("%Y-%m-%d") + " 09:30:00",
        (d - datetime.timedelta(days=353)).strftime("%Y-%m-%d") + " 15:00:00"))

    # ===== ③ RQ五档字段名候选(8.5-②: 字段置换用,逐组试看哪组非空) =====
    two = "300033.SZ,600519.SH"
    raw("RQ五档_A组bid1askSize1", lambda: THS.THS_RQ(two, "bid1,ask1,bidSize1,askSize1"))
    raw("RQ五档_B组bidvol1", lambda: THS.THS_RQ(two, "bid1,bidvol1,ask1,askvol1"))
    raw("RQ五档_C组buyPrice1", lambda: THS.THS_RQ(two, "buyPrice1,buyVolume1,sellPrice1,sellVolume1"))
    raw("RQ五档_D组bidSize", lambda: THS.THS_RQ(two, "bid,ask,bidSize,askSize"))
    raw("RQ五档_E组amount量额", lambda: THS.THS_RQ(two, "latest,amount,volume,vol"))

    # ===== ④ iwencai问询批量(零配额;8.5-③) =====
    raw("iwencai_涨停池切源", lambda: THS.THS_iwencai(dcn + "涨停的股票,涨停原因,首次涨停时间,连续涨停天数,涨停封单量,涨停开板次数", "stock"))
    raw("iwencai_炸板池", lambda: THS.THS_iwencai(dcn + "曾涨停后开板未回封的股票", "stock"))
    raw("iwencai_跌停池", lambda: THS.THS_iwencai(dcn + "跌停的股票", "stock"))
    raw("iwencai_龙虎榜", lambda: THS.THS_iwencai(dcn + "龙虎榜,龙虎榜净买入额,龙虎榜买入营业部", "stock"))
    raw("iwencai_龙虎榜简查", lambda: THS.THS_iwencai(dcn + "上龙虎榜的股票", "stock"))
    raw("iwencai_业绩预告", lambda: THS.THS_iwencai("2026年中报业绩预增的股票,预告净利润同比增幅,业绩预告公告日期", "stock"))
    raw("iwencai_解禁30天", lambda: THS.THS_iwencai("未来30天有限售股解禁的股票,解禁日期,解禁市值", "stock"))
    raw("iwencai_减持公告", lambda: THS.THS_iwencai("近30天发布减持计划公告的股票", "stock"))
    raw("iwencai_两融", lambda: THS.THS_iwencai(dcn + "融资余额,融资买入额,融券余额", "stock"))
    raw("iwencai_大宗交易", lambda: THS.THS_iwencai(dcn + "发生大宗交易的股票,大宗交易成交额,大宗交易折溢价率", "stock"))
    raw("iwencai_竞价额当日", lambda: THS.THS_iwencai(dcn + "集合竞价成交额前100的股票,集合竞价成交额", "stock"))
    raw("iwencai_竞价额历史", lambda: THS.THS_iwencai(dprevcn + "集合竞价成交额前100的股票,集合竞价成交额", "stock"))
    raw("iwencai_股东户数", lambda: THS.THS_iwencai("最新股东户数环比下降超过5%的股票,股东户数", "stock"))

    # ===== ⑤ 外围指数码候选(8.5-④: 逐码单独试,防混市场静默丢行) =====
    for code in ("CN00Y.SG", "XIN9.FTX", "HSI.HK", "IXIC.GI", "DJI.GI", "USDCNH.FX", "NDX.GI", "GC00Y.CMX"):
        raw("外围RQ_" + code, lambda c=code: THS.THS_RQ(c, "latest,changeRatio,preClose"))

    # ===== ⑥ THS_BD基础数据指标候选(8.5-⑤) =====
    raw("BD_所属概念A", lambda: THS.THS_BD("300033.SZ", "ths_the_concept_stock", ds))
    raw("BD_所属概念B", lambda: THS.THS_BD("300033.SZ", "ths_concept_name_stock", ds))
    raw("BD_股东户数", lambda: THS.THS_BD("300033.SZ", "ths_holder_num_stock", "2026-06-30"))
    raw("BD_下次解禁日", lambda: THS.THS_BD("300033.SZ", "ths_next_lifting_date_stock", ds))
    raw("BD_流通市值", lambda: THS.THS_BD("300033.SZ,600519.SH", "ths_free_float_mv_stock", ds))

rep["end"] = str(datetime.datetime.now())
outp = os.path.join(BASE, "_学习", "ifind_测试报告3_%s.json" % today.strftime("%Y%m%d"))
with open(outp, "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print("\n报告已写: " + outp)
print("跑完后回沙箱会话说一声,我读报告逐条定案8.5。")
ifs.logout()
