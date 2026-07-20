# -*- coding: utf-8 -*-
"""盘中实时管道.py — 阶段①宿主常驻(2026-07-18 #028, 设计=升级设计稿v1.9 §2.1/2.4)
Windows计划任务 交易日09:14启动,15:06自杀。数据全走iFind单通道(v1.6),配额记账熔断(v1.5)。
产物: 盘中/{d}/ auction_traj.jsonl / auction_frame_*.csv.gz / watch.jsonl / pulse.json /
      warboard.json(每60s重组→自动调 生成作战台.py) / pipeline.log / selftest.json(自测)
用法: python 盘中实时管道.py [--selftest]   (自测=各环节各跑一轮,不等时刻,周末可跑)
"""
import os, sys, json, time, csv, gzip, glob, datetime, subprocess, traceback
os.environ["NO_PROXY"] = os.environ["no_proxy"] = ".eastmoney.com,.sinajs.cn,.sina.com.cn,.gtimg.cn,.10jqka.com.cn,.hexin.cn"
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE
sys.path.insert(0, BASE)
import ifind_source as ifs
try:
    import 飞书推送 as _feishu   # 模拟盘成交→飞书(60s循环顺手扫账本增量;缺文件不碍管道;#029)
except Exception:
    _feishu = None

D = datetime.date.today().strftime("%Y%m%d")
SELFTEST = "--selftest" in sys.argv
OUT = os.path.join(BASE, "盘中", D); os.makedirs(OUT, exist_ok=True)
LOGP = os.path.join(OUT, "pipeline.log")
QUOTA_CAP = {"实时行情": 300e4, "日内快照": 200e4, "高频序列": 150e4, "历史行情": 100e4, "数据池": 60e4}
QP = os.path.join(BASE, "_学习", "ifind_配额台账_%s.json" % D[:6])

def log(*a):
    line = "%s %s" % (datetime.datetime.now().strftime("%H:%M:%S"), " ".join(str(x) for x in a))
    print(line, flush=True)
    try: open(LOGP, "a", encoding="utf-8").write(line + "\n")
    except Exception: pass

def q_load():
    try: return json.load(open(QP, encoding="utf-8"))
    except Exception: return {}
