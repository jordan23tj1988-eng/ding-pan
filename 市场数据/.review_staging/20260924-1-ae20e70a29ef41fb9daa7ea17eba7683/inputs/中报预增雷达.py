# -*- coding: utf-8 -*-
"""
中报预增雷达.py —— ④产业逻辑·第五段"中报预增·概念叠加雷达"数据引擎(A档确定性)
================================================================================
目标: 从全市场中报业绩预告(预增/扭亏)中, 筛出【还没发酵 + 叠加当前活跃题材】的候选,
供11号产业逻辑agent做纵深与荐票(类型=未启动挖掘/埋伏观察)。范例: 三维通信/高德红外
= 中报预增×概念叠加已发酵的对照组, 本雷达找的是它们的"昨天"。

口径(2026-07-12 用户拍板):
- 预增池 = 东财业绩预告(datacenter, stock_yjyg_em) 报告期=当年中报(0630),
  预测指标含"净利润", 预告类型∈{预增,扭亏}, 公告日期≤d (零后视镜)。
- 剔ST/退/N/C(统计口径铁律)。北交所(4/8/9开头)行情缺失标null入数据缺失, 不编。
- 未发酵 = 近20交易日涨幅<15% 且 近5交易日无涨停(zt_pool本地csv口径)。
- 概念叠加 = 命中当前活跃题材线, 证据三源:
  ①产业链模板.json 结构性卡位  ②东财F10所属概念板块  ③业绩变动原因文本关键词。
  活跃线 = 近3个交易日 题材归位_{d}.json 大方向计数≥2 (剔散票/中报预增自身) ∪ 链条纵深库焦点。
- 行情 = _学习/_bars_cache 优先(不复权), 不新鲜则sina补拉并回写缓存。
输出: _学习/中报预增雷达_{d}.json
用法: python3 中报预增雷达.py YYYYMMDD
"""
import sys, os, json, glob, csv, time, datetime

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据")
    BASE = g[0] if g else BASE
LEARN = os.path.join(BASE, "_学习")
CACHE = os.path.join(LEARN, "_bars_cache")

# 活跃线关键词同义词典(可增补): 线名 -> 匹配词(概念板块名/原因文本)
SYN = {
    "商业航天":   ["商业航天","卫星","航天","火箭","北斗","空天","低轨"],
    "AI算力":     ["算力","AI","人工智能","智算","数据中心","IDC","CPO","光模块","液冷","服务器","东数西算","GPU","AI眼镜","AIGC","智算","PCB","覆铜板","印制电路"],
    "半导体":     ["半导体","芯片","集成电路","存储","先进封装","光刻","元器件"],
    "机器人":     ["机器人","减速器","伺服","丝杠","人形"],
    "医药":       ["创新药","医药","CXO","生物医药","疫苗","医疗"],
    "军工":       ["军工","国防","红外","导弹","无人机","低空"],
    "存储":       ["存储","HBM","内存","闪存"],
    "电网":       ["特高压","电网","输变电","智能电网","虚拟电厂"],
    "农业":       ["养殖","农业","生猪","肉鸡","鸡苗","禽","种业"],
    "传媒":       ["传媒","影视","游戏","短剧","IP"],
    "固态电池":   ["固态电池","锂电","电解质","电池","电解液","六氟","LiFSI","正极","负极"],
    "可控核聚变": ["核聚变","核电","核能"],
    "稀土":       ["稀土","永磁","小金属"],
    "海洋经济":   ["海洋经济","深海","海工"],
}

# 题材类归一(2026-07-12用户拍板:分类浏览"每个题材下面的未发酵个股")
CLASS_MAP = [
    ("AI算力类",      ["AI算力"]),
    ("存储/半导体类", ["存储/半导体","半导体"]),
    ("机器人/人形类", ["机器人","人形机器人"]),
    ("商业航天类",    ["商业航天"]),
    ("军工/低空类",   ["军工"]),
    ("锂电/固态电池类",["汽车","固态电池","锂电"]),
    ("医药类",        ["医药"]),
    ("电网/特高压类", ["电网","特高压"]),
    ("传媒类",        ["传媒"]),
    ("农业类",        ["农业","养殖"]),
    ("旅游/免税类",   ["旅游","免税"]),
]
def class_of_line(line):
    for cls, keys in CLASS_MAP:
        if any(k in line for k in keys):
            return cls
    return line + "类"

