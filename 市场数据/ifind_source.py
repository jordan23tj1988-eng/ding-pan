# -*- coding: utf-8 -*-
r"""ifind_source.py — 同花顺iFinD统一数据层(仅宿主运行, 2026-07-18 变更总账#011)
定位: 本机沙箱无外网, iFinDPy 随 iFinD 终端装在 Windows 宿主 —— 本模块只被
     宿主取数脚本 import, 沙箱侧脚本永远只消费其落地产物(bars_cache/csv/json)。
凭据: D:\股票数据\_ifind_auth.json (在 GitHub 镜像范围之外, 勿移入 市场数据\ 内, 勿写进代码)
接口风格: iFinDPy 新API(THS_HQ/THS_RQ/THS_DP 返回THSData.data=DataFrame)优先,
         老API(THS_HistoryQuotes/THS_RealtimeQuotes/THS_DataPool 返回json)回退。
所有函数失败一律返回 None, 由调用方走旧源回退 —— 铁律: iFind 挂了链路不许断。
"""
import os, sys, json, time, datetime

AUTH_PATH = r"D:\股票数据\_ifind_auth.json"
_state = {"logged": False, "mod": None}

def _mod():
    if _state["mod"] is None:
        import iFinDPy
        _state["mod"] = iFinDPy
    return _state["mod"]

def login(verbose=True):
    """登录一次全程复用。成功True; 未装iFinDPy/未填凭据/登录失败 False(打印原因)。"""
    if _state["logged"]:
        return True
    try:
        THS = _mod()
    except Exception as e:
        if verbose: print("[iFind] iFinDPy 未安装或加载失败: %s (到 iFinD安装目录 bin\\ 下运行 installiFinDPy 安装)" % e)
        return False
    try:
        auth = json.load(open(AUTH_PATH, encoding="utf-8"))
        acc = str(auth.get("account", "")).strip(); pwd = str(auth.get("password", "")).strip()
        if (not acc) or ("填" in acc):
            if verbose: print("[iFind] 请先在 %s 填写账号密码" % AUTH_PATH)
            return False
    except Exception as e:
        if verbose: print("[iFind] 凭据文件读取失败: %s" % e)
        return False
    try:
        rc = THS.THS_iFinDLogin(acc, pwd)
    except Exception as e:
        if verbose: print("[iFind] 登录异常: %s" % e)
        return False
    if rc in (0, -201):  # 0=成功 -201=已登录
        _state["logged"] = True
        if verbose: print("[iFind] 登录OK (rc=%s)" % rc)
        return True
    if verbose: print("[iFind] 登录失败 rc=%s (常见: -101账号密码错 / -1010无接口权限)" % rc)
    return False

def ths_code(code6):
    """6位代码 -> iFind后缀码。6/9→SH, 0/3→SZ, 4/8/92→BJ。"""
    c = str(code6).zfill(6)
    if c[0] in "69": return c + ".SH"
    if c[0] in "03": return c + ".SZ"
    return c + ".BJ"

def _by_exchange(codes6):
    """6位码列表 -> [同交易所后缀码列表,...] (SH/SZ/BJ各一组, 保持组内顺序)。"""
    groups = {}
    for c in codes6:
        t = ths_code(c)
        groups.setdefault(t.rsplit(".", 1)[-1], []).append(t)
    return list(groups.values())

def _to_df(obj):
    """THSData/新API对象 或 老API json串/dict -> DataFrame; 失败None。"""
    import pandas as pd
    try:
        if obj is None: return None
        if hasattr(obj, "errorcode"):                      # 新API THSData
            if obj.errorcode != 0: return None
            d = obj.data
            return d if isinstance(d, pd.DataFrame) else pd.DataFrame(d)
        if isinstance(obj, str):
            obj = json.loads(obj)
        if isinstance(obj, dict):                          # 老API dict: tables[n]{thscode,time[],table{}}
            if obj.get("errorcode") not in (0, None): return None
            rows = []
            for t in obj.get("tables") or []:
                tab = t.get("table") or {}
                times = t.get("time") or []
                n = max([len(v) for v in tab.values()] + [len(times)] or [0])
                for i in range(n):
                    row = {"thscode": t.get("thscode")}
                    if times: row["time"] = times[i] if i < len(times) else None
                    for k, v in tab.items():
                        row[k] = v[i] if isinstance(v, list) and i < len(v) else v
                    rows.append(row)
            return pd.DataFrame(rows) if rows else None
        return None
    except Exception:
        return None