QUOTA = q_load()
def q_add(pool, cells):
    QUOTA[pool] = QUOTA.get(pool, 0) + int(cells)
    try: json.dump(QUOTA, open(QP, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception: pass
def q_pct(pool): return 100.0 * QUOTA.get(pool, 0) / QUOTA_CAP.get(pool, 1)
def q_gate():
    """配额熔断档: 0正常 1降频(任一池>=80%) 2只保竞价+关注池(>=95%)"""
    m = max(q_pct(p) for p in QUOTA_CAP)
    return 2 if m >= 95 else (1 if m >= 80 else 0)

def prev_trade_day(d):
    ds = sorted(x for x in os.listdir(BASE) if x.isdigit() and len(x) == 8 and x < d)
    return ds[-1] if ds else None
DPREV = prev_trade_day(D)

# ---------- 池构建 ----------
def read_codes(day, fn, col="代码", extra=None):
    out = []
    p = os.path.join(BASE, day or "", fn)
    if day and os.path.isfile(p):
        try:
            for r in csv.DictReader(open(p, encoding="utf-8-sig")):
                c = str(r.get(col, "")).zfill(6)
                if c.isdigit(): out.append((c, r))
        except Exception: pass
    return out

def route_positions():
    """六路在持: [(code,{name,route,reason,buy_px,buy_date,weight})]"""
    R = {"auction": "竞价", "lhb": "席位", "theme": "题材", "logic": "逻辑", "limitup": "质量", "master": "总"}
    out = {}
    for rd, rn in R.items():
        try:
            st = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", rd, "状态.json"), encoding="utf-8"))
            for h in st.get("持仓", []):
                c = str(h.get("code", "")).zfill(6)
                e = out.setdefault(c, {"name": h.get("name"), "sources": [], "reason": h.get("reason", ""),
                                       "buy_px": h.get("buy_px"), "buy_date": h.get("buy_date")})
                if rn not in e["sources"]: e["sources"].append(rn)
        except Exception: pass
    return out

def build_pools():
    pos = route_positions()
    zt = read_codes(DPREV, "zt_pool.csv")
    zb = read_codes(DPREV, "zb_pool.csv")
    strong = read_codes(DPREV, "strong_pool.csv")
    rec = list(pos.keys()) + [c for c, _ in zt] + [c for c, _ in zb] + [c for c, _ in strong][:60]
    seen, record_pool = set(), []
    for c in rec:
        if c not in seen: seen.add(c); record_pool.append(c)
    record_pool = record_pool[:300]
    lb2 = [c for c, r in zt if float(r.get("连板数") or 1) >= 2]
    watch_pool = list(dict.fromkeys(list(pos.keys()) + lb2 + [c for c, _ in zt][:80]))[:150]
    meta = {}
    for c, r in zt: meta[c] = {"name": r.get("名称"), "lb": r.get("连板数"), "ind": r.get("所属行业")}
    for c, r in zb: meta.setdefault(c, {"name": r.get("名称"), "lb": "炸板", "ind": r.get("所属行业")})
    return pos, record_pool, watch_pool, meta

# ---------- 取数 ----------
TICK = {}   # code -> {latest,chg,preclose,open,ts}
def rq(codes, tag):
    """快层RQ: 2动态字段;首轮带preClose/open缓存。配额=码×字段。"""
    if not codes: return 0
    first = any(c not in TICK for c in codes)
    fields = "latest,changeRatio,preClose,open" if first else "latest,changeRatio"
    df = ifs.spot(codes, fields=fields, batch=100, sleep=0.4)
    q_add("实时行情", len(codes) * len(fields.split(",")))
    if df is None: return 0
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    n = 0
    for _, r in df.iterrows():
        c = str(r.get("thscode", ""))[:6]
        e = TICK.setdefault(c, {})
        for k, kk in (("latest", "latest"), ("changeRatio", "chg"), ("preClose", "preclose"), ("open", "open")):
            if k in df.columns and r.get(k) == r.get(k):
                e[kk] = float(r[k]) if r.get(k) is not None else None
        e["ts"] = ts; n += 1
    return n

def dump_watch(codes, path):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    row = {"ts": ts, "t": {c: [TICK.get(c, {}).get("latest"), TICK.get(c, {}).get("chg")] for c in codes if c in TICK}}
    open(path, "a", encoding="utf-8").write(json.dumps(row, ensure_ascii=False) + "\n")

def all_a_codes_cached():
    p = os.path.join(BASE, "_学习", "_全A清单.json")
    try:
        j = json.load(open(p, encoding="utf-8"))
        if (datetime.date.today() - datetime.date.fromisoformat(j["asof"])).days < 7:
            return j["codes"]
    except Exception: pass
    df = ifs.all_a_codes()
    if df is None: return None
    col = "THSCODE" if "THSCODE" in df.columns else ("thscode" if "thscode" in df.columns else None)
    if not col: return None
    codes = [str(x) for x in df[col].dropna()]
    q_add("数据池", len(codes) * 3)
    json.dump({"asof": str(datetime.date.today()), "codes": codes}, open(p, "w", encoding="utf-8"))
    return codes

def frame(codes_ths, tag):
    """全场关键帧: 日内快照池首选(不含BJ),RQ回退(占实时池)。存 auction_frame_{tag}.csv.gz"""
    THS = ifs._mod()
    hs = [c for c in codes_ths if not c.endswith(".BJ")]
    rows, used = [], None
    try:
        if hasattr(THS, "THS_Snapshot"):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for i in range(0, len(hs), 800):
                df = ifs._to_df(THS.THS_Snapshot(",".join(hs[i:i+800]), "latest;amount", "", now, now))
                if df is not None:
                    for _, r in df.iterrows(): rows.append((str(r.get("thscode", ""))[:6], r.get("latest"), r.get("amount")))
            if rows: used = "日内快照"; q_add("日内快照", len(hs) * 2)
    except Exception as e:
        log("frame snapshot EXC", str(e)[:80])
    if not rows:
        df = ifs.spot([c[:6] for c in hs], fields="latest,changeRatio", batch=100, sleep=0.35)
        q_add("实时行情", len(hs) * 2)
        if df is not None:
            rows = [(str(r.get("thscode", ""))[:6], r.get("latest"), r.get("changeRatio")) for _, r in df.iterrows()]
            used = "RQ回退"
    if rows:
        with gzip.open(os.path.join(OUT, "auction_frame_%s.csv.gz" % tag), "wt", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["code", "latest", "x"]); w.writerows(rows)
        log("frame", tag, used, len(rows))
    return bool(rows)

CONCEPT = {"codes": None, "names": {}, "top": []}
def concept_pulse():
    THS = ifs._mod()
    try:
        if CONCEPT["codes"] is None:
            lst = ifs._to_df(THS.THS_iwencai("概念指数", "zhishu"))
            if lst is None or "指数代码" not in lst.columns: return
            CONCEPT["codes"] = [str(x) for x in lst["指数代码"].dropna() if str(x).endswith(".TI")]
            CONCEPT["names"] = dict(zip(lst["指数代码"].astype(str), lst["指数简称"].astype(str)))
        vals = []
        for i in range(0, len(CONCEPT["codes"]), 100):
            grp = ",".join(CONCEPT["codes"][i:i+100])
            df = ifs._to_df(THS.THS_RQ(grp, "changeRatio"))
            if df is not None and "changeRatio" in df.columns:
                for _, r in df.iterrows():
                    try: vals.append((CONCEPT["names"].get(str(r["thscode"]), ""), round(float(r["changeRatio"]), 2)))
                    except Exception: pass
            time.sleep(0.3)
        q_add("实时行情", len(CONCEPT["codes"]) * 1)
        vals.sort(key=lambda x: -(x[1] if x[1] is not None else -99))
        CONCEPT["top"] = vals[:6]
    except Exception as e:
        log("concept EXC", str(e)[:80])

PULSE = {}
def zt_pulse():
    """涨停/炸板家数: iwencai首选(免配额),THS dataapi回退。"""
    THS = ifs._mod()
    got = {}
    for key, q in (("zt", "涨停"), ("zb", "炸板")):
        try:
            df = ifs._to_df(THS.THS_iwencai(q, "stock"))
            if df is not None: got[key] = len(df)
        except Exception: pass
    if "zt" not in got:
        try:
            import urllib.request
            u = "https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?page=1&limit=1&field=199112&filter=HS,GEM2STAR&date=" + D
            j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=10).read().decode())
            got["zt"] = (j.get("data") or {}).get("total")
        except Exception: pass
    zt, zb = got.get("zt"), got.get("zb")
    PULSE.update({"zt": zt, "zb": zb,
                  "zb_rate": round(100.0 * zb / (zt + zb), 1) if (zt and zb is not None and zt + zb > 0) else None,
                  "concept_top": CONCEPT["top"], "ts": datetime.datetime.now().strftime("%H:%M:%S")})
    json.dump(PULSE, open(os.path.join(OUT, "pulse.json"), "w", encoding="utf-8"), ensure_ascii=False)

