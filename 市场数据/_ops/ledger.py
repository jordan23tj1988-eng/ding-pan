# -*- coding: utf-8 -*-
"""唯一荐票结算账本 + 统计层。

设计要点
- SQLite 单库 `_学习/_ledger/ledger.db`，不再以多份 JSONL 为真源。
- 荐票以 (route, d, code, kind) 为稳定键；payload 变化才升版本，旧版 superseded。
- 结算同样按 rec 版本升版；同值重复 ingest 幂等，不产生重复行。
- 收益口径：T+1 开盘买入、T+1 收盘卖出（与既有“执行收益”一致）。
  拿不到 T+1 行情就记 unsettled + reason，绝不补造。
- R 倍数只在荐票自带事前止损时计算；没有止损则 r=None，并标 r_basis。
- 统计含 bootstrap 95% CI、t 值、期望值(pp)、盈亏比、最大回撤、Brier。

CLI:
  python _ops/ledger.py ingest --since 20260101 [--until 20261231]
  python _ops/ledger.py stats  --since 20260811 [--route theme] [--kind 荐票]
  python _ops/ledger.py verify
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import random
import sqlite3
import statistics
import sys
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
LEARN = ROOT / "_学习"
BARS = LEARN / "_bars_cache"
DB = LEARN / "_ledger" / "ledger.db"
ROUTES = ("limitup", "theme", "logic", "auction", "lhb")
ROUTE_CN = {"limitup": "质量", "theme": "题材", "logic": "逻辑", "auction": "竞价池", "lhb": "龙虎榜"}
ENGINE = "ledger.v1"


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    bad = 0
    first_err = ""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                bad += 1
                if not first_err:
                    first_err = str(exc)
                continue
            if isinstance(item, dict):
                out.append(item)
    if bad:
        print(f"[WARN] read_jsonl {path.name}: 跳过 {bad} 行坏 JSON（首错 {first_err}）", file=sys.stderr)
    return out


def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def bar_rows(code: str) -> list[tuple[str, float, float, float]]:
    path = BARS / (str(code).zfill(6) + ".csv")
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 5:
            continue
        day = parts[0].strip()
        try:
            rows.append((day, float(parts[1]), float(parts[4]), float(parts[3])))
        except ValueError:
            continue
    return rows


def next_bar(code: str, d: str):
    target = f"{d[:4]}-{d[4:6]}-{d[6:]}"
    for day, open_, close, low in bar_rows(code):
        if day > target:
            return day, open_, close, low
    return None


def normalize_kind(raw) -> str:
    """类型字段在多路里被复用为标签；只认明确语义，绝不把观察升成荐票。"""
    text = str(raw or "").strip()
    if not text:
        return "观察"
    if "非荐" in text or "不荐" in text or "观察" in text:
        return "观察"
    if "荐" in text:
        return "荐票"
    return "观察"


def connect(db=None) -> sqlite3.Connection:
    db = Path(db) if db is not None else DB
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS rec(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          key TEXT NOT NULL, route TEXT NOT NULL, d TEXT NOT NULL,
          code TEXT NOT NULL, name TEXT, kind TEXT,
          version INTEGER NOT NULL, is_current INTEGER NOT NULL DEFAULT 1,
          superseded_by INTEGER, payload TEXT NOT NULL, payload_sha TEXT NOT NULL,
          source TEXT, source_sha TEXT, created_at TEXT NOT NULL,
          UNIQUE(key, version));
        CREATE TABLE IF NOT EXISTS settle(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          rec_id INTEGER NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL,
          t1_date TEXT, entry REAL, exit REAL, ret_pct REAL,
          bench_pct REAL, excess_pp REAL, risk_pct REAL, r_multiple REAL,
          r_basis TEXT, reason TEXT, evidence TEXT, engine TEXT,
          computed_at TEXT NOT NULL, is_current INTEGER NOT NULL DEFAULT 1,
          superseded_by INTEGER, UNIQUE(rec_id, version));
        CREATE TABLE IF NOT EXISTS route_day(
          route TEXT NOT NULL, d TEXT NOT NULL, payload TEXT NOT NULL,
          payload_sha TEXT NOT NULL, source TEXT, PRIMARY KEY(route, d));
        CREATE INDEX IF NOT EXISTS ix_rec_current ON rec(route, d, is_current);
        CREATE INDEX IF NOT EXISTS ix_settle_current ON settle(rec_id, is_current);
        """
    )
    return con


