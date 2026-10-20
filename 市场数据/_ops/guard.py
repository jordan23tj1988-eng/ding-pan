# -*- coding: utf-8 -*-
"""复盘系统运维守护：交易日口径 / 失败告警 / 保留策略 / 磁盘水位。

用法:
  python _ops/guard.py check            # 只检查，输出 JSON
  python _ops/guard.py check --send     # 检查并把新告警推到微信
  python _ops/guard.py retain           # 清理 .review_staging（>14 天）
  python _ops/guard.py install-task     # 注册 OS 级兜底任务（需管理员）

设计原则:
- 守护脚本本身不依赖 Hermes gateway；由 Windows 计划任务触发。
- 退出码: 0=守护正常执行完毕（无论是否发现问题）；2=守护自身异常。
  发现的问题写在 JSON 的 issues 里，避免"告警器自己天天红"。
- 告警去重: 同一 (kind, day) 只推一次，状态落 _学习/_运维/alert_state.json。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
STATE = ROOT / "_学习" / "_运维" / "alert_state.json"
CHAIN_JOB = "c4d23047161f"          # sentiment-daily-review
CRON_DB = Path(os.environ.get("LOCALAPPDATA", "")) / "hermes" / "profiles" / "a" / "cron" / "executions.db"
STAGING_KEEP_DAYS = 14
DISK_WARN_PCT = 80


def _read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def trading_days(root: Path = ROOT) -> list[str]:
    cal = _read_json(root / "_学习" / "_交易日历.json", {})
    if isinstance(cal, dict):
        cal = cal.get("days") or cal.get("dates") or []
    return sorted(str(x) for x in cal if re.fullmatch(r"\d{8}", str(x)))


def latest_due_day(now: dt.datetime | None = None, root: Path = ROOT) -> str | None:
    """最近一个"已到交付时点"的交易日：交易日 20:00 后算当天，否则算上一交易日。"""
    now = now or dt.datetime.now()
    days = trading_days(root)
    if not days:
        return None
    today = now.strftime("%Y%m%d")
    if today in days and now.hour >= 20:
        return today
    past = [d for d in days if d < today]
    return past[-1] if past else None


def _release_days(root: Path) -> set[str]:
    out = set()
    for p in (root / "releases").glob("*/manifest.json"):
        m = _read_json(p, {})
        if m.get("published") and m.get("d"):
            out.add(str(m["d"]))
    return out


def _page_model(root: Path, d: str) -> bool:
    return (root / "_学习" / f"总审_{d}.json").is_file() and (root / "复盘" / "盯盘台" / "index.html").is_file()


def check_release(root: Path, d: str) -> list[dict]:
    issues = []
    if d not in _release_days(root):
        issues.append({"kind": "release_missing", "day": d,
                       "detail": f"{d} 无已发布 release"})
    if not (root / "_学习" / f"总审_{d}.json").is_file():
        issues.append({"kind": "master_missing", "day": d,
                       "detail": f"_学习/总审_{d}.json 缺件"})
    if not (root / "_学习" / f"推演_{d}.json").is_file():
        issues.append({"kind": "prediction_missing", "day": d,
                       "detail": f"_学习/推演_{d}.json 缺件"})
    return issues


def _cron_scan(limit: int = 3):
    if not CRON_DB.is_file():
        return [], []
    try:
        con = sqlite3.connect(f"file:{CRON_DB}?mode=ro", uri=True, timeout=5)
        rows = con.execute(
            "select job_id,status,started_at from executions "
            "where started_at >= datetime('now','-30 day') order by started_at desc").fetchall()
        con.close()
        jobs = _read_json(CRON_DB.parent / "jobs.json", {})
        if isinstance(jobs, dict):
            jobs = jobs.get("jobs", [])
        meta = {j.get("id"): j for j in (jobs or [])}
        streaks: dict[str, int] = {}
        last_fail: dict[str, str] = {}
        done: set[str] = set()
        for job_id, status, started_at in rows:
            if job_id in done:
                continue
            if status == "failed":
                streaks[job_id] = streaks.get(job_id, 0) + 1
                last_fail.setdefault(job_id, started_at)
            else:
                # completed/unknown 都视为“本轮链结束”，避免把历史脏状态算成连续失败
                done.add(job_id)
        active, stale = [], []
        for job_id, n in streaks.items():
            job = meta.get(job_id) or {}
            if n < limit or not job.get("enabled"):
                continue
            item = {"job_id": job_id, "consecutive_failures": n, "name": job.get("name")}
            script = job.get("script")
            paths = []
            if script:
                paths = [CRON_DB.parent / "scripts" / script,
                         CRON_DB.parent.parent / "scripts" / script]
                if job.get("workdir"):
                    paths.append(Path(job["workdir"]) / script)
                paths.append(ROOT / script)
            mtimes = [p.stat().st_mtime for p in paths if p.is_file()]
            failed_at = last_fail.get(job_id)
            if mtimes and failed_at:
                try:
                    if max(mtimes) > dt.datetime.fromisoformat(failed_at).timestamp():
                        item["fixed_after_failure"] = True
                        stale.append(item)
                        continue
                except (ValueError, OSError):
                    pass
            active.append(item)
        return sorted(active, key=lambda x: -x["consecutive_failures"]), stale
    except sqlite3.Error:
        return [], []


def _cron_streaks(limit: int = 3) -> list[dict]:
    return _cron_scan(limit)[0]


def disk_usage(path: Path = ROOT) -> dict:
    total, used, free = shutil.disk_usage(str(path))
    return {"total_gb": round(total / 1e9, 1), "used_pct": round(used / total * 100, 1),
            "free_gb": round(free / 1e9, 1)}


def staging_stats(root: Path = ROOT) -> dict:
    """统计 staging 构建数/体积；体积扫描超过 4 秒即截断并标注下界。"""
    import time
    p = root / ".review_staging"
    if not p.is_dir():
        return {"exists": False, "count": 0, "gb": 0.0}
    count = 0
    size = 0
    oldest = None
    truncated = False
    started = time.monotonic()
    for child in p.iterdir():
        count += 1
        try:
            oldest = min(oldest, child.stat().st_mtime) if oldest else child.stat().st_mtime
        except OSError:
            pass
        for dp, _, fs in os.walk(child):
            for f in fs:
                try:
                    size += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass
            if time.monotonic() - started > 4:
                truncated = True
                break
        if truncated:
            break
    return {"exists": True, "count": count, "gb": round(size / 1024 ** 3, 2), "unit": "GiB",
            "size_is_lower_bound": truncated,
            "oldest_days": round((dt.datetime.now().timestamp() - oldest) / 86400, 1) if oldest else None}


def build_report(root: Path = ROOT) -> dict:
    day = latest_due_day(root=root)
    issues = []
    if day:
        issues.extend(check_release(root, day))
    du = disk_usage(root)
    if du["used_pct"] >= DISK_WARN_PCT:
        issues.append({"kind": "disk_pressure", "day": day, "detail": f"磁盘使用 {du['used_pct']}%"})
    st = staging_stats(root)
    if st.get("count", 0) > 200:
        issues.append({"kind": "staging_bloat", "day": day,
                       "detail": f".review_staging {st['count']} 个构建 / {st['gb']}GB"})
    fails, stale_cron = _cron_scan()
    for f in fails:
        issues.append({"kind": "cron_failures", "day": day,
                       "detail": f"{f.get('name') or f['job_id']} 最近连续失败 {f['consecutive_failures']} 次"})
    board = _read_json(root / "_学习" / "_任务看板" / "最新.json", {}) or {}
    critical = int((board.get("counts") or {}).get("critical", 0) or 0)
    if critical > 50:
        issues.append({"kind": "assignments_overdue", "day": day,
                       "detail": f"总审指派逾期(>2天) {critical} 项，看板见 _学习/_任务看板/最新.json"})
    return {"checked_at": dt.datetime.now().isoformat(timespec="seconds"), "day": day,
            "issues": issues, "disk": du, "staging": st, "cron_failures": fails,
            "cron_stale_skipped": stale_cron,
            "assignments": {"critical": critical, "total": board.get("total")}}


def _load_state() -> dict:
    return _read_json(STATE, {}) or {}


def _save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def send_alert(text: str, target: str = "weixin") -> dict:
    """推送告警。注意 hermes send 即使平台拒绝也返回 rc=0，必须检查输出正文。"""
    try:
        p = subprocess.run(["hermes", "send", "-t", target, text], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=60)
        body = ((p.stdout or "") + (p.stderr or "")).strip()
        ok = p.returncode == 0 and "failed" not in body.lower() and "error" not in body.lower()
        return {"ok": ok, "rc": p.returncode, "out": body[-500:]}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": str(exc)}


def _write_alert_file(text: str, report: dict) -> None:
    try:
        d = STATE.parent
        d.mkdir(parents=True, exist_ok=True)
        with (d / "alerts.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": report.get("checked_at"), "text": text}, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[WARN] alert file write failed: {type(exc).__name__}: {exc}", file=sys.stderr)


def notify_new(report: dict, target: str = "weixin", dry_run: bool = False) -> list[dict]:
    state = _load_state()
    sent = []
    for issue in report.get("issues", []):
        key = f"{issue['kind']}|{issue.get('day')}|{issue.get('detail')}"
        if key in state:
            continue
        text = f"[复盘守卫] {issue['kind']} · {issue.get('day')}\n{issue.get('detail')}\n检查时间 {report['checked_at']}"
        res = {"key": key, "sent": False, "delivery": None}
        _write_alert_file(text, report)          # 本地留痕始终写，与通道可用性解耦
        if not dry_run:
            delivery = send_alert(text, target)
            res["delivery"] = delivery
            res["sent"] = bool(delivery.get("ok"))
        sent.append(res)
        if res["sent"]:
            state[key] = report["checked_at"]
    _save_state(state)
    return sent


def retain(root: Path = ROOT, keep_days: int = STAGING_KEEP_DAYS, apply: bool = False) -> dict:
    p = root / ".review_staging"
    if not p.is_dir():
        return {"removed": 0, "kept": 0}
    cutoff = dt.datetime.now().timestamp() - keep_days * 86400
    removed = kept = 0
    removed_gb = 0.0
    for child in p.iterdir():
        if not child.is_dir():
            continue
        try:
            mtime = child.stat().st_mtime
        except OSError:
            continue
        if mtime >= cutoff:
            kept += 1
            continue
        size = 0
        for dp, _, fs in os.walk(child):
            for f in fs:
                try:
                    size += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass
        if apply:
            shutil.rmtree(child, ignore_errors=True)
        removed += 1
        removed_gb += size / 1e9
    return {"removed": removed, "kept": kept, "removed_gb": round(removed_gb, 2), "applied": apply}


def _gateway_alive() -> bool:
    try:
        p = subprocess.run(["hermes", "cron", "status"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        return "Gateway is running" in (p.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return False


def _last_chain_run() -> dt.datetime | None:
    if not CRON_DB.is_file():
        return None
    try:
        con = sqlite3.connect(f"file:{CRON_DB}?mode=ro", uri=True, timeout=5)
        row = con.execute("select started_at from executions where job_id=? "
                          "order by started_at desc limit 1", (CHAIN_JOB,)).fetchone()
        con.close()
        if not row:
            return None
        return dt.datetime.fromisoformat(row[0])
    except (sqlite3.Error, ValueError):
        return None


def repair(report: dict) -> dict:
    """发布缺失时的兜底：确保 gateway 在跑，并触发日复盘作业；同一交易日只触发一次。"""
    if not any(i.get("kind") == "release_missing" for i in report.get("issues", [])):
        return {"fired": False, "reason": "no_missing_release"}
    last = _last_chain_run()
    now = dt.datetime.now(last.tzinfo) if last and last.tzinfo else dt.datetime.now()
    if last and (now - last).total_seconds() < 90 * 60:
        return {"fired": False, "reason": f"chain_ran_recently:{last.isoformat()}"}
    state = _load_state()
    key = f"repair|{report.get('day')}"
    if key in state:
        return {"fired": False, "reason": "already_fired_today"}
    started_gateway = False
    if not _gateway_alive():
        subprocess.run(["hermes", "-p", "default", "gateway", "restart"], capture_output=True,
                       text=True, timeout=180)
        started_gateway = True
        for _ in range(12):
            if _gateway_alive():
                break
            import time
            time.sleep(5)
    p = subprocess.run(["hermes", "cron", "run", CHAIN_JOB], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    ok = p.returncode == 0
    if ok:
        state[key] = report["checked_at"]
        _save_state(state)
    return {"fired": ok, "gateway_restarted": started_gateway,
            "out": ((p.stdout or "") + (p.stderr or ""))[-400:]}


def cmd_check(args) -> int:
    report = build_report()
    if args.repair:
        report["repair"] = repair(report)
    if args.send:
        report["alerts"] = notify_new(report, target=args.target, dry_run=args.dry_run)
    state_path = ROOT / "_学习" / "_运维" / "guard_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


def cmd_retain(args) -> int:
    print(json.dumps(retain(apply=args.apply), ensure_ascii=False))
    return 0


def cmd_install_task(args) -> int:
    bat = ROOT / "_运维" / "review_guard.bat"
    bat.parent.mkdir(parents=True, exist_ok=True)
    py = r"D:\股票数据\.venv312\Scripts\python.exe"
    bat.write_text(
        "@echo off\r\n"
        f'cd /d "{ROOT}"\r\n'
        f'"{py}" _ops\\guard.py check --repair --send >> "_学习\\_运维\\guard.log" 2>&1\r\n',
        encoding="utf-8")
    cmd = (f'schtasks /create /tn "ReviewChainGuard" /tr "{bat}" /sc weekly /d MON,TUE,WED,THU,FRI '
           f'/st 20:45 /f')
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(json.dumps({"bat": str(bat), "rc": p.returncode, "out": (p.stdout or p.stderr)[-500:]},
                     ensure_ascii=False))
    return 0 if p.returncode == 0 else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--send", action="store_true")
    c.add_argument("--repair", action="store_true")
    c.add_argument("--dry-run", action="store_true")
    c.add_argument("--target", default="weixin")
    c.set_defaults(func=cmd_check)
    r = sub.add_parser("retain")
    r.add_argument("--apply", action="store_true")
    r.set_defaults(func=cmd_retain)
    t = sub.add_parser("install-task")
    t.set_defaults(func=cmd_install_task)
    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # 守护自身异常必须显式，不能静默
        print(json.dumps({"status": "guard_error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