def sse_benchmark():
    """上证指数近60日收盘→_学习/_指数基准.json(展示基准线,v1.9拍板①)"""
    try:
        THS = ifs._mod()
        end = datetime.date.today(); start = end - datetime.timedelta(days=95)
        df = ifs._to_df(THS.THS_HQ("000001.SH", "close", "", str(start), str(end)))
        q_add("历史行情", len(df) if df is not None else 0)
        if df is not None and "close" in df.columns:
            out = {str(r["time"]).replace("-", ""): float(r["close"]) for _, r in df.iterrows()}
            json.dump({"asof": D, "sse_close": out}, open(os.path.join(BASE, "_学习", "_指数基准.json"), "w", encoding="utf-8"))
            log("上证基准", len(out), "日")
    except Exception as e:
        log("sse EXC", str(e)[:80])

# ---------- warboard ----------
def build_warboard(pos, meta, watch_pool):
    cards = []
    for c, e in pos.items():
        t = TICK.get(c, {})
        pnl = None
        try: pnl = round((t.get("latest") / float(e["buy_px"]) - 1) * 100, 2)
        except Exception: pass
        cards.append({"code": c, "name": e["name"], "sources": e["sources"], "status": "持有中",
                      "theme": (meta.get(c) or {}).get("ind"), "px": t.get("latest"), "chg_pct": t.get("chg"),
                      "why": (e.get("reason") or "")[:90],
                      "trigger": "已于%s成交 ¥%s" % (e.get("buy_date"), e.get("buy_px")), "abort": "—",
                      "sell": "阶段①观察期:执行仍走晚间指令;阶段②起接盘中通道",
                      "hold": {"pnl_pct": pnl} if pnl is not None else None,
                      "auction": _auc(c), "timeline": [["09:25", "竞价盘点(自动)"]]})
    for c in watch_pool:
        if c in pos: continue
        m = meta.get(c) or {}
        if not m.get("lb") or m.get("lb") == "炸板": continue
        try: lb = int(float(m["lb"]))
        except Exception: lb = 1
        if lb < 2: continue
        t = TICK.get(c, {})
        cards.append({"code": c, "name": m.get("name"), "sources": ["总"], "status": "观察",
                      "theme": m.get("ind"), "px": t.get("latest"), "chg_pct": t.get("chg"),
                      "why": "昨%d连板梯队(阶段①自动入册,题材列暂用行业,阶段②接题材归位)" % lb,
                      "trigger": "阶段①只观察不参与", "abort": "—", "sell": "—",
                      "auction": _auc(c), "timeline": []})
    acct = None
    try:
        st = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "master", "状态.json"), encoding="utf-8"))
        nv = json.load(open(os.path.join(BASE, "_学习", "_模拟盘", "master", "净值.json"), encoding="utf-8"))
        curve = [[k, float(v["nav"] if isinstance(v, dict) else v)] for k, v in sorted(nv.items())]
        acct = {"nav": st.get("nav"), "week_pct": st.get("本周pct"), "bench_week_pct": st.get("基准本周pct"),
                "cash_pct": round(st.get("现金", 0) / 1e6 * 100), "pos_pct": round(100 - st.get("现金", 0) / 1e6 * 100),
                "n_pos": len(st.get("持仓", [])), "curve": curve}
    except Exception: pass
    judg = None
    jp = os.path.join(OUT, "judgment_hero.json")
    if os.path.isfile(jp):
        try: judg = json.load(open(jp, encoding="utf-8"))
        except Exception: pass
    W = {"date": D, "mode": "live", "ts": datetime.datetime.now().strftime("%H:%M:%S"),
         "pipeline": {"last_tick": PULSE.get("ts") or datetime.datetime.now().strftime("%H:%M:%S"), "fresh_sec": 0,
                      "quota": {k: {"used": round(QUOTA.get(k, 0) / 1e4, 1), "cap": int(QUOTA_CAP[k] / 1e4)} for k in QUOTA_CAP}},
         "pulse": {"zt": PULSE.get("zt"), "dt": PULSE.get("dt"), "zb": PULSE.get("zb"),
                   "zb_rate": PULSE.get("zb_rate"), "top_lb": None, "concept_top": PULSE.get("concept_top") or []},
         "auction_review": {"ts": "09:25", "summary": "阶段①自动盘点(gap判定)"},
         "account": acct, "judgment": judg, "cards": cards}
    json.dump(W, open(os.path.join(OUT, "warboard.json"), "w", encoding="utf-8"), ensure_ascii=False)
    try:
        subprocess.run([sys.executable, os.path.join(BASE, "生成作战台.py"), D], cwd=BASE, timeout=60,
                       stdout=subprocess.DEVNULL)
    except Exception as e:
        log("page EXC", str(e)[:60])

