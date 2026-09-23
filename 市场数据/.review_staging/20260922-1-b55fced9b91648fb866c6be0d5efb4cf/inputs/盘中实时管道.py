# -*- coding: utf-8 -*-
"""
盘中实时管道 v1.1 (2026-08-13 重建)
================================================
原版(竞价轨迹+预案+实时采集)于 8/11 前后丢失, 此版按报警档案+消费者 agent 需求重建。
由 intraday_pipeline_launcher.py (cron 09:14) spawn, 常驻到 15:05。

职责:
  1) 09:15-09:25 竞价段: 观察池逐票竞价轨迹 → 盘中/{d}/auction_traj.jsonl
  2) 09:30-15:00 连续段: 观察池实时 tick(每60s) → 盘中/{d}/realtime_ticks.jsonl
  3) 数据源优先级: iFinD THS_RealtimeQuotes 批量(主) → 腾讯 qt.gtimg.cn 批量(降级)
     东财 82.push2 clist 因风控动态封禁(2026-08-13 实测)不在链内。

观察池: 昨日涨停池(数据/每日/{prev}/zt_pool.csv 或 _学习/涨停复盘/{prev}/limitup.json)
        为空时用自选兜底(市场数据/自选/自选池.csv), 再空则只采上证指数+沪深300。
playbook.json: 本管道不产(属晚间复盘 agent 产物), 保持原边界。

用法: python 盘中实时管道.py [--selftest]
      --selftest: 采集一轮即退出(供 cron 体检/人工验证)
退出条件: 15:05 后自然退出; 连续 30 分钟全源失败则报警退出。
"""
import os, sys, json, time, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据"
MDIR = os.path.join(BASE, "市场数据")
POOL_CANDIDATES = []          # 启动时填充
IFIND = None                  # iFinDPy 句柄(登录后)
SELFTEST = "--selftest" in sys.argv
POOL_INFO = {}                # 观察池来源/日期/是否滞后(供 tick 落档审计)
ALARM_PATH = None             # main() 里设为 盘中/{d}/pipeline_alarm.jsonl
_IFIND_FAILS = 0              # iFinD 实时连续失败计数(熔断用)
_IFIND_DOWN_UNTIL = 0.0       # iFinD 熔断截止时刻(time.time())


def _alarm(kind, detail):
    """报警落档(不退出)。type 字段供哨兵/复盘消费。"""
    path = ALARM_PATH
    if not path:
        log("ALARM %s: %s" % (kind, detail))
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "level": "ALARM", "type": kind, "detail": detail},
                               ensure_ascii=False) + "\n")
    except Exception as e:
        log("报警写盘失败: %s" % e)
    log("ALARM %s: %s" % (kind, detail))


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line, flush=True)


def today():
    return datetime.date.today().strftime("%Y%m%d")


def prev_trading_day(d):
    """留档简化版: 周一前=周五; 其余前一自然日(节假日由调用方容错)"""
    dt = datetime.datetime.strptime(d, "%Y%m%d")
    back = dt - datetime.timedelta(days=3 if dt.weekday() == 0 else 1)
    return back.strftime("%Y%m%d")


def _load_zt_pool_file(f):
    import csv
    rows = list(csv.DictReader(open(f, encoding="utf-8-sig", errors="replace")))
    codes = []
    for r in rows:
        code = str(r.get("代码", r.get("股票代码", ""))).strip()
        name = str(r.get("名称", r.get("股票简称", ""))).strip()
        if code and len(code) == 6:
            codes.append((code, name))
    return codes