def _current_rec(con, key):
    return con.execute("SELECT * FROM rec WHERE key=? AND is_current=1", (key,)).fetchone()


def upsert_rec(con, rec: dict, source: str, source_sha: str) -> tuple[int, bool]:
    key = f"{rec['route']}|{rec['d']}|{rec['code']}|{rec.get('kind') or ''}"
    payload = canon(rec)
    payload_sha = sha(payload)
    cur = _current_rec(con, key)
    if cur:
        if cur["payload_sha"] == payload_sha:
            return cur["id"], False
        new_version = cur["version"] + 1
        cur_id = cur["id"]
    else:
        new_version = 1
        cur_id = None
    with con:
        rid = con.execute(
            "INSERT INTO rec(key,route,d,code,name,kind,version,payload,payload_sha,source,source_sha,created_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (key, rec["route"], rec["d"], rec["code"], rec.get("name"), rec.get("kind"),
             new_version, payload, payload_sha, source, source_sha, now()),
        ).lastrowid
        if cur_id is not None:
            con.execute("UPDATE rec SET is_current=0,superseded_by=? WHERE id=?", (rid, cur_id))
    return rid, cur_id is not None


def upsert_settle(con, rec_id: int, s: dict) -> str:
    cur = con.execute("SELECT * FROM settle WHERE rec_id=? AND is_current=1", (rec_id,)).fetchone()
    identity = (s["status"], s.get("t1_date"), s.get("entry"), s.get("exit"), s.get("ret_pct"),
                s.get("bench_pct"), s.get("excess_pp"), s.get("reason"))
    if cur:
        old = (cur["status"], cur["t1_date"], cur["entry"], cur["exit"], cur["ret_pct"],
               cur["bench_pct"], cur["excess_pp"], cur["reason"])
        same = all((a is None and b is None) or (a == b) or
                   (isinstance(a, float) and isinstance(b, float) and abs(a - b) < 1e-9)
                   for a, b in zip(identity, old))
        if same:
            return "unchanged"
        version = cur["version"] + 1
        with con:
            sid = con.execute(
                "INSERT INTO settle(rec_id,version,status,t1_date,entry,exit,ret_pct,bench_pct,excess_pp,"
                "risk_pct,r_multiple,r_basis,reason,evidence,engine,computed_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec_id, version, s["status"], s.get("t1_date"), s.get("entry"), s.get("exit"),
                 s.get("ret_pct"), s.get("bench_pct"), s.get("excess_pp"), s.get("risk_pct"),
                 s.get("r_multiple"), s.get("r_basis"), s.get("reason"), s.get("evidence"),
                 ENGINE, now()),
            ).lastrowid
            con.execute("UPDATE settle SET is_current=0,superseded_by=? WHERE id=?", (sid, cur["id"]))
        return "superseded"
    with con:
        con.execute(
            "INSERT INTO settle(rec_id,version,status,t1_date,entry,exit,ret_pct,bench_pct,excess_pp,"
            "risk_pct,r_multiple,r_basis,reason,evidence,engine,computed_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rec_id, 1, s["status"], s.get("t1_date"), s.get("entry"), s.get("exit"),
             s.get("ret_pct"), s.get("bench_pct"), s.get("excess_pp"), s.get("risk_pct"),
             s.get("r_multiple"), s.get("r_basis"), s.get("reason"), s.get("evidence"),
             ENGINE, now()),
        )
    return "inserted"


def bench_for(con, route: str, d: str):
    row = con.execute("SELECT payload FROM route_day WHERE route=? AND d=?", (route, d)).fetchone()
    if not row:
        return None
    payload = json.loads(row["payload"])
    summary = payload.get("汇总") if isinstance(payload.get("汇总"), dict) else payload
    for key in ("全场涨停均收", "全场均收", "全场均值"):
        value = to_float(summary.get(key))
        if value is not None:
            return value
    return None