def kw_for_line(line):
    """活跃线名 -> 关键词集合: 命中SYN取并集, 否则按分隔符拆词。"""
    kws = set()
    for key, words in SYN.items():
        if key in line:
            kws.update(words)
    for tok in line.replace("/", "|").replace("·", "|").replace("+", "|").split("|"):
        tok = tok.strip()
        if len(tok) >= 2:
            kws.add(tok)
    return kws

def bad_name(name):
    n = str(name).replace(" ", "")
    if "ST" in n.upper() or "退" in n:
        return True
    if n[:1] in ("N","C") and len(n) > 1:
        return True
    return False

def trade_folders(d):
    ds = sorted([x for x in os.listdir(BASE) if x.isdigit() and len(x)==8 and os.path.isdir(os.path.join(BASE,x))])
    return [x for x in ds if x <= d]

def zt_codes_lastN(d, n=5):
    codes = set()
    for day in trade_folders(d)[-n:]:
        p = os.path.join(BASE, day, "zt_pool.csv")
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                c = str(row.get("代码","")).zfill(6)
                if c:
                    codes.add(c)
    return codes

def load_bars(code, d, sess):
    """返回 close 列表(升序, 截至≤d)。缓存优先, 不新鲜则sina补拉回写。"""
    dd = d[:4]+"-"+d[4:6]+"-"+d[6:]
    p = os.path.join(CACHE, code+".csv")
    rows = []
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                rows = [r for r in csv.DictReader(f) if r.get("date") and r.get("close")]
        except Exception:
            rows = []
    if rows and rows[-1]["date"] >= dd:
        return [(r["date"], float(r["close"])) for r in rows if r["date"] <= dd]
    # 不新鲜 -> sina
    pre = "sh" if code.startswith("6") else ("sz" if code[0] in "03" else None)
    if pre is None:
        return None  # 北交所等, sina不覆盖
    try:
        import akshare as ak
        df = ak.stock_zh_a_daily(symbol=pre+code, start_date=(datetime.datetime.strptime(d,"%Y%m%d")-datetime.timedelta(days=430)).strftime("%Y%m%d"), end_date=d)
        if df is None or df.empty:
            return None
        df = df.reset_index()
        out = []
        for _, r in df.iterrows():
            dt = str(r["date"])[:10]
            out.append((dt, float(r["close"])))
        # 回写缓存(整写: date,open,high,low,close,volume,turnover,circ_mv亿)
        try:
            with open(p, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["date","open","high","low","close","volume","turnover","circ_mv亿"])
                for _, r in df.iterrows():
                    w.writerow([str(r["date"])[:10], r.get("open",""), r.get("high",""), r.get("low",""), r["close"], r.get("volume",""), "", ""])
        except Exception:
            pass
        time.sleep(0.12)
        return [(x,y) for x,y in out if x <= dd]
    except Exception:
        return None

def pos_of(bars):
    """长周期位置(年内): r250=现价/近250样本首收-1, 距250日高/低。样本<40返回None。"""
    if not bars or len(bars) < 40:
        return None
    cur = bars[-1][1]
    w = [x[1] for x in bars[-250:]]
    return {"r250": round((cur/w[0]-1)*100,1), "距250日高%": round((cur/max(w)-1)*100,1), "距250日低%": round((cur/min(w)-1)*100,1)}

def r20_of(bars):
    if not bars or len(bars) < 21:
        return None
    c_now = bars[-1][1]; c_20 = bars[-21][1]
    if c_20 <= 0:
        return None
    return round((c_now/c_20 - 1.0)*100, 2)

def f10_concepts(code, sess):
    mk = "SH" if code.startswith("6") else ("SZ" if code[0] in "03" else "BJ")
    try:
        r = sess.get("https://emweb.securities.eastmoney.com/PC_HSF10/CoreConception/PageAjax",
                     params={"code": mk+code}, timeout=10)
        j = r.json()
        boards = [x.get("BOARD_NAME","") for x in (j.get("ssbk") or [])]
        hxtc = " ".join([str(x.get("MAINPOINT_CONTENT",""))[:120] for x in (j.get("hxtc") or [])[:3]])
        time.sleep(0.15)
        return boards, hxtc
    except Exception:
        return None, None