def _auc(c):
    t = TICK.get(c, {})
    if t.get("open") and t.get("preclose"):
        gap = round((t["open"] / t["preclose"] - 1) * 100, 2)
        v = "符合预案" if abs(gap) <= 3 else ("恶化" if gap > 5 or gap < -5 else "超预期")
        return {"gap_pct": gap, "verdict": v, "note": "自动gap判定(阶段①)"}
    return None

# ---------- 主循环 ----------
def hhmm(): return datetime.datetime.now().strftime("%H%M%S")
def until(ts):
    now = datetime.datetime.now()
    tgt = now.replace(hour=int(ts[:2]), minute=int(ts[2:4]), second=int(ts[4:6]), microsecond=0)
    return (tgt - now).total_seconds()

def main():
    if datetime.date.today().weekday() >= 5 and not SELFTEST:
        print("周末,不跑"); return
    if not ifs.login():
        log("[X] iFind登录失败,管道退出(链路无恙:作战台显示断更)"); sys.exit(1)
    pos, record_pool, watch_pool, meta = build_pools()
    log("池: 录像%d 关注%d 持仓%d 昨日%s" % (len(record_pool), len(watch_pool), len(pos), DPREV))
    sse_benchmark()
    ajl = os.path.join(OUT, "auction_traj.jsonl"); wjl = os.path.join(OUT, "watch.jsonl")
    if SELFTEST:
        rep = {"d": D, "steps": {}}
        rep["steps"]["录像池tick"] = rq(record_pool, "auc") ; dump_watch(record_pool, ajl)
        allc = all_a_codes_cached()
        rep["steps"]["全A清单"] = len(allc) if allc else 0
        rep["steps"]["关键帧"] = frame(allc or [], "selftest") if allc else False
        rep["steps"]["快层tick"] = rq(watch_pool, "w"); dump_watch(watch_pool, wjl)
        concept_pulse(); zt_pulse()
        rep["steps"]["脉搏"] = PULSE
        build_warboard(pos, meta, watch_pool)
        rep["steps"]["warboard"] = os.path.getsize(os.path.join(OUT, "warboard.json"))
        rep["quota万格"] = {k: round(v / 1e4, 2) for k, v in QUOTA.items()}
        json.dump(rep, open(os.path.join(OUT, "selftest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        log("[√√] 自测完成", json.dumps(rep["steps"], ensure_ascii=False, default=str)[:300])
        log("报告:", os.path.join(OUT, "selftest.json")); ifs.logout(); return
    allc = all_a_codes_cached() or []
    frames = [("091530", "091530"), ("091940", "091940"), ("092100", "092100"), ("092440", "092440"), ("145200", "145200")]
    fdone = set()
    next_concept = 0; next_board = 0
    while True:
        now = hhmm()
        if now >= "150600": break
        if "113100" <= now < "125900": time.sleep(20); continue
        if now < "091500": time.sleep(min(5, max(1, until("091500")))); continue
        gate = q_gate()
        try:
            for ft, tag in frames:
                if ft not in fdone and now >= ft and gate < 2 or (ft not in fdone and now >= ft and ft.startswith("09")):
                    if now >= ft: frame(allc, tag); fdone.add(ft)
            if now < "092540":                      # 竞价段: 录像池20秒
                rq(record_pool, "auc"); dump_watch(record_pool, ajl); time.sleep(20 if gate == 0 else 40)
            elif now < "093000":
                time.sleep(3)
            else:                                    # 盘中段
                rq(watch_pool, "w"); dump_watch(watch_pool, wjl)
                tnow = time.time()
                if tnow >= next_concept and gate < 2:
                    concept_pulse(); zt_pulse(); next_concept = tnow + (600 if gate == 0 else 1200)
                if tnow >= next_board:
                    build_warboard(pos, meta, watch_pool); next_board = tnow + 60
                    if _feishu: _feishu.scan_quiet()
                hi = now < "100000"
                time.sleep((30 if hi else 60) * (2 if gate >= 1 else 1))
        except Exception as e:
            log("loop EXC", str(e)[:120], traceback.format_exc()[-200:])
            try: ifs._state["logged"] = False; ifs.login(verbose=False)
            except Exception: pass
            time.sleep(15)
    build_warboard(pos, meta, watch_pool)
    if _feishu: _feishu.scan_quiet()
    log("[√] 15:06 收工. 配额(万格):", {k: round(v / 1e4, 1) for k, v in QUOTA.items()})
    ifs.logout()

if __name__ == "__main__":
    main()