def load_detail_index() -> dict[tuple[str, str, str], dict]:
    """按日结算文件的明细是真源之一：route+d+code -> 明细行。"""
    out = {}
    for route in ROUTES:
        prefix = ROUTE_CN[route]
        for path in sorted(LEARN.glob(f"{prefix}荐票结算_*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            d = str(payload.get("荐票日") or "")
            for item in payload.get("明细") or []:
                code = str(item.get("代码") or "").zfill(6)
                if len(d) == 8 and code.strip("0"):
                    out[(route, d, code)] = item
    return out


def load_route_days(con) -> int:
    count = 0
    for route in ROUTES:
        prefix = ROUTE_CN[route]
        for path in sorted(LEARN.glob(f"{prefix}荐票结算_*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            d = str(payload.get("荐票日") or path.stem.split("_")[-1])
            if len(d) != 8 or not d.isdigit():
                continue
            body = canon(payload)
            with con:
                con.execute(
                    "INSERT INTO route_day(route,d,payload,payload_sha,source) VALUES(?,?,?,?,?)"
                    " ON CONFLICT(route,d) DO UPDATE SET payload=excluded.payload,"
                    " payload_sha=excluded.payload_sha,source=excluded.source",
                    (route, d, body, sha(body), str(path.relative_to(ROOT))),
                )
            count += 1
    return count


def existing_rows() -> dict[tuple[str, str], dict]:
    """已结算 JSONL 按 (route,d,code) 索引；只用于对照，不当作真源。"""
    out = {}
    for row in read_jsonl(LEARN / "_荐票逐票结算.jsonl"):
        d = str(row.get("荐票日") or "")
        code = str(row.get("代码") or "").zfill(6)
        if len(d) == 8 and code.strip("0"):
            out[("limitup", d, code)] = row
    for row in read_jsonl(LEARN / "_龙虎榜荐票结算.jsonl"):
        d = str(row.get("荐票日") or "")
        code = str(row.get("代码") or "").zfill(6)
        if len(d) == 8 and code.strip("0"):
            out[("lhb", d, code)] = row
    return out


def settle_one(rec: dict, existing: dict, details: dict, con) -> dict:
    code, d, route = rec["code"], rec["d"], rec["route"]
    bench = bench_for(con, route, d)
    detail = details.get((route, d, code))
    if detail:
        ret = to_float(detail.get("执行收益"))
        if ret is not None:
            return {"status": "settled", "ret_pct": ret, "bench_pct": bench,
                    "excess_pp": None if bench is None else round(ret - bench, 4),
                    "reason": "按日结算明细", "evidence": f"detail:{route}:{d}:{code}"}
    prior = existing.get((route, d, code))
    if prior:
        ret = to_float(prior.get("执行收益"))
        if ret is not None:
            return {"status": "settled", "ret_pct": ret, "bench_pct": bench,
                    "excess_pp": None if bench is None else round(ret - bench, 4),
                    "reason": "既有逐票结算", "evidence": f"existing:{route}:{d}:{code}"}
    bar = next_bar(code, d)
    if not bar:
        return {"status": "unsettled", "bench_pct": bench,
                "reason": "无 T+1 行情（bars 缺失或尚未到期）", "evidence": f"bars:{code}"}
    t1, open_, close, low = bar
    if not open_:
        return {"status": "unsettled", "t1_date": t1, "bench_pct": bench,
                "reason": "T+1 开盘价缺失", "evidence": f"bars:{code}"}
    ret = (close - open_) / open_ * 100
    risk_pct = None
    r_multiple = None
    r_basis = "no_ex_ante_stop"
    stop = to_float(rec.get("止损") or rec.get("stop_pct"))
    if stop is not None and open_:
        risk_pct = abs(stop)
        if risk_pct > 0:
            r_multiple = round(ret / risk_pct, 4)
            r_basis = "declared_stop"
    return {"status": "settled", "t1_date": t1, "entry": open_, "exit": close,
            "ret_pct": round(ret, 4), "bench_pct": bench,
            "excess_pp": None if bench is None else round(ret - bench, 4),
            "risk_pct": risk_pct, "r_multiple": r_multiple, "r_basis": r_basis,
            "reason": "", "evidence": f"bars:{code}:{t1}"}


def ingest(since: str, until: str) -> dict:
    con = connect()
    days = load_route_days(con)
    existing = existing_rows()
    details = load_detail_index()
    stats = {"recs": 0, "inserted": 0, "superseded": 0, "unchanged": 0,
             "settled": 0, "unsettled": 0, "route_days": days}
    for route in ROUTES:
        for path in sorted(LEARN.glob(f"{route}判断_*.json")):
            d = "".join(ch for ch in path.stem if ch.isdigit())
            if len(d) != 8 or not d.isdigit() or not (since <= d <= until):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            picks = (payload.get("荐票") or {}).get("标的") or []
            try:
                source = str(path.relative_to(ROOT))
            except ValueError:
                source = str(path)
            source_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            seen = set()
            for item in picks:
                code = str(item.get("代码") or "").strip().zfill(6)
                if not code.strip("0"):
                    continue
                kind_raw = str(item.get("类型") or "观察")
                kind = normalize_kind(kind_raw)
                key = (code, kind)
                if key in seen:
                    continue
                seen.add(key)
                rec = {"route": route, "d": d, "code": code, "name": item.get("名称"),
                       "kind": kind, "kind_raw": kind_raw,
                       "tier": item.get("档位") or item.get("档"),
                       "prob": to_float(item.get("预测执1胜率")),
                       "reason": item.get("理由"), "buy_gate": item.get("buy_gate"),
                       "historical": item.get("历史对照")}
                rid, rec_changed = upsert_rec(con, rec, source, source_sha)
                if rec_changed:
                    stats["rec_superseded"] = stats.get("rec_superseded", 0) + 1
                stats["recs"] += 1
                outcome = settle_one(rec, existing, details, con)
                action = upsert_settle(con, rid, outcome)
                stats[action] = stats.get(action, 0) + 1
                stats[outcome["status"]] += 1
    con.close()
    return stats


def bootstrap_ci(values, n=10000, seed=42):
    if len(values) < 2:
        return [None, None]
    rng = random.Random(seed)
    means = []
    for _ in range(n):
        means.append(sum(rng.choice(values) for _ in values) / len(values))
    means.sort()
    return [round(means[int(0.025 * n)], 4), round(means[int(0.975 * n) - 1], 4)]


def stats(since: str, until: str, route=None, kind="荐票") -> dict:
    con = connect()
    where = ["r.is_current=1", "s.is_current=1", "s.status='settled'", "r.d>=?", "r.d<=?"]
    args = [since, until]
    if route:
        where.append("r.route=?")
        args.append(route)
    if kind and kind != "all":
        where.append("r.kind=?")
        args.append(kind)
    rows = con.execute(
        "SELECT r.route,r.d,r.code,r.name,r.kind,r.payload,s.ret_pct,s.bench_pct,s.excess_pp,s.r_multiple "
        "FROM rec r JOIN settle s ON s.rec_id=r.id WHERE " + " AND ".join(where) + " ORDER BY r.d,r.route,r.code",
        args,
    ).fetchall()
    con.close()
    by_route = {}
    for row in rows:
        by_route.setdefault(row["route"], []).append(row)
    out = {"range": [since, until], "route": route or "all", "kind": kind, "n": len(rows), "routes": {}}
    all_ret = [r["ret_pct"] for r in rows]
    for name, group in sorted(by_route.items()):
        rets = [r["ret_pct"] for r in group]
        wins = [x for x in rets if x > 0]
        losses = [x for x in rets if x <= 0]
        mean = statistics.fmean(rets)
        sd = statistics.stdev(rets) if len(rets) > 1 else None
        ci = bootstrap_ci(rets)
        r_vals = [r["r_multiple"] for r in group if r["r_multiple"] is not None]
        probs, outcomes = [], []
        for row in group:
            payload = json.loads(row["payload"])
            prob = to_float(payload.get("prob"))
            if prob is not None:
                probs.append(prob / 100.0)
                outcomes.append(1.0 if row["ret_pct"] > 0 else 0.0)
        brier = None
        if probs:
            brier = round(sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs), 4)
        cum, peak, mdd = 0.0, 0.0, 0.0
        for x in rets:
            cum += x
            peak = max(peak, cum)
            mdd = min(mdd, cum - peak)
        t_stat = mean / (sd / math.sqrt(len(rets))) if sd and len(rets) > 1 else None
        p_value = math.erfc(abs(t_stat) / math.sqrt(2)) if t_stat is not None else None
        out["routes"][name] = {
            "n": len(rets),
            "win_rate": round(len(wins) / len(rets), 4) if rets else None,
            "mean_pct": round(mean, 4),
            "median_pct": round(statistics.median(rets), 4) if rets else None,
            "std_pct": round(sd, 4) if sd is not None else None,
            "ci95_mean": ci,
            "t_stat": round(t_stat, 3) if t_stat is not None else None,
            "p_value": round(p_value, 4) if p_value is not None else None,
            "expectancy_pp": round((len(wins) / len(rets)) * statistics.fmean(wins) +
                                   (len(losses) / len(rets)) * statistics.fmean(losses), 4)
            if wins and losses else None,
            "avg_win_pct": round(statistics.fmean(wins), 4) if wins else None,
            "avg_loss_pct": round(statistics.fmean(losses), 4) if losses else None,
            "profit_factor": round(sum(wins) / abs(sum(losses)), 4) if losses and sum(losses) else None,
            "max_drawdown_pp": round(mdd, 4),
            "mean_excess_pp": round(statistics.fmean([r["excess_pp"] for r in group if r["excess_pp"] is not None]), 4)
            if any(r["excess_pp"] is not None for r in group) else None,
            "n_r": len(r_vals), "mean_r": round(statistics.fmean(r_vals), 4) if r_vals else None,
            "brier": brier, "n_brier": len(probs),
            "cost_sensitivity": {f"{bp}bp": round(mean - bp / 100.0, 4) for bp in (0, 10, 20, 30)},
            "breakeven_cost_bps": round(mean * 100, 2) if mean > 0 else 0.0,
        }
    # Benjamini-Hochberg：跨路多重检验，q 值才算“发现”，单路 p 只作线索。
    tested = [(name, item["p_value"]) for name, item in out["routes"].items() if item.get("p_value") is not None]
    tested.sort(key=lambda x: x[1])
    m = len(tested)
    prev_q = 1.0
    for rank, (name, p) in reversed(list(enumerate(tested, start=1))):
        q = min(prev_q, p * m / rank)
        out["routes"][name]["q_value_bh"] = round(q, 4)
        prev_q = q
    if all_ret:
        out["all"] = {"n": len(all_ret), "mean_pct": round(statistics.fmean(all_ret), 4),
                      "win_rate": round(len([x for x in all_ret if x > 0]) / len(all_ret), 4),
                      "ci95_mean": bootstrap_ci(all_ret)}
    return out


def weekly(week_end: str) -> dict:
    """周统计：只统计当周发行的荐票，T+1 已结算样本；不足 10 笔标 insufficient。"""
    day = dt.date(int(week_end[:4]), int(week_end[4:6]), int(week_end[6:]))
    monday = (day - dt.timedelta(days=day.weekday())).strftime("%Y%m%d")
    out = {"week_end": week_end, "week_start": monday,
           "口径": "荐票口径；T+1开盘买→T+1收盘卖；n<10 不足样本，不参与合格判定",
           "routes": {}}
    for route in ROUTES:
        result = stats(monday, week_end, route=route, kind="荐票")
        item = result["routes"].get(route)
        if not item:
            out["routes"][route] = {"n": 0, "status": "insufficient"}
            continue
        item["status"] = "ok" if item["n"] >= 10 else "insufficient"
        out["routes"][route] = item
    target = LEARN / "_模拟盘" / f"周统计_{week_end}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    out["path"] = str(target)
    return out


def walkforward(since: str, until: str, kind="荐票", min_n=5) -> dict:
    """按月滚动（walk-forward）：每个月都是当月的样本外，不做参数拟合。"""
    con = connect()
    where = ["r.is_current=1", "s.is_current=1", "s.status='settled'", "r.d>=?", "r.d<=?"]
    args = [since, until]
    if kind and kind != "all":
        where.append("r.kind=?"); args.append(kind)
    rows = con.execute(
        "SELECT r.route,r.d,s.ret_pct FROM rec r JOIN settle s ON s.rec_id=r.id WHERE "
        + " AND ".join(where) + " ORDER BY r.d", args).fetchall()
    con.close()
    by = {}
    for row in rows:
        month = row["d"][:6]
        by.setdefault((row["route"], month), []).append(row["ret_pct"])
    folds = {}
    for (route, month), rets in sorted(by.items()):
        folds.setdefault(route, []).append({
            "month": month, "n": len(rets), "mean_pct": round(statistics.fmean(rets), 4),
            "win_rate": round(len([x for x in rets if x > 0]) / len(rets), 4),
            "ci95_mean": bootstrap_ci(rets) if len(rets) >= min_n else None,
        })
    summary = {}
    for route, items in folds.items():
        eligible = [x for x in items if x["n"] >= min_n]
        summary[route] = {
            "folds": len(items), "eligible_folds": len(eligible),
            "positive_folds": sum(1 for x in eligible if x["mean_pct"] > 0),
            "consistency": round(sum(1 for x in eligible if x["mean_pct"] > 0) / len(eligible), 4) if eligible else None,
            "pooled_n": sum(x["n"] for x in items),
        }
    out = {"range": [since, until], "kind": kind, "min_n": min_n,
           "routes": summary, "folds": folds,
           "note": "按月切分，当月样本不参与任何参数选择；consistency=正收益月份占比"}
    target = LEARN / "_ledger" / f"walkforward_{until}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    out["path"] = str(target)
    return out


def verify() -> dict:
    con = connect()
    rec_total = con.execute("SELECT COUNT(*) c FROM rec").fetchone()["c"]
    rec_current = con.execute("SELECT COUNT(*) c FROM rec WHERE is_current=1").fetchone()["c"]
    settle_total = con.execute("SELECT COUNT(*) c FROM settle").fetchone()["c"]
    settle_current = con.execute("SELECT COUNT(*) c FROM settle WHERE is_current=1").fetchone()["c"]
    no_settle = con.execute(
        "SELECT COUNT(*) c FROM rec r WHERE r.is_current=1 AND NOT EXISTS"
        " (SELECT 1 FROM settle s WHERE s.rec_id=r.id AND s.is_current=1)").fetchone()["c"]
    multi = con.execute(
        "SELECT COUNT(*) c FROM (SELECT key,COUNT(*) n FROM rec WHERE is_current=1 GROUP BY key HAVING n>1)"
    ).fetchone()["c"]
    con.close()
    return {"rec_total": rec_total, "rec_current": rec_current, "settle_total": settle_total,
            "settle_current": settle_current, "rec_without_settle": no_settle,
            "duplicate_current_rec": multi}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest"); p.add_argument("--since", default="20260101"); p.add_argument("--until", default="20991231")
    p = sub.add_parser("stats"); p.add_argument("--since", default="20260101"); p.add_argument("--until", default="20991231")
    p.add_argument("--route", choices=ROUTES); p.add_argument("--kind", default="荐票")
    sub.add_parser("verify")
    p = sub.add_parser("weekly"); p.add_argument("--week-end", required=True)
    p = sub.add_parser("walkforward"); p.add_argument("--since", required=True)
    p.add_argument("--until", required=True); p.add_argument("--kind", default="荐票")
    args = ap.parse_args(argv)
    if args.cmd == "ingest":
        result = ingest(args.since, args.until)
    elif args.cmd == "stats":
        result = stats(args.since, args.until, args.route, args.kind)
    elif args.cmd == "weekly":
        result = weekly(args.week_end)
    elif args.cmd == "walkforward":
        result = walkforward(args.since, args.until, args.kind)
    else:
        result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