def active_lines(d):
    """近3个归位日的大方向计数≥2 ∪ 链条纵深库板块。返回 {线名:计数}"""
    lines = {}
    days = sorted([x[5:13] for x in os.listdir(LEARN) if x.startswith("题材归位_") and x.endswith(".json")])
    days = [x for x in days if x <= d][-3:]
    for day in days:
        try:
            j = json.load(open(os.path.join(LEARN, "题材归位_"+day+".json"), encoding="utf-8"))
            for v in (j.get("映射") or {}).values():
                if not isinstance(v, dict):
                    continue
                ln = str(v.get("大方向","")).strip()
                if not ln or "散票" in ln or "个股逻辑" in ln or "中报预增" in ln:
                    continue
                lines[ln] = lines.get(ln, 0) + 1
        except Exception:
            pass
    lines = {k: v for k, v in lines.items() if v >= 2}
    try:
        chains = json.load(open(os.path.join(LEARN, "链条纵深库.json"), encoding="utf-8"))
        for bk in chains:
            if bk not in ("说明",) and bk not in lines:
                lines[bk] = lines.get(bk, 0) or 1
    except Exception:
        pass
    return lines

def template_map():
    """产业链模板.json -> {code:(板块,环节)}"""
    m = {}
    try:
        j = json.load(open(os.path.join(BASE, "产业链模板.json"), encoding="utf-8"))
        for bk, v in j.items():
            if bk == "说明" or not isinstance(v, dict):
                continue
            envs = v.get("环节") if isinstance(v.get("环节"), dict) else v
            if not isinstance(envs, dict):
                continue
            for env, ev in envs.items():
                stocks = ev.get("公司") if isinstance(ev, dict) else ev
                if isinstance(stocks, dict):
                    it = stocks.items()
                elif isinstance(stocks, list):
                    it = [(s.get("代码",""), s.get("名称","")) if isinstance(s, dict) else (str(s),"") for s in stocks]
                else:
                    continue
                for c, _n in it:
                    c = str(c).zfill(6)
                    if c.isdigit():
                        m.setdefault(c, (bk, env))
    except Exception:
        pass
    return m

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
    year = d[:4]
    period = year + "0630"
    dd = d[:4]+"-"+d[4:6]+"-"+d[6:]
    import requests
    sess = requests.Session(); sess.trust_env = False

    import akshare as ak
    df = ak.stock_yjyg_em(date=period)
    df = df[df["预测指标"].astype(str).str.contains("净利润")]
    df = df[~df["预测指标"].astype(str).str.contains("扣除")]
    df = df[df["预告类型"].isin(["预增","扭亏"])]
    df = df[df["公告日期"].astype(str).str[:10] <= dd]
    df = df.drop_duplicates(subset=["股票代码"], keep="first")
    total_raw = len(df)

    zt5 = zt_codes_lastN(d, 5)
    lines = active_lines(d)
    line_kws = {ln: kw_for_line(ln) for ln in lines}
    tpl = template_map()

    # 断点续跑: 沙箱bash调用有时限, 进度存/tmp, 重跑自动跳过已算
    CKPT = "/tmp/radar_ckpt_" + d + ".json"
    ck = {"bars": {}, "f10": {}}
    if os.path.exists(CKPT):
        try:
            ck = json.load(open(CKPT))
        except Exception:
            pass
    def save_ck():
        json.dump(ck, open(CKPT, "w"), ensure_ascii=False)

    cands, fermented, missing, pure, priced = [], [], [], [], []
    n_st = 0
    n_new = 0
    for _, r in df.iterrows():
        code = str(r["股票代码"]).zfill(6)
        name = str(r["股票简称"]).strip()
        if bad_name(name):
            n_st += 1
            continue
        rec = {"代码": code, "名称": name, "预告类型": str(r["预告类型"]),
               "变动幅度%": (round(float(r["业绩变动幅度"]),1) if str(r["业绩变动幅度"]) not in ("nan","None","") else None),
               "公告日期": str(r["公告日期"])[:10],
               "原因": str(r["业绩变动原因"])[:400]}
        ent = ck["bars"].get(code)
        if not isinstance(ent, dict):
            bars = load_bars(code, d, sess)
            r20 = r20_of(bars) if bars and len(bars) >= 21 else None
            ent = {"r20": r20, "pos": pos_of(bars)}
            ck["bars"][code] = ent
            n_new += 1
            if n_new % 15 == 0:
                save_ck(); print("bars进度", len(ck["bars"]), flush=True)
        r20 = ent["r20"]
        if r20 is None:
            rec["近20日涨幅%"] = None
            missing.append(rec)
            continue
        ztn = 1 if code in zt5 else 0
        rec["近20日涨幅%"] = r20
        rec["近5日涨停"] = ztn
        if ent.get("pos"):
            rec.update(ent["pos"])
        # ★预期已兑现(2026-07-12用户拍板): 年内净涨幅≥100%(已翻倍)=预增在市场预期内,
        # 不算"未发酵"(江波龙式:预增+68299%但r250=+590%,业绩早在价内)。单列不入候选。
        if (rec.get("r250") or 0) >= 100.0:
            priced.append(rec)
        elif r20 < 15.0 and ztn == 0:
            cands.append(rec)
        else:
            fermented.append(rec)

    # 概念叠加: 只对未发酵候选 + 已发酵top12 拉F10
    fermented.sort(key=lambda x: -(x.get("近20日涨幅%") or 0))
    save_ck()
    def stack_of(rec):
        c = rec["代码"]
        if c in ck["f10"]:
            boards, hxtc = ck["f10"][c]
        else:
            boards, hxtc = f10_concepts(c, sess)
            ck["f10"][c] = [boards, hxtc]
            if len(ck["f10"]) % 15 == 0:
                save_ck(); print("f10进度", len(ck["f10"]), flush=True)
        hits = []
        TXT_BAN = {"AI"}  # 泛词禁入文本匹配(圆通速递式蹭字母教训,2026-07-12)
        for ln, kws in line_kws.items():
            ev = []; w = 0
            t = tpl.get(rec["代码"])
            if t and (t[0] in ln or ln in t[0]):
                ev.append("模板卡位:"+t[0]+"·"+t[1]); w += 3
            if boards:
                bh = [b for b in boards if any(k in b for k in kws)]
                if bh:
                    ev.append("概念:"+",".join(bh[:3])); w += 2
            txt = rec["原因"] + " " + (hxtc or "")
            th = [k for k in kws if len(k) >= 2 and k not in TXT_BAN and k in txt]
            if th:
                ev.append("文本:"+",".join(th[:3])); w += min(2, len(th))
            # ★叠加线成立门槛: 权重≥2(须有概念板块/模板级证据,或≥2个文本关键词)
            if ev and w >= 2:
                hits.append({"线": ln, "依据": ev, "权重": w})
        rec["概念板块"] = ([b for b in (boards or []) if "板块" not in b and "融资" not in b and "通" != b[-1:]][:8]) if boards is not None else None
        rec["叠加"] = hits
        rec["叠加数"] = len(hits)
        return rec

    # ★成色自动审核(2026-07-12用户拍板,标准=当日44只人工归因的规则化):
    # A=概念×业绩共振: 叠加线关键词出现在【业绩变动原因文本】(文本:证据)——业绩动因即题材业务;
    # C=非经常性/低质: 原因命中C词表(重整/处置/出售/保险赔/补助/减值转回/一次性/低基数/公允价值/退税);
    # B=其余(主业增长真实但与叠加题材无关,F10概念tag=蹭)。
    # C词命中但同时有A证据 → A(标"含非经常增厚,幅度打折")。初判可被人工override升降档。
    C_WORDS = ["重整","资产处置","处置收益","处置损失","出售","转让","保险赔","赔偿款","补助",
               "汇兑","减值损失同比","减值转回","冲回","低基数","基数较低","一次性","公允价值变动",
               "税费退还","退税","递延确认"]
    TXT_BAN2 = {"AI"}
    def audit_of(rec):
        reason = rec.get("原因") or ""
        a_kw = []
        for h in rec.get("叠加", []):
            for kws_ln in [line_kws.get(h["线"], set())]:
                a_kw += [k for k in kws_ln if len(k) >= 2 and k not in TXT_BAN2 and k in reason]
        a_kw = sorted(set(a_kw))
        c_hit = sorted({w for w in C_WORDS if w in reason})
        if a_kw and c_hit:
            rec["成色初判"] = "A"; rec["初判依据"] = "动因词:" + ",".join(a_kw[:4]) + ";含非经常增厚(" + ",".join(c_hit[:3]) + "),幅度打折"
        elif a_kw:
            rec["成色初判"] = "A"; rec["初判依据"] = "动因词:" + ",".join(a_kw[:4]) + "(题材业务=业绩来源)"
        elif c_hit:
            rec["成色初判"] = "C"; rec["初判依据"] = "非经常信号:" + ",".join(c_hit[:4])
        else:
            rec["成色初判"] = "B"; rec["初判依据"] = "原因文本无题材动因词,概念tag疑蹭"
        return rec

    def merge_verdict(stacked_list):
        """人工复核override合并: _学习/中报预增成色判定_{d}.json 的档优先于初判"""
        ov = {}
        vp = os.path.join(LEARN, "中报预增成色判定_" + d + ".json")
        if os.path.exists(vp):
            try:
                ov = json.load(open(vp, encoding="utf-8")).get("判定", {})
            except Exception:
                ov = {}
        for x in stacked_list:
            o = ov.get(x["代码"])
            if o:
                x["成色"] = o.get("档", x["成色初判"]); x["成色依据"] = o.get("依据", x["初判依据"]); x["成色来源"] = "人工复核"
                if o.get("改归类"):
                    x["主类"] = o["改归类"]
            else:
                x["成色"] = x["成色初判"]; x["成色依据"] = x["初判依据"]; x["成色来源"] = "自动初判"
        return stacked_list

    def rank_score(x):
        """A池重要度分(排序参考,页面顺序agent可再调): 动因共振+卡位+位置+幅度"""
        s = 0
        if "动因词" in (x.get("成色依据") or ""): s += 2
        if any(e.startswith("模板卡位") for h in x.get("叠加", []) for e in h["依据"]): s += 1
        s += min(x.get("叠加数", 0), 3)
        r250 = x.get("r250")
        if r250 is not None:
            if r250 < 0: s += 2
            elif r250 < 50: s += 1
        if (x.get("距250日高%") or 0) <= -30: s += 1
        if (x.get("变动幅度%") or 0) >= 200: s += 1
        if "幅度打折" in (x.get("成色依据") or ""): s -= 1
        return s

    # 刚点火组: 近5日有涨停但20日涨幅尚未透支(<15%)——发酵初段,单列(如三维通信07-10首板日)
    ignited = [x for x in fermented if x.get("近5日涨停")==1 and (x.get("近20日涨幅%") or 0) < 15.0]
    ignited.sort(key=lambda x: -(x.get("变动幅度%") or 0))
    priced.sort(key=lambda x: -(x.get("r250") or 0))
    for rec in cands:
        stack_of(rec)
    for rec in priced[:12]:
        stack_of(rec)
    for rec in fermented[:12]:
        stack_of(rec)
    for rec in ignited[:15]:
        if "叠加" not in rec:
            stack_of(rec)
    save_ck()

    stacked = [x for x in cands if x["叠加数"] > 0]
    # 按题材类归组(主类唯一防重复;副类记chips)
    def group_by_class(items):
        for x in items:
            score = {}
            for h in x.get("叠加", []):
                cls = class_of_line(h["线"])
                score[cls] = score.get(cls, 0) + h.get("权重", 1)
            if not score:
                x["主类"] = None; x["副类"] = []
                continue
            best = sorted(score.items(), key=lambda t: -t[1])
            x["主类"] = best[0][0]
            x["主类权重"] = best[0][1]   # ≥5=模板/多源强叠加, 3-4=中, 2=仅单一概念tag(弱叠加,防蹭)
            x["副类"] = [c for c, _ in best[1:4]]
        groups = {}
        for x in items:
            if x.get("主类"):
                groups.setdefault(x["主类"], []).append(x)
        for g in groups.values():
            g.sort(key=lambda t: (-(t.get("主类权重") or 0), -(t.get("变动幅度%") or 0)))
        return dict(sorted(groups.items(), key=lambda kv: -len(kv[1])))
    pure = [x for x in cands if x["叠加数"] == 0]
    stacked.sort(key=lambda x: (-x["叠加数"], -(x["变动幅度%"] or 0)))
    pure.sort(key=lambda x: -(x["变动幅度%"] or 0))

    by_class = group_by_class(stacked)
    for x in stacked:
        audit_of(x)
    merge_verdict(stacked)
    a_pool = [x for x in stacked if x.get("成色") == "A"]
    for x in a_pool:
        x["重要度分"] = rank_score(x)
    a_pool.sort(key=lambda x: (-x["重要度分"], -(x.get("变动幅度%") or 0)))
    n_a = len(a_pool); n_b = sum(1 for x in stacked if x.get("成色")=="B"); n_c = sum(1 for x in stacked if x.get("成色")=="C")
    out = {
        "日期": d, "报告期": period,
        "口径": "预增/扭亏(归母净利润,公告≤d);剔ST退N/C;★预期已兑现=r250年内净涨≥100%剔出(2026-07-12);未发酵=近20日<15%且近5日无涨停;行情=bars_cache/sina不复权(补拉430天保长历史)",
        "统计": {"预告池(净利润·预增扭亏)": total_raw, "剔ST退N/C": n_st,
                 "未发酵候选": len(cands), "其中概念叠加": len(stacked),
                 "已发酵(对照)": len(fermented), "其中刚点火": len(ignited), "预期已兑现(r250≥100%)": len(priced), "行情缺失": len(missing),
                 "成色A共振": n_a, "成色B概念蹭": n_b, "成色C低质": n_c},
        "活跃线": lines,
        "A共振池(重要度排序)": [{"代码":x["代码"],"名称":x["名称"],"预告类型":x["预告类型"],"变动幅度%":x["变动幅度%"],
            "近20日涨幅%":x["近20日涨幅%"],"r250":x.get("r250"),"距250日高%":x.get("距250日高%"),
            "主类":x.get("主类"),"重要度分":x["重要度分"],"成色依据":x["成色依据"],"成色来源":x["成色来源"],
            "叠加线":[h["线"] for h in x.get("叠加",[])][:4],"原因":x["原因"][:120]} for x in a_pool],
        "按题材归类": {cls: [{"代码":x["代码"],"名称":x["名称"],"预告类型":x["预告类型"],"变动幅度%":x["变动幅度%"],"近20日涨幅%":x["近20日涨幅%"],"r250":x.get("r250"),"距250日高%":x.get("距250日高%"),"权重":x.get("主类权重"),"副类":x["副类"],"成色":x.get("成色"),"成色来源":x.get("成色来源"),"原因":x["原因"][:80]} for x in v] for cls, v in by_class.items()},
        "概念叠加候选": stacked,
        "纯预增未叠加": pure[:40],
        "预期已兑现(年内已翻倍,不入候选)": priced[:20],
        "刚点火(有涨停未透支)": ignited[:15],
        "已发酵对照Top12": fermented[:12],
        "行情缺失": [{"代码": x["代码"], "名称": x["名称"]} for x in missing],
    }
    fp = os.path.join(LEARN, "中报预增雷达_"+d+".json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("OK", fp)
    print(json.dumps(out["统计"], ensure_ascii=False))
    print("活跃线:", ",".join(lines.keys()))
    print("成色: A共振%d B蹭%d C低质%d" % (n_a, n_b, n_c))
    for x in a_pool:
        print(" A", x["重要度分"], x["代码"], x["名称"], x.get("主类"), x["成色来源"], "|", x["成色依据"][:60])
    for cls, v in by_class.items():
        print(f"[{cls}] {len(v)}只:", " ".join(x["名称"] for x in v))

if __name__ == "__main__":
    main()