def daily_bars(codes6, start, end, fields="open,high,low,close,volume,turnoverRatio", batch=50, sleep=0.3):
    """日K(不复权)。codes6=6位代码列表, start/end='YYYY-MM-DD'。
    返回DataFrame(thscode,time,open,high,low,close,volume,turnoverRatio) 或 None。"""
    import pandas as pd
    if not login(): return None
    THS = _mod(); out = []
    for codes in _by_exchange(codes6):   # ★按交易所分组: 混批会静默丢北交所行(2026-07-18实测)
        for i in range(0, len(codes), batch):
            grp = ",".join(codes[i:i+batch])
            df = None
            try:
                if hasattr(THS, "THS_HQ"):
                    df = _to_df(THS.THS_HQ(grp, fields, "", start, end))
            except Exception: df = None
            if df is None:
                try:
                    df = _to_df(THS.THS_HistoryQuotes(grp, fields, "Interval:D,CPS:0,baseDate:1900-01-01", start, end))
                except Exception: df = None
            if df is not None and len(df): out.append(df)
            if sleep: time.sleep(sleep)
    return pd.concat(out, ignore_index=True) if out else None

def spot(codes6, fields="open,latest,changeRatio,preClose", batch=100, sleep=0.2):
    """实时快照(盘后=当日收盘口径)。返回DataFrame(thscode+fields) 或 None。"""
    import pandas as pd
    if not login(): return None
    THS = _mod(); out = []
    for codes in _by_exchange(codes6):   # ★按交易所分组: 混批会静默丢北交所行(2026-07-18实测)
        for i in range(0, len(codes), batch):
            grp = ",".join(codes[i:i+batch])
            df = None
            try:
                if hasattr(THS, "THS_RQ"):
                    df = _to_df(THS.THS_RQ(grp, fields))
            except Exception: df = None
            if df is None:
                try:
                    df = _to_df(THS.THS_RealtimeQuotes(grp, fields, ""))
                except Exception: df = None
            if df is not None and len(df): out.append(df)
            if sleep: time.sleep(sleep)
    return pd.concat(out, ignore_index=True) if out else None

def all_a_codes(date=None):
    """全部A股清单 -> DataFrame(thscode, security_name) 或 None。板块池id: 001005010=全部A股。"""
    if not login(): return None
    THS = _mod()
    d = date or datetime.date.today().strftime("%Y-%m-%d")
    for call in (
        lambda: THS.THS_DP("block", "%s;001005010" % d, "date:Y,thscode:Y,security_name:Y") if hasattr(THS, "THS_DP") else None,
        lambda: THS.THS_DataPool("block", "%s;001005010" % d, "date:Y,thscode:Y,security_name:Y"),
    ):
        try:
            df = _to_df(call())
            if df is not None and len(df): return df
        except Exception:
            pass
    return None

def concept_index_quotes(date=None):
    """同花顺概念指数(885xxx.TI)当日涨幅榜 -> DataFrame(thscode,名称,涨幅%) 或 None。
    路线: iwencai拉概念指数清单 -> RQ批量取涨跌幅。清单一天取一次即可。"""
    import pandas as pd
    if not login(): return None
    THS = _mod()
    lst = None
    for q, dom in (("同花顺概念指数", "zhishu"), ("概念指数", "zhishu")):
        try:
            lst = _to_df(THS.THS_iwencai(q, dom))
            if lst is not None and len(lst) > 3: break
        except Exception:
            lst = None
    if lst is None or not len(lst): return None
    # ★2026-07-18实测: iwencai返回的thscode列全null,真码在"指数代码" — 选非空占比最高的码列
    cands = [c for c in lst.columns if "code" in str(c).lower() or "代码" in str(c)]
    codecol = max(cands, key=lambda c: lst[c].notna().sum(), default=None) if cands else None
    namecol = next((c for c in lst.columns if "简称" in c or "名称" in c or "name" in c.lower()), None)
    if not codecol: return None
    codes = [str(x) for x in lst[codecol].dropna().tolist() if "TI" in str(x).upper() or str(x)[:3] in ("885", "886")]
    if not codes: return None
    out = []
    for i in range(0, len(codes), 100):
        grp = ",".join(c if "." in c else c + ".TI" for c in codes[i:i+100])
        try:
            df = _to_df(THS.THS_RQ(grp, "latest,changeRatio") if hasattr(THS, "THS_RQ")
                        else THS.THS_RealtimeQuotes(grp, "latest,changeRatio", ""))
            if df is not None and len(df): out.append(df)
        except Exception:
            pass
        time.sleep(0.2)
    if not out: return None
    q = pd.concat(out, ignore_index=True)
    if namecol:
        nm = dict(zip(lst[codecol].astype(str).str.replace(".TI", "", regex=False), lst[namecol]))
        q["名称"] = q["thscode"].astype(str).str.replace(".TI", "", regex=False).map(nm)
    return q

def logout():
    try:
        if _state["logged"]: _mod().THS_iFinDLogout()
    except Exception:
        pass
    _state["logged"] = False