def load_pool(d):
    """观察池: 昨日涨停池 → 回溯最近可用涨停池 → 自选 → 指数兜底, 返回 [(code, name), ...]

    ★20260911 修复: 原实现只认"昨日"池, 主取数链滞后一个交易日时(实测 9/10、9/11 的
      {prev}/zt_pool.csv 均未落档)直接退指数兜底 → 观察池只剩 3 个指数 → 竞价撤单差分/
      开盘验证维/日内温度曲线/日内轮动图谱 四项能力必然 unavailable。改为回溯最多 10 个
      交易日取最近可用池, 并落 ALARM(pool_stale) 声明滞后; 只有连池都没有才退指数。
      池来源/日期写进 POOL_INFO, 随 tick 落档, 供复盘审计(零编造, 不假装是当日池)。
    """
    prev = prev_trading_day(d)
    cur = prev
    for _ in range(10):
        for f in (os.path.join(MDIR, cur, "zt_pool.csv"),
                  os.path.join(MDIR, "数据", "每日", cur, "zt_pool.csv"),
                  os.path.join(MDIR, "每日数据", cur, "zt_pool.csv"),
                  os.path.join(BASE, "_学习", "涨停复盘", cur, "zt_pool.csv")):
            if not os.path.exists(f):
                continue
            try:
                codes = _load_zt_pool_file(f)
            except Exception as e:
                log("池读取失败 %s: %s" % (f, e))
                continue
            if codes:
                stale = cur != prev
                POOL_INFO.update(kind="zt_pool", source=f, date=cur, count=len(codes), stale=stale)
                log("观察池=涨停池 %s (%d只)%s" % (f, len(codes), " [⚠池滞后: 目标 %s 未落档]" % prev if stale else ""))
                if stale:
                    _alarm("pool_stale", "目标日 %s 涨停池未落档, 降级用最近可用池 %s(%d只)" % (prev, cur, len(codes)))
                return codes
        cur = prev_trading_day(cur)
    # 自选兜底
    for f in [os.path.join(MDIR, "自选", "自选池.csv"), os.path.join(MDIR, "自选池.csv")]:
        if os.path.exists(f):
            try:
                import csv
                rows = list(csv.DictReader(open(f, encoding="utf-8-sig", errors="replace")))
                codes = [(str(r.get("代码", "")).strip(), str(r.get("名称", "")).strip())
                         for r in rows if str(r.get("代码", "")).strip()]
                if codes:
                    log("观察池=自选 (%d只)" % len(codes))
                    POOL_INFO.update(kind="watchlist", source=f, date=d, count=len(codes), stale=True)
                    _alarm("pool_fallback", "涨停池/自选池均无, 退自选兜底(%d只), 盘中能力口径降级" % len(codes))
                    return codes
            except Exception as e:
                log("自选读取失败: %s" % e)
    log("观察池=指数兜底(上证+沪深300+创业板)")
    POOL_INFO.update(kind="index_fallback", source="", date=d, count=3, stale=True)
    _alarm("pool_fallback", "涨停池/自选池均无, 退指数兜底(3只指数), 四项盘中能力将 unavailable")
    return [("000001.SH", "上证指数"), ("000300.SH", "沪深300"), ("399006.SZ", "创业板指")]


def ths_code(code):
    if code.endswith((".SH", ".SZ", ".BJ")):
        return code
    if code.startswith(("4", "8")):
        return code + ".BJ"
    if code.startswith(("5", "6", "9")):
        return code + ".SH"
    return code + ".SZ"


def ifind_login():
    global IFIND
    try:
        import iFinDPy
        auth = json.load(open(os.path.join(BASE, "_ifind_auth.json"), encoding="utf-8"))
        rc = iFinDPy.THS_iFinDLogin(auth["account"], auth["password"])
        IFIND = iFinDPy if rc == 0 else None
        log("iFinD login rc=%s" % rc)
        return rc == 0
    except Exception as e:
        log("iFinD login 异常: %s" % e)
        IFIND = None
        return False


def fetch_ifind(codes):
    """iFinD 批量实时: 返回 {thscode: {latest, pct, amount, volume, bid1, ask1}}"""
    if IFIND is None:
        return None
    try:
        code_str = ",".join(ths_code(c) for c, _ in codes)
        r = IFIND.THS_RealtimeQuotes(code_str,
            "latest;changeRatio;amount;volume;bid1;ask1;open;high;low;preClose")
        if not isinstance(r, dict) or r.get("errorcode") != 0:
            log("iFinD 实时 errorcode=%s" % (r.get("errorcode") if isinstance(r, dict) else "?"))
            return None
        out = {}
        for t in r.get("tables") or []:
            code = t.get("thscode")          # 外层标量
            nt = t.get("table")              # 嵌套 OrderedDict, 每字段=list
            if not code or not isinstance(nt, dict):
                continue
            row = {}
            for k in ("latest", "changeRatio", "amount", "volume",
                      "bid1", "ask1", "open", "high", "low", "preClose"):
                v = nt.get(k)
                if isinstance(v, list) and v:
                    row[k] = v[-1]
                else:
                    row[k] = None
            row["pct"] = row.get("changeRatio")   # 与腾讯 fetch 键名统一
            out[code] = row
        return out or None
    except Exception as e:
        log("iFinD 实时异常: %s" % e)
        return None


