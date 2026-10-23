# -*- coding: utf-8 -*-
"""P1/P2 data capability helpers. Explicit roots, no synthetic market data."""
from __future__ import annotations
import csv, gzip, json, re
from datetime import datetime
from pathlib import Path


def valid_date(d: str) -> str:
    if not isinstance(d, str) or not re.fullmatch(r"\d{8}", d):
        raise ValueError("date must be YYYYMMDD")
    datetime.strptime(d, "%Y%m%d")
    return d


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError):
        return default


def write_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def result(name, d, status, sources=None, metrics=None, errors=None, note=None):
    return {"schema_version": 1, "capability": name, "date": d, "status": status,
            "sources": sources or [], "metrics": metrics or {}, "errors": errors or [],
            "note": note}


def jsonl(path: Path):
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        yield obj
                except ValueError:
                    continue
    except OSError:
        return


def auction_rows(root: Path, d: str):
    """Return (timestamp, row) pairs from only same-day trajectory evidence."""
    csv_path = root / d / "竞价轨迹.csv"
    if csv_path.is_file():
        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    ts = r.get("时刻") or r.get("ts")
                    code = str(r.get("代码") or "").zfill(6)
                    if ts and code:
                        yield str(ts), r
        except (OSError, csv.Error):
            pass
    path = root / "盘中" / d / "auction_traj.jsonl"
    for packet in jsonl(path):
        ts = packet.get("ts") or packet.get("时刻")
        for r in packet.get("rows") or []:
            if ts and isinstance(r, dict) and r.get("code"):
                yield str(ts), r


def continuous_rows(root: Path, d: str):
    path = root / "盘中" / d / "realtime_ticks.jsonl"
    for packet in jsonl(path):
        if packet.get("phase") not in ("continuous", "selftest"):
            continue
        ts = packet.get("ts")
        for r in packet.get("rows") or []:
            if ts and isinstance(r, dict) and r.get("code"):
                yield str(ts), r


def read_mapping(root: Path, d: str):
    obj = load_json(root / "_学习" / f"题材归位_{d}.json", {})
    mapping = obj.get("映射") if isinstance(obj, dict) else None
    return mapping if isinstance(mapping, dict) else {}
