# -*- coding: utf-8 -*-
r"""iFind回填驱动.py — P0a纯加法数据回填(宿主每晚,2026-07-18 #037,设计稿v2.0第八节)
与阶段①②零耦合: 只新增 _学习/ 产物,不碰管道/取数/评分/哨兵/prompt任何现行文件。
三步(均幂等可断点续跑,共享 ifind_配额台账_{YYYYMM}.json 与管道同格式):
  ①概念指数日K增量回填(历史行情池): 全部885/886概念指数 close+amount,首跑约一年≈19.4万格,之后每日增量
     → _学习/_概念指数日K/{thscode}.csv (题材五维"成交额份额/抽血量化"的原料)
  ②iwencai盘后六项存档(零配额): 业绩预告/解禁/减持/两融/大宗/股东户数 → _学习/_iwencai存档/{d}_*.json
  ③分时形态库回填(高频序列池,预算默认4万格/晚): _ths_zt_pool.json 全部涨停样本 T日+T+1 五分钟K(close,volume)
     ★优先级=先回封样本(open_num>=1)的T日(炸板时点研究先有料),再全量按日期新→旧
     → _学习/_分时库/{涨停日}.jsonl.gz + 状态=_学习/_分时库回填状态.json
护栏: 工作日09:00-15:20拒跑(防与盘中管道抢同账号登录); 高频池台账>=80%停③; 历史池>=80%停①。
用法: python iFind回填驱动.py [--budget 40000] [--no-hf] (双击 数据回填每晚.bat)
"""
import os, sys, json, gzip, time, datetime, argparse
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, BASE)
import ifind_source as ifs

XUE = os.path.join(BASE, "_学习")
NOW = datetime.datetime.now()
QP = os.path.join(XUE, "ifind_配额台账_%s.json" % NOW.strftime("%Y%m"))
QUOTA_CAP = {"实时行情": 300e4, "日内快照": 200e4, "高频序列": 150e4, "历史行情": 100e4, "数据池": 60e4}

def log(*a):
    print("%s %s" % (datetime.datetime.now().strftime("%H:%M:%S"), " ".join(str(x) for x in a)), flush=True)

def q_load():
    try: return json.load(open(QP, encoding="utf-8"))
    except Exception: return {}