def fetch_tencent(codes):
    """腾讯批量: q=sh600519,sz000001,... 返回 {code6: {...}}

    ★20260911 修复三处(9/10、9/11 全天降级源失效的直接原因):
      ① 拼接: 原用原始 c 拼前缀, 对带后缀代码(指数兜底池 "000001.SH")拼出 "sh000001.SH"
         非法查询 → 腾讯返 v_pv_none_match → 静默返回 None。改为取 6 位裸代码。
      ② 解码: 腾讯返回 GBK 字节, text=True 在 PYTHONUTF8=1 环境按 utf-8 解码抛错 →
         r.stdout=None → `"v_pv_none_match" in None` TypeError。改为 errors="replace"。
      ③ 空结果不静默: 解析后无有效行即 log(区分"接口无匹配"与"有响应但字段不足")。
    """
    try:
        q = ",".join(("sh" if ths_code(c).endswith("SH") else "sz") + str(c).split(".")[0]
                     for c, _ in codes)
        url = "http://qt.gtimg.cn/q=" + q
        r = subprocess.run(["curl", "--noproxy", "*", "-s", "-m", "10", url],
                           capture_output=True, text=True, errors="replace", timeout=30)
        if r.returncode != 0:
            log("腾讯实时失败 rc=%s" % r.returncode)
            return None
        stdout = r.stdout or ""
        out = {}
        for line in stdout.strip().split(";"):
            if "=" not in line:
                continue
            head, body = line.split("=", 1)
            code = head.split("_")[-1][2:]
            f = body.strip('"\n').split("~")
            if len(f) < 40:
                continue
            out[code] = {"latest": float(f[3]) if f[3] else None,
                         "pct": float(f[32]) if f[32] else None,
                         "amount": float(f[37]) if f[37] else None,
                         "volume": float(f[36]) if f[36] else None,
                         "bid1": float(f[9]) if f[9] else None,
                         "ask1": float(f[19]) if f[19] else None,
                         "open": float(f[5]) if f[5] else None,
                         "high": float(f[33]) if f[33] else None,
                         "low": float(f[34]) if f[34] else None,
                         "preClose": float(f[4]) if f[4] else None}
        if not out:
            log("腾讯实时空结果(none_match=%s, 请求%d只)" % ("v_pv_none_match" in stdout, len(codes)))
            return None
        return out
    except Exception as e:
        log("腾讯实时异常: %s" % e)
        return None


def fetch_batch(codes):
    """源优先级: iFinD → 腾讯; iFinD 连续失败 3 次熔断 10 分钟, 期间主源切腾讯(不再每轮白等)。

    ★20260911 新增熔断: 实测 iFinD 实时整段返 -1010(登录态失效)时, 原实现每轮先白等一次
      iFinD, 再走腾讯; 熔断后 tick 直接由腾讯产出, 保证盘中证据不断档。
    """
    global _IFIND_FAILS, _IFIND_DOWN_UNTIL
    now = time.time()
    if IFIND is not None and now >= _IFIND_DOWN_UNTIL:
        d = fetch_ifind(codes)
        if d:
            _IFIND_FAILS = 0
            return ("iFinD", d)
        _IFIND_FAILS += 1
        if _IFIND_FAILS >= 3:
            _IFIND_DOWN_UNTIL = now + 600
            _alarm("ifind_breaker", "iFinD 实时连续 %d 次无数据 → 熔断10分钟, 主源暂切腾讯" % _IFIND_FAILS)
    d = fetch_tencent(codes)
    if d:
        return ("腾讯", d)
    return (None, None)


def write_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def run_auction_phase(codes, outdir, d):
    """09:15-09:25 竞价轨迹, 每20s一轮"""
    log("竞价段启动 %d只" % len(codes))
    while True:
        now = datetime.datetime.now()
        hm = now.strftime("%H:%M")
        if hm >= "09:26":
            break
        if hm < "09:15":
            time.sleep(10)
            continue
        src, data = fetch_batch(codes)
        if data:
            row = {"ts": now.strftime("%Y-%m-%d %H:%M:%S"), "phase": "auction",
                   "src": src, "n": len(data)}
            for c, name in codes:
                tc = ths_code(c)
                v = data.get(tc) or data.get(c)
                if v:
                    row.setdefault("rows", []).append(
                        {"code": c, "name": name, "latest": v["latest"], "pct": v["pct"],
                         "amount": v["amount"], "bid1": v["bid1"], "ask1": v["ask1"]})
            write_jsonl(os.path.join(outdir, "auction_traj.jsonl"), row)
            log("竞价tick %s 源=%s" % (hm, src))
        time.sleep(20)
    log("竞价段结束")