QUOTA = q_load()
def q_add(pool, cells):
    QUOTA.update(q_load())  # 合并其他进程(管道)可能写过的最新值
    QUOTA[pool] = QUOTA.get(pool, 0) + int(cells)
    try: json.dump(QUOTA, open(QP, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception: pass
def q_pct(pool): return 100.0 * q_load().get(pool, 0) / QUOTA_CAP.get(pool, 1)

# ---------- 护栏: 交易时段拒跑 ----------
def trading_hours_guard():
    if NOW.weekday() < 5 and datetime.time(9, 0) <= NOW.time() <= datetime.time(15, 20):
        log("[护栏] 工作日09:00-15:20拒跑(盘中管道占用iFind登录),晚间再来"); sys.exit(0)

# ---------- ① 概念指数日K增量 ----------
def step_concepts():
    if q_pct("历史行情") >= 80:
        log("[①概念] 历史池>=80%,本步跳过"); return
    outdir = os.path.join(XUE, "_概念指数日K"); os.makedirs(outdir, exist_ok=True)
    THS = ifs._mod()
    lst = None
    for q in ("同花顺概念指数", "概念指数"):
        try:
            lst = ifs._to_df(THS.THS_iwencai(q, "zhishu"))
            if lst is not None and len(lst) > 3: break
        except Exception: lst = None
    if lst is None or not len(lst):
        log("[①概念] iwencai清单失败,跳过"); return
    cands = [c for c in lst.columns if "code" in str(c).lower() or "代码" in str(c)]
    codecol = max(cands, key=lambda c: lst[c].notna().sum(), default=None) if cands else None
    namecol = next((c for c in lst.columns if "简称" in c or "名称" in c), None)
    codes = [str(x) for x in lst[codecol].dropna().tolist() if str(x)[:3] in ("885", "886")] if codecol else []
    names = dict(zip(lst[codecol].astype(str), lst[namecol].astype(str))) if (codecol and namecol) else {}
    if not codes:
        log("[①概念] 清单空,跳过"); return
    end = NOW.strftime("%Y-%m-%d"); default_start = (NOW - datetime.timedelta(days=400)).strftime("%Y-%m-%d")
    done = miss = cells = 0
    for code in codes:
        tc = code if "." in code else code + ".TI"
        fp = os.path.join(outdir, tc.replace(".", "_") + ".csv")
        start = default_start; old = []
        if os.path.isfile(fp):
            try:
                old = open(fp, encoding="utf-8").read().rstrip("\n").split("\n")
                last = old[-1].split(",")[0]
                if last >= end: continue  # 已最新
                start = (datetime.datetime.strptime(last, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            except Exception: old = []
        df = None
        try:
            df = ifs._to_df(ifs._mod().THS_HQ(tc, "close,amount", "", start, end))
        except Exception: df = None
        if df is None or not len(df):
            miss += 1; continue
        cells += len(df) * 2
        rows = ["%s,%s,%s" % (r["time"], r.get("close"), r.get("amount")) for _, r in df.iterrows()]
        header = [] if old else ["# %s %s" % (tc, names.get(code, "")), "time,close,amount"]
        with open(fp, "a", encoding="utf-8") as f:
            f.write("\n".join(header + rows) + "\n")
        done += 1; time.sleep(0.12)
        if q_load().get("历史行情", 0) + cells >= 0.85 * QUOTA_CAP["历史行情"]:
            log("[①概念] 历史池临近85%,中断续待明晚"); break
    q_add("历史行情", cells)
    log("[①概念] 更新%d个 无数据%d个 计%d格 历史池%.1f%%" % (done, miss, cells, q_pct("历史行情")))

# ---------- ② iwencai盘后存档(零配额) ----------
IWENCAI_QS = {
    # ★问句全部沿用ifind_测试报告3实测通过的原文(iwencai语义解析敏感,别自由发挥)
    "业绩预告": "2026年中报业绩预增的股票,预告净利润同比增幅,业绩预告公告日期",
    "解禁30天": "未来30天有限售股解禁的股票,解禁日期,解禁市值",
    "减持公告": "近30天发布减持计划公告的股票",
    "两融": "{dcn}融资余额,融资买入额,融券余额",
    "大宗交易": "{dcn}发生大宗交易的股票,大宗交易成交额,大宗交易折溢价率",
    "股东户数": "最新股东户数环比下降超过5%的股票,股东户数",
}
def step_iwencai():
    d = NOW.date()
    while d.weekday() >= 5: d -= datetime.timedelta(days=1)
    ds = d.strftime("%Y%m%d"); dcn = "%d年%d月%d日" % (d.year, d.month, d.day)
    outdir = os.path.join(XUE, "_iwencai存档"); os.makedirs(outdir, exist_ok=True)
    THS = ifs._mod(); n = 0
    for name, q in IWENCAI_QS.items():
        fp = os.path.join(outdir, "%s_%s.json" % (ds, name))
        if os.path.isfile(fp): continue  # 幂等
        try:
            df = ifs._to_df(THS.THS_iwencai(q.format(dcn=dcn), "stock"))
            if df is None or not len(df):
                log("[②存档] %s 无数据(照实跳过)" % name); continue
            df.to_json(fp, orient="records", force_ascii=False)
            n += 1; time.sleep(0.3)
        except Exception as e:
            log("[②存档] %s 异常 %s" % (name, str(e)[:80]))
    log("[②存档] %s 新落%d项(零配额)" % (ds, n))

# ---------- ③ 分时形态库回填(5分钟K, 预算制) ----------
SAFE_PCT = 78  # ★#038补注3: 高频池安全线——盘中管道q_gate看"任一池>=80%即降频",回填永不许把池推过78%
def step_hf(budget):
    headroom = int(QUOTA_CAP["高频序列"] * SAFE_PCT / 100) - q_load().get("高频序列", 0)
    if headroom <= 0:
        log("[③分时] 高频池已达%d%%安全线(现%.1f%%),本晚停,等翻月" % (SAFE_PCT, q_pct("高频序列"))); return
    budget = min(budget, headroom)
    zp = os.path.join(XUE, "_ths_zt_pool.json")
    try: pool = json.load(open(zp, encoding="utf-8"))
    except Exception:
        log("[③分时] 读不到_ths_zt_pool.json,跳过"); return
    days = sorted(pool.keys())
    nxt = {days[i]: days[i + 1] for i in range(len(days) - 1)}  # T+1=池内下一交易日
    stp = os.path.join(XUE, "_分时库回填状态.json")
    try: state = json.load(open(stp, encoding="utf-8"))
    except Exception: state = {"done": []}
    done = set(state["done"])
    outdir = os.path.join(XUE, "_分时库"); os.makedirs(outdir, exist_ok=True)
    # 任务队列: 阶段A=回封样本(open_num>=1)T日腿,新→旧; 阶段B=其余全部腿,新→旧
    tasks = []
    for d in reversed(days):
        for it in pool[d]:
            if int(it.get("open_num") or 0) >= 1:
                tasks.append((d, str(it["code"]).zfill(6), "T", d))
    for d in reversed(days):
        for it in pool[d]:
            code = str(it["code"]).zfill(6)
            if int(it.get("open_num") or 0) < 1:
                tasks.append((d, code, "T", d))
            if d in nxt:
                tasks.append((d, code, "T1", nxt[d]))
    THS = ifs._mod(); cells = fetched = 0
    spent = 0  # ★#038bug修复: cells每100腿flush清零,预算必须用独立累计器(首晚曾致预算失控)
    fail_streak = []  # ★断路器: 连续失败的腿(登录被踢/断网时防止把后续腿全误标done)
    # ★年限墙(#038补注2): iFind高频只保留近1年,更早的腿永远取不到——回填前过滤,
    #   照实标"超窗"永久跳过(实测360天前2025-07-23可取,382天前20250701不可取)
    cutoff = (NOW - datetime.timedelta(days=360)).strftime("%Y%m%d")
    over = state.get("超窗", [])
    n_over0 = len(over)
    for pd_, code, leg, fd in tasks:
        key = "%s|%s|%s" % (pd_, code, leg)
        if key in done: continue
        if fd < cutoff:
            done.add(key); over.append(key); continue  # 超窗:不发请求,永久标记
        if spent >= budget:
            log("[③分时] 本晚预算%d格用完" % budget); break
        fds = "%s-%s-%s" % (fd[:4], fd[4:6], fd[6:])
        # ★ifs.ths_code把9开头一律判SH,但920xxx=北交所新代码——本地纠偏(不碰共用ifind_source)
        tc = code + ".BJ" if code.startswith("92") else ifs.ths_code(code)
        try:
            df = ifs._to_df(THS.THS_HF(tc, "close;volume", "Interval:5",
                                       fds + " 09:30:00", fds + " 15:00:00"))
        except Exception: df = None
        done.add(key)  # 失败也记(退市/停牌无分时,不无限重试;可手工从状态删除重试)
        if df is None or not len(df):
            fail_streak.append(key)
            if len(fail_streak) >= 10:  # 连续10腿失败=大概率登录被踢/断网,回滚这10腿并停
                for k in fail_streak: done.discard(k)
                log("[③分时] ★连续%d腿失败,疑似登录被踢/断网——回滚失败腿并停止本晚" % len(fail_streak))
                break
        else:
            fail_streak = []
        if df is not None and len(df):
            rows = [json.dumps({"code": code, "leg": leg, "time": str(r["time"]),
                                "close": r.get("close"), "volume": r.get("volume")}, ensure_ascii=False)
                    for _, r in df.iterrows()]
            with gzip.open(os.path.join(outdir, pd_ + ".jsonl.gz"), "at", encoding="utf-8") as f:
                f.write("\n".join(rows) + "\n")
            cells += len(df) * 2; spent += len(df) * 2; fetched += 1
        time.sleep(0.1)
        if fetched % 100 == 0 and fetched:
            state["done"] = sorted(done); json.dump(state, open(stp, "w", encoding="utf-8"))
            q_add("高频序列", cells); cells = 0
            if q_pct("高频序列") >= 80:
                log("[③分时] 高频池达80%,停"); break
    state["done"] = sorted(done); state["总腿数"] = len(tasks); state["已完成"] = len(done)
    state["超窗"] = over; state["最后运行"] = str(NOW)
    json.dump(state, open(stp, "w", encoding="utf-8"), ensure_ascii=False)
    q_add("高频序列", cells)
    log("[③分时] 本晚取%d腿 新标超窗%d腿(累计%d) 进度%d/%d 高频池%.1f%%"
        % (fetched, len(over) - n_over0, len(over), len(done), len(tasks), q_pct("高频序列")))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=40000, help="③分时回填每晚格数预算")
    ap.add_argument("--no-hf", action="store_true", help="跳过③分时回填")
    a = ap.parse_args()
    trading_hours_guard()
    if not ifs.login():
        log("[X] iFind登录失败,退出"); sys.exit(1)
    try:
        step_concepts()
        step_iwencai()
        if not a.no_hf: step_hf(a.budget)
    finally:
        ifs.logout()
    log("回填驱动完成。台账: " + json.dumps(q_load(), ensure_ascii=False))