def run_continuous_phase(codes, outdir, d):
    """连续段: 每60s 采一轮 → 落 盘中/{d}/realtime_ticks.jsonl。

    ★20260911 修复: 原实现「连续30分钟全源失败 → 报警并 break」把全天多时点证据一次性丢掉
      (9/10、9/11 实测 10:00 退出, 之后零采样; 当日锁残留还导致当天不再重启)。改为报警但不
      退出(每 30 分钟最多报一次), 全天保持重试; 池为兜底时每 10 分钟重试真池, 真池落档即自动
      升级(9/9 实测真池 09:21 落档, 仅晚于开盘 7 分钟)。
    """
    log("连续段启动")
    fail_streak = 0
    last_alarm_min = -30
    last_pool_try = 0.0
    while True:
        now = datetime.datetime.now()
        hm = now.strftime("%H:%M")
        if hm >= "15:05":
            log("收盘退出")
            break
        if hm < "09:31" and not SELFTEST:
            time.sleep(10)
            continue
        # 兜底池自动升级: 真池(昨日涨停池)落档后本轮起改用真池
        if POOL_INFO.get("kind") != "zt_pool" and time.time() - last_pool_try >= 600:
            last_pool_try = time.time()
            new_codes = load_pool(d)
            if POOL_INFO.get("kind") == "zt_pool" and new_codes and new_codes != codes:
                log("观察池升级: 兜底 → 真池(%d只), 本轮起按真池采样" % len(new_codes))
                codes = new_codes
        src, data = fetch_batch(codes)
        if data:
            fail_streak = 0
            row = {"ts": now.strftime("%Y-%m-%d %H:%M:%S"), "phase": "continuous",
                   "src": src, "n": len(data),
                   "pool_date": POOL_INFO.get("date"), "pool_kind": POOL_INFO.get("kind"),
                   "pool_stale": bool(POOL_INFO.get("stale"))}
            for c, name in codes:
                tc = ths_code(c)
                v = data.get(tc) or data.get(c) or data.get(str(c).split(".")[0])
                if v:
                    row.setdefault("rows", []).append(
                        {"code": c, "name": name, "latest": v["latest"], "pct": v["pct"],
                         "amount": v["amount"], "volume": v["volume"],
                         "open": v["open"], "high": v["high"], "low": v["low"],
                         "preClose": v["preClose"]})
            if row.get("rows"):
                write_jsonl(os.path.join(outdir, "realtime_ticks.jsonl"), row)
                log("tick %s 源=%s n=%d" % (hm, src, len(row["rows"])))
            else:
                fail_streak += 1
                log("取数有响应但无匹配行(源=%s, 池%d只) streak=%d" % (src, len(codes), fail_streak))
        else:
            fail_streak += 1
            log("取数失败 streak=%d" % fail_streak)
            m = now.hour * 60 + now.minute
            if fail_streak >= 30 and (m - last_alarm_min) >= 30:
                last_alarm_min = m
                _alarm("all_source_dead", "连续 %d 轮全源失败(不退出, 保持重试); 近 %d 分钟无 tick" % (fail_streak, fail_streak))
        if SELFTEST:
            log("selftest 完成")
            break
        time.sleep(60)


def main():
    global ALARM_PATH
    d = today()
    outdir = os.path.join(MDIR, "盘中", d)
    os.makedirs(outdir, exist_ok=True)
    ALARM_PATH = os.path.join(outdir, "pipeline_alarm.jsonl")
    codes = load_pool(d)
    log("观察池落档: kind=%s date=%s stale=%s n=%d" % (
        POOL_INFO.get("kind"), POOL_INFO.get("date"), POOL_INFO.get("stale"), len(codes)))
    if not ifind_login():
        log("iFinD 不可用, 仅腾讯降级(竞价轨迹可用但无 Level1 盘口)")
    now = datetime.datetime.now()
    if now.strftime("%H:%M") <= "09:26" or SELFTEST:
        run_auction_phase(codes, outdir, d) if now.strftime("%H:%M") >= "09:15" else None
        if SELFTEST:
            # selftest: 采一轮验证(★20260911: 落真实 rows — 原实现只记 n, 无法证明代码映射/字段解析可用)
            src, data = fetch_batch(codes)
            if data:
                row = {"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "phase": "selftest", "src": src, "n": len(data),
                       "pool_date": POOL_INFO.get("date"), "pool_kind": POOL_INFO.get("kind")}
                for c, name in codes:
                    tc = ths_code(c)
                    v = data.get(tc) or data.get(c) or data.get(str(c).split(".")[0])
                    if v:
                        row.setdefault("rows", []).append(
                            {"code": c, "name": name, "latest": v["latest"], "pct": v["pct"],
                             "amount": v["amount"], "volume": v["volume"],
                             "open": v["open"], "high": v["high"], "low": v["low"],
                             "preClose": v["preClose"]})
                write_jsonl(os.path.join(outdir, "realtime_ticks.jsonl"), row)
                log("selftest OK: 源=%s 请求%d只 落档%d行" % (src, len(codes), len(row.get("rows") or [])))
                if not row.get("rows"):
                    log("selftest FAIL: 有响应但 0 行(代码映射/字段解析问题)")
                    sys.exit(1)
            else:
                log("selftest FAIL: 双源均无数据")
                sys.exit(1)
            sys.exit(0)
    run_continuous_phase(codes, outdir, d)


if __name__ == "__main__":
    main()
