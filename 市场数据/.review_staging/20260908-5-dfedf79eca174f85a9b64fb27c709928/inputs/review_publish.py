"""Fail-closed release builder. All roots explicit; legacy records are read-only.

build_site receives an isolated root containing frozen inputs, not the live root.
Optional review_pages.input_files(root, d) declares extra relative consumed files.
No legacy page writer or HTTP daemon is invoked here. See IMPLEMENTATION.md.
"""
from __future__ import annotations

import argparse
import ast
import base64
import builtins
import csv
import functools
import html as html_module
import socket
import struct
import stat
import tempfile
import time
import urllib.request
import contextlib
import datetime as dt
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import types
import threading
from urllib.parse import unquote, urlsplit
import uuid

ROUTES = ("index", "cycle", "auction", "lhb", "theme", "logic", "limitup")
REQUIRED_CHECKS = ("cycle", "auction", "lhb", "theme", "limitup", "logic", "consistency", "browser")
SAFE_SENTINELS = ("cycle", "auction", "lhb", "theme", "limitup")
_IMPORT_LOCK = threading.RLock()


def valid_date(d):
    if not isinstance(d, str) or not re.fullmatch(r"[0-9]{8}", d):
        raise ValueError("date must be strict YYYYMMDD")
    dt.datetime.strptime(d, "%Y%m%d")
    return d


def fail(d, errors):
    return {"schema_version": 1, "status": "fail", "errors": [str(x) for x in errors], "d": d}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def contained(base, value):
    """Reject traversal, Windows drives/ADS, symlinks and junction escapes."""
    base = Path(base).resolve()
    raw = str(value).replace("\\", "/")
    p = Path(value)
    if not p.is_absolute():
        if any(part in ("..", "") for part in raw.split("/")) or ":" in raw:
            raise ValueError(f"unsafe path: {value}")
        p = base / p
    resolved = p.resolve()
    if not resolved.is_relative_to(base) or resolved == base:
        raise ValueError(f"path escapes root: {value}")
    cursor = p
    while cursor != base and cursor != cursor.parent:
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            info = None
        if info is not None and (stat.S_ISLNK(info.st_mode) or
                getattr(info, "st_file_attributes", 0) & 0x400):
            # Windows reparse points include junctions, even when their target
            # stays inside root. lstat never traverses the link being checked.
            raise ValueError(f"linked path forbidden: {value}")
        cursor = cursor.parent
    return resolved


def read_json(path):
    def reject(value):
        raise ValueError(f"invalid JSON number {value}")
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=reject)


def write_json(path, value):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        write_json(temp, value)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


@contextlib.contextmanager
def exclusive(root, name=".review_publish.lock"):
    lock = contained(root, name)
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError(f"lock busy: {lock}") from exc
    try:
        yield
    finally:
        lock.rmdir()


@contextlib.contextmanager
def isolated_imports(frozen, source_root):
    """Import declared local dependencies from frozen bytes, without cache leaks."""
    with _IMPORT_LOCK:
        local_names = {p.stem for p in Path(source_root).glob("*.py")}
        local_names.update(p.stem for p in Path(frozen).glob("*.py"))
        saved = {name: sys.modules[name] for name in local_names if name in sys.modules}
        old_path, old_bytecode = sys.path[:], sys.dont_write_bytecode
        try:
            for name in local_names:
                sys.modules.pop(name, None)
            source_root = Path(source_root).resolve()
            publisher_root = Path(__file__).resolve().parent
            sys.path[:] = [str(frozen)] + [entry for entry in old_path
                if Path(entry or os.getcwd()).resolve() not in (source_root, publisher_root)]
            sys.dont_write_bytecode = True
            yield
        finally:
            for name in local_names:
                sys.modules.pop(name, None)
            sys.modules.update(saved)
            sys.path[:] = old_path
            sys.dont_write_bytecode = old_bytecode


def load_module(path):
    # Executing compiled source avoids .pyc writes and stale same-second caches.
    module = types.ModuleType("_review_" + uuid.uuid4().hex)
    module.__file__ = str(path)
    exec(compile(Path(path).read_bytes(), str(path), "exec"), module.__dict__)
    return module


def input_files(root, d):
    # Narrow legacy adapter: only inputs consumed by P0/P1 and audited checks.
    names = {"review_pages.py", f"_学习/judgment_{d}.json", f"_学习/fact_{d}.json"}
    for route in SAFE_SENTINELS:
        names.add(f"{route}数据核对.py")
    for name in ("_市场温度表.json", "_情绪先行指标.json", "_周期投票台账.jsonl",
                 "_竞价池结算.jsonl", "_逻辑荐票结算.jsonl", "_资金温度.json", "_席位分档.json", "_席位分档快照.jsonl", "_题材四维.json"):
        names.add("_学习/" + name)
    for prefix in ("竞价池发出", "竞价池结算", "席位荐票", "题材归位", "涨停对链条",
                   "主流题材6有", "题材生命周期判断", "题材龙头判断", "review_view"):
        names.add(f"_学习/{prefix}_{d}.json")
    names.update({f"{d}/zt_pool.csv", f"{d}/lhb.csv", f"_学习/_席位动向/{d}.csv",
                  f"_学习/席位荐票卡_{d}.html", f"_学习/龙虎榜复盘存档/{d}.json"})
    names.update({"_契约/页面契约.v1.json", f"_学习/页面判断_{d}.json",
                  "复盘一致性哨兵.py", "module_render_limitup.py", "_认知库渲染.py", "trading_calendar.py",
                  "_学习/_交易日历.json", "_学习/_ths_zt_pool.json", "_变更总账.md"})
    names.update({'module_render_'+route+'.py' for route in ROUTES})
    names.add('logic_pool.py')
    names.update('_学习/'+name for name in ('链条纵深库.json',f'中报预增雷达_{d}.json',
        f'竞价评分_{d}.json',f'题材生命周期_{d}.json'))
    names.update(f'_学习/{prefix}_{d}.html' for prefix in ('先行指标灯','周期投票牌','先行指标卡',
        '竞价评分卡','竞价评分库卡','资金温度卡','涨停质量荐票卡','市场温度卡','质量库折叠'))
    for prefix in ("总审", "cycle判断", "auction判断", "lhb判断", "theme判断", "logic判断", "limitup判断",
                   "涨停质量荐票", "先行指标卡", "池外候选卡"):
        names.add(f"_学习/{prefix}_{d}.{'html' if prefix.endswith('卡') else 'json'}")
    for route in ("master", "auction", "lhb", "theme", "logic", "limitup"):
        names.update({f"_学习/_模拟盘/{route}/{name}" for name in ("状态.json", "state.json", "净值.json", "账本.jsonl", f"看板_{d}.html")})
        names.add(f"_学习/交易计划_{route}_{d}.json")
    names.update(f"复盘/盯盘台/{name}.html" for name in ("intraday", "history"))
    for folder in ("archive",):
        base = root / "复盘" / "盯盘台" / folder
        if base.exists():
            names.update(p.relative_to(root).as_posix() for p in base.rglob("*") if p.is_file())
    names.add(f'_external/candidates/candidates_{d}.json')
    # C4 reads every recommendation; C8 audits registration of all root scripts/specs.
    for pattern in ('*.py','_agent规格/*.md',f'_学习/*荐票_{d}.json'):
        names.update(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())
    names.update(('_多agent重构_设计规范.md','_盯盘台组件规范.md','_模拟盘设计.md','_链路地图.md'))
    for path in (root/'_学习').glob('链条位置_*_????????.json'):
        date=path.stem.rsplit('_',1)[-1]
        if re.fullmatch(r'[0-9]{8}',date) and date<=d:names.add(path.relative_to(root).as_posix())
    prior = sorted(p.name for p in root.iterdir() if p.is_dir() and re.fullmatch(r"[0-9]{8}",p.name) and p.name < d)
    if prior:
        previous = prior[-1]
        names.add(f"{previous}/zt_pool.csv")
        names.update(f"_学习/{prefix}_{previous}.json" for prefix in ("质量荐票结算","题材荐票结算","逻辑荐票结算","席位荐票结算"))
    extra_bars = root / "_学习" / "_模拟盘" / "_bars_extra"
    if extra_bars.exists():
        names.update(p.relative_to(root).as_posix() for p in extra_bars.glob("*.csv") if p.is_file())
    cache = root / "_学习" / "_bars_cache"
    if cache.exists():
        # C3 enumerates the cache; C4 reads exact dates. Freeze its actual inputs.
        names.update(p.relative_to(root).as_posix() for p in cache.glob("*.csv"))
    structured = root / "_学习" / f"页面判断_{d}.json"
    if structured.exists():
        for evidence in read_json(structured).get("evidence", []):
            name = evidence.get("source", "").split("#",1)[0]
            if name:
                names.add(name if "/" in name else "_学习/"+name)
    builder = contained(root, "review_pages.py")
    if builder.is_file():
        with isolated_imports(root, root):
            m = load_module(builder)
            extra = m.input_files(root, d) if hasattr(m, "input_files") else None
        if extra is not None:
            if not isinstance(extra, (list, tuple)) or not all(isinstance(x, str) for x in extra):
                raise ValueError("input_files must return relative path strings")
            for name in extra:
                if Path(name).is_absolute():
                    raise ValueError("input_files must be relative")
                contained(root, name)
                if any(token > d for token in re.findall(r"(?<![0-9])[0-9]{8}(?![0-9])", name)):
                    raise ValueError(f"future input: {name}")
                names.add(name)
    return sorted(names)


def hashes(root, names):
    result = {}
    for name in names:
        path = contained(root, name)
        if path.exists() and not path.is_file():
            raise ValueError(f"input is not a file: {name}")
        result[name] = digest(path) if path.is_file() else None
    return result


def validate_inputs(frozen, d):
    errors = []
    try:
        if (frozen / "_学习" / f"页面判断_{d}.json").exists():
            return validate_structured_input(frozen,d)
        j = read_json(frozen / "_学习" / f"judgment_{d}.json")
        if not isinstance(j, dict):
            return ["judgment must be object"]
        # Legacy date is explicitly supported without rewriting its schema.
        if j.get("date", j.get("d")) != d:
            errors.append("judgment date mismatch")
        if "schema_version" in j and (type(j["schema_version"]) is not int or j["schema_version"] != 1):
            errors.append("judgment schema_version unsupported")
        bodies = j.get("bodies")
        if not isinstance(bodies, dict):
            return errors + ["judgment bodies must be object"]
        for route in ROUTES:
            if not isinstance(bodies.get(route), str) or not bodies[route].strip():
                errors.append(f"missing or invalid body: {route}")
        fact = frozen / "_学习" / f"fact_{d}.json"
        if fact.exists():
            f = read_json(fact)
            if not isinstance(f, dict) or f.get("d", f.get("date")) != d:
                errors.append("fact date mismatch")
            elif "schema_version" in f and (type(f["schema_version"]) is not int or f["schema_version"] != 1):
                errors.append("fact schema_version unsupported")
        if not (frozen / "_契约" / "页面契约.v1.json").exists():
            # Whole historical sources must be supplied as an as-of snapshot.
            # Reject future rows rather than rewriting a frozen source or silently
            # allowing a legacy consumer to select a later row.
            for name in ("_市场温度表.json", "_情绪先行指标.json", "_题材四维.json"):
                path = frozen / "_学习" / name
                if path.exists():
                    table = read_json(path)
                    if not isinstance(table, dict):
                        errors.append(f"input table invalid: {name}")
                    elif any(re.fullmatch(r"[0-9]{8}", str(k)) and str(k) > d for k in table):
                        errors.append(f"future dated input rows: {name}")
            path = frozen / "_学习" / "_资金温度.json"
            if path.exists():
                rows = read_json(path)
                if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
                    errors.append("fund temperature rows invalid")
                elif any(str(r.get("日", "")) > d for r in rows):
                    errors.append("future dated input rows: _资金温度.json")
            path = frozen / "_学习" / "_席位分档.json"
            if path.exists():
                window = read_json(path).get("窗口", "")
                if any(value > d for value in re.findall(r"[0-9]{8}", window)):
                    errors.append("future dated input window: _席位分档.json")
            for name, key in (("_周期投票台账.jsonl", "d"), ("_竞价池结算.jsonl", "池日")):
                path = frozen / "_学习" / name
                if path.exists():
                    for line in path.read_text(encoding="utf-8-sig").splitlines():
                        if line.strip():
                            row = json.loads(line)
                            if str(row.get(key, "")) > d:
                                errors.append(f"future dated input rows: {name}")
                                break
        # No stale temperature fallback may certify an absent current row.
        tpath = frozen / "_学习" / "_市场温度表.json"
        if tpath.exists() and d not in read_json(tpath):
            errors.append("temperature missing exact date")
    except Exception as exc:
        errors.append(f"input invalid: {exc}")
    return errors


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = set()
        self.dates = []
        self.schemas = []
        self.body = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "body":
            self.body = True
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "html":
            if "data-d" in a:
                self.dates.append(a["data-d"])
            if "data-schema-version" in a:
                self.schemas.append(a["data-schema-version"])
        if tag == "meta":
            if a.get("name") in ("review-date", "d"):
                self.dates.append(a.get("content"))
            if a.get("name") in ("review-schema-version", "schema_version"):
                self.schemas.append(a.get("content"))
        for attr in ("href", "src", "poster"):
            if a.get(attr):
                self.refs.append(a[attr])


def validate_references(stage):
    errors = []
    parsed = {}
    for p in stage.rglob("*.html"):
        h = Page()
        h.feed(p.read_text(encoding="utf-8"))
        parsed[p.resolve()] = h
    for p, h in parsed.items():
        for ref in h.refs:
            u = urlsplit(ref)
            if u.scheme in ("https", "http", "mailto", "tel", "data") or u.netloc:
                continue
            if u.scheme:
                errors.append(f"reference forbidden scheme: {p.name}: {ref}")
                continue
            try:
                target = p if not u.path else contained(stage, p.parent / unquote(u.path))
                if not target.is_file():
                    errors.append(f"reference missing: {p.name}: {ref}")
                elif u.fragment and target in parsed and unquote(u.fragment) not in parsed[target].ids:
                    errors.append(f"reference anchor missing: {p.name}: {ref}")
            except Exception as exc:
                errors.append(f"reference invalid: {p.name}: {ref}: {exc}")
    return errors


def validate_pages(stage, result, d):
    errors = []
    if not isinstance(result, dict):
        return ["P1 result must be object"]
    if "schema_version" in result and (type(result["schema_version"]) is not int or result["schema_version"] != 1):
        errors.append("P1 schema_version unsupported")
    if result.get("d") != d:
        errors.append("P1 date mismatch")
    expected_version = result.get("contract_snapshot",{}).get("template_version","1")
    if result.get("template_version") != expected_version:
        errors.append("P1 template_version unsupported")
    if result.get("status") not in ("pass", "degraded", "fail"):
        errors.append("P1 status invalid")
    if result.get("status") == "fail":
        errors.append("P1 reported fail")
    if not isinstance(result.get("errors"), list):
        errors.append("P1 errors field invalid")
    else:
        errors.extend(str(e) for e in result["errors"])
    pages = result.get("pages")
    if not isinstance(pages, list):
        return errors + ["P1 pages must be list"]
    seen = set()
    for entry in pages:
        if not isinstance(entry, dict):
            errors.append("page record invalid")
            continue
        route = entry.get("route")
        if route not in ROUTES or route in seen:
            errors.append(f"page route invalid or duplicate: {route}")
            continue
        seen.add(route)
        if entry.get("status") != "pass" or entry.get("errors") != []:
            errors.append(f"page {route}: status={entry.get('status')} errors={entry.get('errors')}")
        try:
            path = contained(stage, entry["path"])
            if path != (stage / f"{route}.html").resolve():
                raise ValueError("route path mismatch")
            h = Page()
            raw = path.read_text(encoding="utf-8")
            h.feed(raw)
            if result.get("contract") == "p1.1":
                model = read_json(stage / "models" / f"{route}.json")
                if model.get("d") == d and model.get("schema_version") == 1 and model.get("template_version") == expected_version:
                    # Current p1.1 stores schema in a linked model and date in kick.
                    if re.search(r'class="kick"[^>]*>[^<]*'+d, raw):
                        h.dates.append(d);h.schemas.append("1")
            if not h.body:
                errors.append(f"page {route}: no body element")
            # New P1 metadata is checked independently, never trusted via PASS.
            if not h.dates or any(value != d for value in h.dates):
                errors.append(f"page {route}: date metadata missing/mismatch")
            if not h.schemas or any(value != "1" for value in h.schemas):
                errors.append(f"page {route}: schema metadata missing/mismatch")
        except Exception as exc:
            errors.append(f"page {route}: {exc}")
    for route in set(ROUTES) - seen:
        errors.append(f"page missing: {route}")
    for route in ROUTES:
        if not (stage / f"{route}.html").is_file():
            errors.append(f"page file missing: {route}")
    auxiliary = {}
    for asset in result.get("auxiliary_assets",[]):
        path = contained(stage, asset["path"])
        if asset.get("kind") not in ("preserved","p1_history") or not path.is_file() or digest(path)!=asset.get("sha256"):
            errors.append("auxiliary asset invalid: "+str(asset.get("path")))
        auxiliary[asset["path"]] = asset
    for p in stage.rglob("*.html"):
        if p.relative_to(stage).as_posix() not in {r + ".html" for r in ROUTES} | set(auxiliary):
            errors.append(f"unreported HTML page: {p.relative_to(stage)}")
    errors.extend(validate_references(stage))
    return errors


def previous_pool_check(root,stage,d):
    """C9/P1 contract: previous trading pool, settled on d, never d+1 outcome."""
    result={'status':'fail','errors':[],'pool_date':None}
    try:
        previous=sorted(p.name for p in root.iterdir() if p.is_dir() and re.fullmatch(r'[0-9]{8}',p.name) and p.name<d)[-1]
        source=root/'_学习'/'_竞价池结算.jsonl'
        rows=[json.loads(line) for line in source.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        selected=[row for row in rows if row.get('池日')==previous]
        if not selected:raise ValueError('previous pool settlement missing')
        row=selected[-1]
        dom=_DOM((stage/'auction.html').read_text(encoding='utf-8'))
        node=dom.ids.get('component-POOLLEDGER')
        if node is None:raise ValueError('POOLLEDGER component missing')
        def summaries(n):
            for part in n['parts']:
                if isinstance(part,dict):
                    if part['tag']=='summary':yield part
                    else:yield from summaries(part)
        latest=next(summaries(node),None)
        if latest is None:raise ValueError('latest settlement summary missing')
        text=''.join(''.join(latest['text']).split())
        expected={key:row.get(key) for key in ('次日封板','执行胜率','执行均收')}
        if any(v is None for v in expected.values()):raise ValueError('settlement source has null values')
        # Assert both the date/denominator context and each source value in the
        # named component, not an unrelated audit or KPI elsewhere in the page.
        prefixes={'次日封板':'封板','执行胜率':'胜率','执行均收':'均收'}
        matched={key:(prefixes[key]+str(value) in text) for key,value in expected.items()}
        date_ok=text.startswith(previous[4:6]+'-'+previous[6:]+'池终结算')
        if not date_ok or not all(matched.values()):result['errors'].append('dated previous pool settlement mismatch')
        result.update(pool_date=previous,expected=expected,matched=matched,source_sha256=digest(source),date_matches=date_ok)
        result['status']='fail' if result['errors'] else 'pass'
    except Exception as exc:result['errors'].append(str(exc))
    return result


def seat_snapshot(root,d):
    path=root/'_学习/_席位分档快照.jsonl'
    if not path.exists():return None
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    selected=[row for row in rows if row.get('日')==d]
    if not selected:return None
    if any(row!=selected[-1] for row in selected):raise ValueError('conflicting dated seat snapshots')
    return selected[-1]


def scoped_p12_check(root,stage,d,route,*,raw=None):
    """P1.2 gate repair contract: actual producer data in its fixed section.

    Independent of complete/ok claims; legacy financial checks still execute.
    Does not grant permission to publish a page with missing judgments.
    """
    errors=[];dimensions=[]
    try:
        contract=page_contract(root)
        model=read_json(stage/'models'/(route+'.json'))
        if contract.get('template_version')!='p1.2' or model.get('template_version')!='p1.2' or model.get('d')!=d or model.get('route')!=route:
            raise ValueError('unsupported scoped template/date/route')
        raw=(stage/(route+'.html')).read_text(encoding='utf-8') if raw is None else raw
        dom=_DOM(raw)
        sections=contract['routes'][route]['sections']
        expected=[n+' '+sec['title'] for n,sec in zip('一二三四五六七',sections)]
        if [''.join(n['text']).strip() for n in dom.headings]!=expected:errors.append('ordered sections mismatch')
        if dom.duplicates:errors.append('duplicate IDs')
        if len(dom.kpis)!=4:errors.append('four KPI slots required')
        for sec in sections:
            node=dom.ids.get(sec['id'])
            if node is None or node['tag']!='section':errors.append('missing section '+sec['id'])
        dimensions.append('fixed complete sections, four KPI slots, unique IDs')
        required={'cycle':{'VOLSTEP':'volume','LEADIND':'leading','VOTEBOARD':'stages','LADDER':'ladder'},
                  'auction':{'POOLLEDGER':'settlement'},'lhb':{'SEATLIB':'tiers'}}[route]
        components={c['id']:c for c in model.get('components',[])}
        cycle_body = ''
        if route == 'cycle':
            judgment = contained(root, '_学习') / ('judgment_' + d + '.json')
            if judgment.exists():
                cycle_body = read_json(judgment).get('bodies', {}).get('cycle', '') or ''
        cycle_body_mode = route == 'cycle' and bool(cycle_body and '<h2>一' in cycle_body)
        if cycle_body_mode:
            # Body days follow the golden shape: no machine components,
            # no machine fold, and no machine anchors.  The legacy sentinel
            # still runs below and independently checks the same absence.
            for key in ('VOLSTEP','LEADIND','VOTEBOARD','LADDER'):
                if key in components:
                    errors.append('body-day must omit machine component '+key)
            if 'details class="chain"' in raw:
                # The page-level audit fold is allowed; only a machine fold is
                # forbidden.  A machine fold has the explicit source summary.
                if re.search(r'<details[^>]*class="chain"[^>]*>\s*<summary>\s*<b>机器数据源', raw):
                    errors.append('body-day must omit machine fold')
            dimensions.append('cycle body-day golden shape: machine components/fold/anchors absent')
            required = {}
        for key,section in required.items():
            comp=components.get(key);node=dom.ids.get('component-'+key)
            if not comp or comp.get('status')!='ok' or not comp.get('sources') or node is None:errors.append('missing component '+key);continue
            if comp.get('section')!=section or not any(n['tag']=='section' and n['attrs'].get('id')==section for n in node['ancestors']):errors.append('wrong component section '+key)
            if any(n['tag']=='details' for n in node['ancestors']):errors.append('extra machine fold '+key)
            for source in comp.get('sources',[]):
                if digest(contained(root,source['path']))!=source['sha256']:errors.append('source hash '+key)
            rendered=canonical_text(expanded_dom_text(node,dom))
            if key=='SEATLIB':
                row=seat_snapshot(root,d)
                if not row:raise ValueError('missing dated seat snapshot')
                window=row.get('窗口','');counts=row.get('档分布',{})
                bounds=window.split('~')
                if len(bounds)!=2:raise ValueError('invalid snapshot window')
                for bound in bounds:valid_date(bound)
                if not bounds[0]<=bounds[1]<=d:raise ValueError('future snapshot window')
                if type(row.get('笔数')) is not int or any(type(counts.get(k)) is not int or counts[k]<0 for k in 'SABCP'):raise ValueError('missing snapshot counts')
                expected_window='窗口'+window+str(row['笔数'])+'笔'
                expected_counts='/'.join((k if k!='P' else '预备')+str(counts[k]) for k in 'SABCP')
                if expected_window not in rendered:errors.append('dated seat window/count mismatch')
                if expected_counts not in rendered:errors.append('dated seat tier counts mismatch')
                if comp.get('window_id')!=window or comp.get('as_of')!=d:errors.append('seat as-of mismatch')
                if '_学习/_席位分档快照.jsonl' not in {v['path'] for v in comp['sources']}:errors.append('missing snapshot provenance')
            else:
                original=component_source_text(root,d,route,comp)
                strip=lambda text:re.sub(r'更早存档[0-9]+条','',text)
                actual=strip(rendered);source=strip(original)
                if actual!=source:
                    prefix=source[:-len(actual)] if actual and source.endswith(actual) else None
                    if key!='POOLLEDGER' or prefix is None or prefix not in canonical_text(raw):errors.append('producer content mismatch '+key)
                anchors={'VOLSTEP':['VOLSTEP'],'LEADIND':['LEADIND'],'VOTEBOARD':['MACHVOTE','VOTEBOARD'],'LADDER':['LADDER'],'POOLLEDGER':['POOLLEDGER','MACHPOOL']}[key]
                # Check anchor placement in the exact named section as well as totals.
                start=raw.find('<section id="'+section+'">');end=raw.find('</section>',start)
                part=raw[start:end]
                for anchor in anchors:
                    for token in ('<!--'+anchor+'-->','<!--/'+anchor+'-->'):
                        if raw.count(token)!=1 or part.count(token)!=1:errors.append('anchor pair/placement '+anchor)
        dimensions.append('dated source hashes, producer content, exact component positions and anchors')
    except Exception as exc:errors.append(str(exc))
    return {'status':'fail' if errors else 'pass','errors':errors,'contract':'gate-repair/p1.2-v1','dimensions':dimensions}


def _check_one(frozen, stage, d, route):
    """Child process: audited read-only legacy main, explicit isolated --page."""
    if route not in SAFE_SENTINELS:
        raise ValueError("unaudited check")
    if route == "limitup":
        with isolated_imports(frozen, frozen):
            dep = load_module(frozen / "module_render_limitup.py")
        dep.BASE = dep.CD = str(frozen)
        dep.L = str(frozen / "_学习")
        sys.modules["module_render_limitup"] = dep
    module = load_module(frozen / f"{route}数据核对.py")
    module.R = str(frozen)
    module.BASE = str(frozen)
    module.L = str(frozen / "_学习")
    module.SITE = str(stage)
    sys.argv = [module.__file__, d, "--page", str(stage / f"{route}.html")]
    view = None
    replacement_labels = set()
    active_html = ['']
    if route == 'cycle' and (stage/'models'/'cycle.json').is_file():
        contract = page_contract(frozen)
        if contract.get('template_version') == 'p1.1':
            view = view_check(frozen,stage,d,route)
            replacement_labels = {'机器锚'+a+'应缺席(有body黄金版形态)' for a in ('VOLSTEP','LEADIND','LADDER','MACHVOTE')}
            replacement_labels.add('无机器折叠区(黄金版形态)')
            original_check_page = module.check_page
            def checked_page(h,day):
                active_html[0]=h
                return original_check_page(h,day)
            module.check_page=checked_page
    bindings = []
    if route in ('lhb','limitup') and (stage/'models'/(route+'.json')).is_file():
        if page_contract(frozen).get('template_version') == 'p1.1':
            view=view_check(frozen,stage,d,route)
            active_html[0]=(stage/(route+'.html')).read_text(encoding='utf-8')
            if route=='limitup':
                find_block=module.find_block
                def contract_block(h,start,end,start_from=0):
                    if (start,end)==('一 涨停复盘','<h2>二'):
                        bindings.append({'legacy_section':start,'p1_section':'recommendations','assertions':'unchanged Top5 name/rate against dated source'})
                        opening='<section id="recommendations">'
                        i=h.find(opening)
                        j=h.find('<section id=',i+len(opening)) if i>=0 else -1
                        return (h[i:j if j>=0 else len(h)] if i>=0 and view['status']=='pass' else None),i
                    return find_block(h,start,end,start_from)
                module.find_block=contract_block
    settlement=None
    if route=='auction' and (stage/'models'/'auction.json').is_file():
        if page_contract(frozen).get('template_version')=='p1.1':
            view=view_check(frozen,stage,d,route)
            settlement=previous_pool_check(frozen,stage,d)
    scoped=None
    if route in ('cycle','auction','lhb') and (stage/'models'/(route+'.json')).is_file() and page_contract(frozen).get('template_version')=='p1.2':
        scoped=scoped_p12_check(frozen,stage,d,route)
        if route=='cycle':
            original_check_page=module.check_page
            def checked_p12(h,day):
                active_html[0]=h
                return original_check_page(h,day)
            module.check_page=checked_p12
            replacement_labels={'机器锚'+a+'应缺席(有body黄金版形态)' for a in ('VOLSTEP','LEADIND','LADDER','MACHVOTE')}
            replacement_labels.add('无机器折叠区(黄金版形态)')
        if route=='auction':settlement=previous_pool_check(frozen,stage,d)
    # Capturing every actual chk call exposes empty or skipped check runs.
    rows = []
    first_issues = []
    original = module.chk
    def record(issues, ok, label, detail=""):
        if not first_issues:
            first_issues.append(issues)
        row = {"ok": bool(ok), "label": label, "detail": str(detail), "negative_injection": issues is not first_issues[0]}
        if scoped is not None and label in replacement_labels:
            validation=scoped_p12_check(frozen,stage,d,route,raw=active_html[0])
            ok=validation['status']=='pass'
            row.update(legacy_ok=row['ok'],ok=ok,replacement_contract=validation['contract'],errors=validation['errors'])
        elif label in replacement_labels:
            # Explicit dual contract: old absent anchors -> source-verified P1.1
            # components, unique paired anchors and named sections. No content
            # assertion is replaced; each injected check uses its own HTML.
            h=active_html[0]
            anchors=('VOLSTEP','LEADIND','LADDER','MACHVOTE','VOTEBOARD')
            ok=view['status']=='pass' and all(h.count('<!--'+a+'-->')==1 and h.count('<!--/'+a+'-->')==1 for a in anchors)
            row.update(legacy_ok=row['ok'],ok=bool(ok),replacement_contract='p1.1: source-verified components and exactly paired anchors')
        if route=='lhb' and view is not None and label=='Top5卡在页面':
            # Sanitization may change harmless tags/attributes. The entire card
            # text must still occupy its named component, with frozen provenance.
            dom=_DOM(active_html[0]);node=dom.ids.get('component-SEATCARD')
            card=(frozen/'_学习'/f'席位荐票卡_{d}.html').read_text(encoding='utf-8-sig')
            ok=view['status']=='pass' and node is not None and canonical_text(card)==''.join(''.join(node['text']).split())
            row.update(legacy_ok=row['ok'],ok=bool(ok),replacement_contract='p1.1: exact normalized source card in component-SEATCARD')
        if settlement is not None and (label.startswith('结算·') or label=='结算(未到结算日)'):
            ok=settlement['status']=='pass'
            row.update(legacy_ok=row['ok'],ok=bool(ok),replacement_contract=('gate-repair/p1.2-v1' if scoped is not None else 'p1.1')+'/C9: previous trading pool settled on d',pool_date=settlement['pool_date'])
        if scoped is not None and route=='cycle' and label=='断档卡存在':
            gap=read_json(stage/'models/cycle.json')
            cp=frozen/'_学习'/f'cycle判断_{d}.json'; jp=frozen/'_学习'/f'judgment_{d}.json'
            source_absent=not (cp.exists() and read_json(cp)) and not (jp.exists() and read_json(jp).get('bodies',{}).get('cycle'))
            ok=scoped['status']=='pass' and gap.get('judgment_complete') is False and source_absent and gap.get('hero',{}).get('text')=='当日判断缺失' and '当日判断缺失' in active_html[0] and '当日周期判断缺失' in active_html[0]
            row.update(legacy_ok=row['ok'],ok=ok,replacement_contract=scoped['contract']+'/explicit missing judgment')
        if scoped is not None and route=='lhb' and label.startswith(('分档库','分档表新鲜度')):
            ok=scoped['status']=='pass'
            row.update(legacy_ok=row['ok'],ok=ok,replacement_contract=scoped['contract'],errors=scoped['errors'])
        rows.append(row)
        return original(issues, ok, label, detail)
    module.chk = record
    log = io.StringIO()
    with readonly_files(frozen,stage) as (reads,denied), contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        code = module.main()
    # cycle/auction main also execute negative self-tests; their deliberate FAIL
    # rows are not a production failure when main itself returns zero.
    baseline_ok = bool(rows) and all(r["ok"] for r in rows if not r["negative_injection"])
    passed = code == 0 and baseline_ok and (scoped is None or scoped['status']=='pass') and not denied and (view is None or view["status"] == "pass") and (settlement is None or settlement["status"] == "pass")
    return {"name": route, "status": "pass" if passed else "fail",
            "errors": [] if passed else [f"sentinel exit={code}, baseline_ok={baseline_ok}, checks={len(rows)}"] + ((view or {}).get("errors",[])) + ((settlement or {}).get("errors",[])) + ((scoped or {}).get("errors",[])),
            "scoped_validation": scoped, "exit_code": code, "log": log.getvalue(), "view_verification": view, "section_bindings": bindings, "settlement_validation": settlement, "observed_checks": rows, "read_files": sorted(reads), "denied_operations": denied}


def run_checks(frozen, stage, d):
    results = []
    for route in REQUIRED_CHECKS:
        try:
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "_check", d,
                                "--root", str(frozen), "--stage", str(stage), "--route", route],
                               cwd=frozen, env=env, capture_output=True, text=True, encoding="utf-8", timeout=180)
            row = json.loads(r.stdout)
            if r.returncode != 0:
                row["status"] = "fail"
                row.setdefault("errors", []).append(f"check process exit={r.returncode}")
            results.append(row)
        except Exception as exc:
            results.append({"name": route, "status": "fail", "errors": [str(exc)]})
    return results


def check_errors(checks):
    errors = []
    if not isinstance(checks, list):
        return ["checks must be list"]
    seen = set()
    for check in checks:
        if not isinstance(check, dict):
            errors.append("check record invalid")
            continue
        name = check.get("name")
        if not isinstance(name, str) or name in seen:
            errors.append("check name invalid/duplicate")
            continue
        seen.add(name)
        if check.get("status") != "pass" or check.get("errors") != []:
            errors.append(f"check {name}: {check.get('status')} {check.get('errors')}")
    errors.extend(f"check {name}: not_run" for name in REQUIRED_CHECKS if name not in seen)
    return errors


def tree_hashes(directory):
    result = {}
    for p in sorted(directory.rglob("*")):
        contained(directory, p)
        if p.is_file():
            result[p.relative_to(directory).as_posix()] = digest(p)
    return result


def _build(root, d, publish, allow_degraded):
    staging = contained(root, ".review_staging")
    releases = contained(root, "releases")
    staging.mkdir(exist_ok=True)
    releases.mkdir(exist_ok=True)
    revision = 1 + max([int(p.name.split("-")[1]) for p in releases.iterdir()
                        if re.fullmatch(d + r"-[0-9]+-[0-9a-f]{32}", p.name)] or [0])
    build_id = f"{d}-{revision}-{uuid.uuid4().hex}"
    work = staging / build_id
    work.mkdir()
    frozen = work / "inputs"
    frozen.mkdir()
    stage = work / "site"
    stage.mkdir()
    manifest = {"schema_version": 1, "d": d, "build_id": build_id, "revision": revision,
                "source_hashes": {}, "template_version": None, "page_hashes": {},
                "checks": [{"name": n, "status": "not_run", "errors": ["build has not reached checks"]} for n in REQUIRED_CHECKS],
                "status": "fail", "errors": [], "published": False,
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    errors = manifest["errors"]
    try:
        names = input_files(root, d)
        before = hashes(root, names)
        manifest["source_hashes"] = before
        manifest["publisher_sha256"] = digest(Path(__file__))
        for name, sha in before.items():
            if sha is None:
                continue
            target = contained(frozen, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(contained(root, name), target)
        if hashes(frozen, names) != before or hashes(root, names) != before:
            raise ValueError("source changed while freezing")
        errors.extend(validate_inputs(frozen, d))
        result = None
        # Render even invalid/missing body input to retain an honest failed preview.
        try:
            with isolated_imports(frozen, root):
                # These pure dependencies must bind before legacy renderers insert
                # their historical production path into sys.path.
                for dependency in ('logic_pool','_认知库渲染'):
                    path=frozen/(dependency+'.py')
                    if path.exists():sys.modules[dependency]=load_module(path)
                builder = load_module(frozen / "review_pages.py")
                result = builder.build_site(frozen, d, stage)
            write_json(work / "p1_report.json", result)
            result = adapt_p1_report(frozen, stage, result, d)
            manifest["template_version"] = result.get("template_version") if isinstance(result, dict) else None
            errors.extend(validate_pages(stage, result, d))
        except Exception as exc:
            errors.append(f"P1 build failure: {exc}")
        validated_pages = tree_hashes(stage)
        manifest["checks"] = run_checks(frozen, stage, d)
        errors.extend(check_errors(manifest["checks"]))
        if hashes(root, names) != before:
            errors.append("source changed during build")
        if hashes(frozen, names) != before:
            errors.append("frozen inputs changed during build")
        manifest["page_hashes"] = tree_hashes(stage)
        if manifest["page_hashes"] != validated_pages:
            errors.append("page changed after validation")
        degraded = isinstance(result, dict) and result.get("status") == "degraded"
        if degraded and publish:
            errors.append("degraded cannot publish (allow_degraded is preview-only)")
        if not errors:
            manifest["status"] = "degraded" if degraded else "pass"
        # Final checks occur before any immutable release or CURRENT change.
        if publish and manifest["status"] == "pass":
            manifest["published"] = True
            write_json(work / "manifest.json", manifest)
            destination = releases / build_id
            if destination.exists():
                raise ValueError("immutable release already exists")
            os.rename(work, destination)
            pointer = {"schema_version": 1, "d": d, "build_id": build_id, "revision": revision,
                       "release": f"releases/{build_id}", "manifest_sha256": digest(destination / "manifest.json")}
            atomic_json(contained(root, "CURRENT.json"), pointer)
            return dict(manifest, release_dir=str(destination))
    except Exception as exc:
        manifest["status"] = "fail"
        manifest["published"] = False
        errors.append(str(exc))
    if work.exists():
        write_json(work / "manifest.json", manifest)
    return dict(manifest, preview_dir=str(work))


def build_release(root: Path, d: str, *, publish: bool = False, allow_degraded: bool = False) -> dict:
    try:
        valid_date(d)
        root = Path(root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("root must be directory")
        with exclusive(root):
            return _build(root, d, publish, allow_degraded)
    except Exception as exc:
        return fail(d, [exc])


def verify_release(root: Path, d: str) -> dict:
    """Verify CURRENT, manifest identity, complete check set and every frozen hash."""
    try:
        valid_date(d)
        root = Path(root).resolve(strict=True)
        pointer = read_json(contained(root, "CURRENT.json"))
        if pointer.get("schema_version") != 1 or pointer.get("d") != d:
            raise ValueError("CURRENT date/schema mismatch")
        build_id = pointer.get("build_id", "")
        if not re.fullmatch(d + r"-[0-9]+-[0-9a-f]{32}", build_id):
            raise ValueError("CURRENT build_id invalid")
        if pointer.get("release") != f"releases/{build_id}":
            raise ValueError("CURRENT release path invalid")
        directory = contained(root, pointer["release"])
        mp = contained(directory, "manifest.json")
        if digest(mp) != pointer.get("manifest_sha256"):
            raise ValueError("manifest hash mismatch")
        m = read_json(mp)
        if m.get("schema_version") != 1 or m.get("status") != "pass" or m.get("errors") != [] or m.get("published") is not True:
            raise ValueError("manifest not accepted PASS")
        for key in ("d", "build_id", "revision"):
            if m.get(key) != pointer.get(key):
                raise ValueError(f"manifest {key} mismatch")
        if type(m.get("revision")) is not int or m["revision"] < 1 or not isinstance(m.get("template_version"),str):
            raise ValueError("manifest revision/template invalid")
        if check_errors(m.get("checks")):
            raise ValueError("manifest checks not pass")
        pages = m.get("page_hashes")
        if not isinstance(pages, dict) or not all(r + ".html" in pages for r in ROUTES):
            raise ValueError("manifest missing pages")
        if tree_hashes(directory / "site") != pages:
            raise ValueError("page hashes mismatch")
        sources = m.get("source_hashes")
        if not isinstance(sources, dict) or not (sources.get(f"_学习/judgment_{d}.json") or sources.get(f"_学习/页面判断_{d}.json")) or not sources.get("review_pages.py"):
            raise ValueError("manifest source_hashes invalid")
        if hashes(directory / "inputs", sources) != sources:
            raise ValueError("source hashes mismatch")
        return dict(m, release_dir=str(directory), manifest_sha256=pointer["manifest_sha256"])
    except Exception as exc:
        return fail(d, [exc])



@contextlib.contextmanager
def readonly_files(root, stage):
    """Deny mutation and out-of-root data reads while executing audited legacy code."""
    root, stage = Path(root).resolve(), Path(stage).resolve()
    allowed = (root, stage, Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
    seen, denied = set(), []
    old_open, old_io = builtins.open, io.open
    def checked(file, mode="r", *args, **kw):
        if isinstance(file, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(file)).resolve()
            if any(c in mode for c in "wax+"):
                denied.append("write: " + str(path))
                raise PermissionError(denied[-1])
            if not any(path.is_relative_to(base) for base in allowed):
                denied.append("outside read: " + str(path))
                raise PermissionError(denied[-1])
            if path.is_relative_to(root):
                seen.add(path.relative_to(root).as_posix())
        return old_open(file, mode, *args, **kw)
    builtins.open = io.open = checked
    try:
        yield seen, denied
    finally:
        builtins.open, io.open = old_open, old_io


def run_consistency(root, stage, d):
    """Execute every C1..C11 statement; rewrite only filesystem bindings in memory."""
    valid_date(d)
    source = contained(root, "复盘一致性哨兵.py")
    code = source.read_text(encoding="utf-8-sig")
    tree = ast.parse(code, filename=str(source))
    class Bind(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                norm = node.value.replace("\\", "/")
                if norm == "D:/股票数据/市场数据":
                    return ast.copy_location(ast.Constant(str(root)), node)
                if norm == "/sessions/*/mnt/股票数据/市场数据":
                    return ast.copy_location(ast.Constant(str(root / ".no_session_roots")), node)
                if norm == "D:/股票数据/量价因子库/data/daily":
                    return ast.copy_location(ast.Constant(str(root / "_external" / "candidates")), node)
            return node
        def visit_Assign(self, node):
            self.generic_visit(node)
            if any(isinstance(t, ast.Name) and t.id == "SITE" for t in node.targets):
                node.value = ast.Constant(str(stage))
            return node
    tree = ast.fix_missing_locations(Bind().visit(tree))
    # The original calendar cache writer is deliberately never invoked. Use its
    # existing read-only _build only when the cache is absent, with no persistence.
    cal = load_module(root / "trading_calendar.py")
    def calendar():
        p = root / "_学习" / "_交易日历.json"
        values = read_json(p) if p.exists() else cal._build(str(root / "_学习" / "_bars_cache"))
        return sorted(str(x) for x in values if str(x) <= d)
    cal.load_trading_calendar = calendar
    old_cal = sys.modules.get("trading_calendar")
    old_argv, old_path = sys.argv[:], sys.path[:]
    sys.modules["trading_calendar"] = cal
    sys.argv = [str(source), d]
    scope = {"__name__": "_isolated_consistency", "__file__": str(source)}
    output = io.StringIO()
    exit_code = 1
    rule_starts=[(i,match.group(1)) for i,line in enumerate(code.splitlines(),1)
        if (match:=re.match(r'# -+ (C[0-9]+) ',line))]
    reached=set()
    old_trace=sys.gettrace()
    def coverage(frame,event,arg):
        if event=='line' and frame.f_code.co_filename==str(source):
            rules=[name for line,name in rule_starts if line<=frame.f_lineno]
            if rules:reached.add(rules[-1])
        return coverage
    try:
        with readonly_files(root, stage) as (reads, denied), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                sys.settrace(coverage)
                exec(compile(tree, str(source), "exec"), scope)
            except SystemExit as exc:
                exit_code = exc.code
    except Exception as exc:
        scope.setdefault("FAIL", []).append("adapter exception: " + str(exc))
    finally:
        sys.settrace(old_trace)
        sys.argv[:], sys.path[:] = old_argv, old_path
        if old_cal is None:
            sys.modules.pop("trading_calendar", None)
        else:
            sys.modules["trading_calendar"] = old_cal
    errors = [str(x) for x in scope.get("FAIL", [])] + denied
    if exit_code != 0 and not errors:
        errors.append("consistency exit=" + str(exit_code))
    return {"name": "consistency", "status": "fail" if errors else "pass", "errors": errors,
            "warnings": scope.get("WARN", []), "log": output.getvalue(), "exit_code": exit_code,
            "executed_rules": sorted(reached,key=lambda x:int(x[1:])), "source_sha256": digest(source),
            "path_bindings": {"R":str(root), "SITE":str(stage)}, "read_files":sorted(reads)}


def canonical_text(value):
    class Text(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
        def handle_data(self,data):self.parts.append(data)
    parser=Text();parser.feed(str(value));parser.close()
    return ''.join(''.join(parser.parts).split())


def source_value(root, source, pointer):
    if not isinstance(source,str) or not source:
        raise ValueError("missing source")
    rel = source.split('#',1)[0]
    if '/' not in rel and '\\' not in rel:
        rel = '_学习/' + rel
    path = contained(root, rel)
    value = read_json(path)
    for token in pointer.strip('/').split('/') if pointer.strip('/') else []:
        token = token.replace('~1','/').replace('~0','~')
        value = value[int(token)] if isinstance(value,list) else value[token]
    return value


def expected_kpis(root,d,route,template_version=None):
    """Independent dated arithmetic for P1.1 hashed source KPI slots."""
    def get(name):
        p=contained(root,'_学习/'+name)
        return read_json(p) if p.exists() else None
    market=(get('_市场温度表.json') or {}).get(d,{})
    sources=['_市场温度表.json']
    if route=='index':
        row=(get('_情绪先行指标.json') or {}).get(d,{}).get('晋级',{})
        values=[market.get('温度'),market.get('成交额亿'),
            f"{market['涨停数']}/{market['跌停数']}" if all(k in market for k in ('涨停数','跌停数')) else None,row.get('一进二率')]
        sources+=['_情绪先行指标.json']
    elif route=='cycle':
        values=[market.get('成交额亿'),None,market.get('温度'),None]
        if template_version=='p1.2':
            sources.append('_周期投票台账.jsonl')
            path=root/'_学习/_周期投票台账.jsonl'
            votes=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()] if path.exists() else []
            vote=next((row for row in reversed(votes) if row.get('d')==d),{})
            judgment=get('judgment_'+d+'.json') or {}
            if judgment.get('bodies',{}).get('cycle') or get('cycle判断_'+d+'.json'):
                values[1]=vote.get('主判',{}).get('stage')
    elif route=='limitup':values=[market.get('涨停数'),market.get('最高板'),market.get('温度'),None]
    elif route=='auction':
        sources=[f'竞价评分_{d}.json'];rows=(get(sources[0]) or {}).get('明细') or []
        values=[None]*4
        if rows:
            top=max(rows,key=lambda x:x.get('竞价分') if x.get('竞价分') is not None else -1)
            values=[f"{sum(str(r.get('信号','')).startswith('一字') for r in rows)}/{len(rows)}",len(rows),top.get('名称'),None]
    elif route=='lhb':
        sources=['_资金温度.json'];row=next((r for r in (get(sources[0]) or []) if str(r.get('日'))==d),{})
        values=[row.get('温度分位'),f"{row['机构席次']}席 / {row['机构金额亿']}亿" if all(k in row for k in ('机构席次','机构金额亿')) else None,None,None]
        if template_version=='p1.2':
            sources.append('席位荐票_'+d+'.json')
            picks=(get(sources[-1]) or {}).get('top5',[])
            values[2]=picks[0].get('名称') if picks else None
    elif route=='theme':
        sources=['_题材四维.json'];row=(get(sources[0]) or {}).get(d,{})
        widths=[v['宽度'] for v in row.values() if isinstance(v,dict) and v.get('宽度') is not None]
        values=[max(widths) if widths else None,'；'.join(row.get('_警报',[])) or None,None,None]
    elif route=='logic':
        sources=[f'中报预增雷达_{d}.json','链条纵深库.json'];radar=get(sources[0]) or {};lib=get(sources[1])
        values=[radar.get('统计',{}).get('成色A共振'),sum(isinstance(v,dict) and str(v.get('最后更新','99999999'))<=d for v in lib.values()) if lib is not None else None,None,None]
    else:raise ValueError('unsupported KPI route')
    return values,{'_学习/'+n for n in sources if contained(root,'_学习/'+n).exists()}


def validate_model_sources(root, d, models):
    """Independent checks of source values, dated evidence, full placement and cognition."""
    errors=[]
    resolve=functools.lru_cache(maxsize=4096)(lambda source,pointer: source_value(root,source,pointer))
    normalized=functools.lru_cache(maxsize=4096)(canonical_text)
    for route, model in models.items():
        try:
            if model.get('schema_version') != 1 or model.get('d') != d or model.get('route') != route:
                raise ValueError('model schema/date/route')
            if model.get('complete') is not True or model.get('status') not in ('ok','pass') or model.get('errors'):
                raise ValueError('model incomplete: '+str(model.get('errors')))
            claims=model.get('claims',[])
            ids={c['id'] for c in claims}
            if len(ids)!=len(claims) or not ids:
                raise ValueError('duplicate/empty claims')
            refs={key for section in model['sections'] for key in section['claim_refs']}
            optional_empty={('cycle','research'),('logic','forward')}
            if refs!=ids or any(not section['claim_refs'] and (route,section['id']) not in optional_empty for section in model['sections']):
                raise ValueError('unplaced claims or empty sections')
            if not any(c['role']=='cognition' for c in claims):
                raise ValueError('missing cognition')
            evs={e['id']:e for e in model['evidence']}
            if len(evs)!=len(model['evidence']):raise ValueError('duplicate evidence')
            for e in evs.values():
                valid_date(e['d'])
                if e['d']>d:raise ValueError('future evidence')
                if e.get('sha256'):
                    source=e['source'] if '/' in e['source'] else '_学习/'+e['source']
                    if digest(contained(root,source))!=e['sha256']:raise ValueError('evidence hash mismatch: '+e['id'])
                    continue
                pointer=e.get('pointer','')
                # Legacy /block indexes refer to the archived HTML import, not a
                # JSON array; each associated fragment is separately verified below.
                if pointer.startswith('/bodies/') and len(pointer.split('/')) > 3:
                    resolve(e['source'],'/'.join(pointer.split('/')[:3]))
                    continue
                value=resolve(e['source'],pointer)
                if 'value' in e:
                    actual=value.get('value') if isinstance(value,dict) and 'value' in value else value
                    if actual!=e['value']:raise ValueError('evidence value mismatch: '+e['id'])
            for c in claims:
                if not c.get('evidence_refs') or any(r not in evs for r in c['evidence_refs']):
                    raise ValueError('unresolved claim evidence: '+c['id'])
                pointer=c.get('source_pointer','')
                if pointer.startswith('/bodies/') and len(pointer.split('/')) > 3:
                    original=resolve(c['source'],'/'.join(pointer.split('/')[:3]))
                    if normalized(c['text']) not in normalized(original):
                        raise ValueError('legacy claim absent from source: '+c['id'])
                elif c.get('source'):
                    original=resolve(c['source'],pointer)
                    text=original if isinstance(original,str) else json.dumps(original,ensure_ascii=False,indent=2)
                    if normalized(text)!=normalized(c['text']):
                        raise ValueError('claim changed from source: '+c['id'])
            derived=any(e.get('sha256') for e in evs.values()) and any(k.get('id','').startswith('slot-') for k in model['kpis'])
            expected,required=expected_kpis(root,d,route,model.get("template_version")) if derived else (None,None)
            if len(model['kpis'])!=4:raise ValueError('four KPI slots required')
            for index,k in enumerate(model['kpis']):
                references=k.get('evidence_refs',[])
                if any(r not in evs for r in references):raise ValueError('unresolved KPI evidence')
                if derived:
                    actual={evs[r]['source'] for r in references if evs[r].get('sha256')}
                    if k.get('id')!='slot-'+str(index) or actual!=required or k['value']!=expected[index]:
                        raise ValueError('derived KPI mismatch: '+str(k.get('id')))
                elif k['value'] is not None and not any(evs[r].get('value')==k['value'] for r in references):
                    raise ValueError('KPI without matching evidence')
        except Exception as exc:
            errors.append(route+': '+str(exc))
    return errors




class _DOM(HTMLParser):
    def __init__(self,raw):
        super().__init__(convert_charrefs=True)
        self.stack=[];self.ids={};self.headings=[];self.kpis=[];self.duplicates=[]
        self.feed(raw);self.close()
    def handle_starttag(self,tag,attrs):
        node={'tag':tag,'attrs':dict(attrs),'text':[],'parts':[],'ancestors':list(self.stack)}
        if self.stack:self.stack[-1]['parts'].append(node)
        if node['attrs'].get('id'):
            key=node['attrs']['id']
            if key in self.ids:self.duplicates.append(key)
            self.ids[key]=node
        if tag=='h2':self.headings.append(node)
        if 'kpi' in node['attrs'].get('class','').split():self.kpis.append(node)
        if tag not in ('meta','link','img','br','hr','input','source','wbr','col','area','base','embed'):
            self.stack.append(node)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:del self.stack[i:];break
    def handle_data(self,data):
        if self.stack:self.stack[-1]['parts'].append(data)
        for node in self.stack:node['text'].append(data)


def component_source_text(root,d,route,comp):
    """Re-read producer artifacts or rerun only audited pure rendering functions."""
    key=comp['id']
    artifacts={'index':{'IDXLEAD':'先行指标灯','IDXVOTE':'周期投票牌'},
        'cycle':{'LEADIND':'先行指标卡','VOTEBOARD':'周期投票牌'},
        'auction':{'SCORECARD':'竞价评分卡','MACHSIG':'竞价评分库卡'},
        'lhb':{'SEATCARD':'席位荐票卡','FUNDTEMP':'资金温度卡'},
        'limitup':{'SCORECARD':'涨停质量荐票卡','TEMPCARD':'市场温度卡','QUALITYLIB':'质量库折叠'}}
    if key in artifacts.get(route,{}):
        name=f"_学习/{artifacts[route][key]}_{d}.html"
        if name not in {r['path'] for r in comp['sources']}:raise ValueError('required component artifact not reported')
        return canonical_text(contained(root,name).read_text(encoding='utf-8-sig'))
    if (route,key) in (('auction','POOLLEDGER'),('lhb','LHBLEDGER'),('limitup','LEDGER')):
        body=read_json(root/'_学习'/f'judgment_{d}.json')['bodies'][route]
        match=re.search('<!--'+key+'-->(.*?)<!--/'+key+'-->',body,re.S)
        if not match:raise ValueError('ledger source anchor missing')
        return canonical_text(match[1])
    functions={'index':{'IDXTEMP':'r_mach_temp'},'cycle':{'VOLSTEP':'r_mach_volstep','LADDER':'r_mach_ladder'},
        'theme':{'THEMEBATTLE':'r_chart_matrix','LIFECYCLE':'r_chart_lifeaxis'},
        'logic':{'MACHCHAIN':'r_mach_chain','MACHRADAR':'r_mach_radar','MACHHIST':'r_mach_hist'}}
    function=functions.get(route,{}).get(key)
    if function is None:raise ValueError('unknown machine component '+key)
    with isolated_imports(root,root):
        for dep in ('logic_pool','_认知库渲染'):
            path=root/(dep+'.py')
            if path.exists():sys.modules[dep]=load_module(path)
        module=load_module(root/('module_render_'+route+'.py'))
        module.BASE=module.R=str(root);module.L=str(root/'_学习')
        def read(name,date=None):
            name=name if date is None else name % date
            path=contained(root,'_学习/'+name)
            if not path.exists():return None
            data=read_json(path)
            if isinstance(data,dict):
                if name=='链条纵深库.json':return {k:v for k,v in data.items() if isinstance(v,dict) and str(v.get('最后更新','99999999'))<=d}
                return {k:v for k,v in data.items() if not re.fullmatch(r'20[0-9]{6}',k) or k<=d}
            return data
        module.load_json=read
        with readonly_files(root,root):
            return canonical_text(getattr(module,function)(d))


def expanded_dom_text(node,dom,visited=None):
    visited=set() if visited is None else visited
    href=node['attrs'].get('href','')
    if node['tag']=='a' and href.startswith('#table-'):
        target=href[1:]
        if target in visited or target not in dom.ids:raise ValueError('invalid table reference')
        return expanded_dom_text(dom.ids[target],dom,visited|{target})
    return ''.join(part if isinstance(part,str) else expanded_dom_text(part,dom,visited) for part in node['parts'])


def view_check(root,stage,d,route):
    errors=[];dimensions=[]
    try:
        model=read_json(stage/'models'/(route+'.json'))
        errors.extend(validate_model_sources(root,d,{route:model}))
        contract=page_contract(root)
        raw=(stage/(route+'.html')).read_text(encoding='utf-8')
        dom=_DOM(raw)
        if dom.duplicates:errors.append('duplicate IDs: '+str(dom.duplicates[:10]))
        expected=[num+' '+section['title'] for num,section in zip('一二三四五六七',contract['routes'][route]['sections'])]
        headings=[''.join(n['text']).strip() for n in dom.headings]
        if headings!=expected:errors.append('ordered section contract mismatch: '+str(headings))
        dimensions.append('named sections and unique DOM IDs')
        if len(dom.kpis)!=4:errors.append('four KPI slots required')
        else:
            for k,node in zip(model['kpis'],dom.kpis):
                value='—' if k['value'] is None else str(k['value'])
                if canonical_text(value) not in ''.join(''.join(node['text']).split()):errors.append('rendered KPI mismatch: '+k['id'])
        dimensions.append('four rendered KPI values against source-checked model')
        for claim in model['claims']:
            node=dom.ids.get('claim-'+claim['id'])
            if not node:errors.append('missing claim DOM: '+claim['id']);continue
            if claim.get('component_ref'):
                if 'component-'+claim['component_ref'] not in dom.ids:errors.append('claim component missing: '+claim['id'])
            elif claim.get('history_ref'):
                url=urlsplit(claim['history_ref']);target=contained(stage,stage/url.path)
                if not target.is_file() or 'id="'+url.fragment+'"' not in target.read_text(encoding='utf-8'):errors.append('claim history missing: '+claim['id'])
            elif canonical_text(claim['text']) not in canonical_text(''.join(node['text'])):
                # A deduplicated table is an explicit reference, not discarded data.
                text=canonical_text(claim['text'])
                if text not in canonical_text(raw):errors.append('claim text not displayed/referenced: '+claim['id'])
        dimensions.append('all claim IDs and complete source text/history targets')
        for comp in model.get('components',[]):
            if comp.get('status')!='ok' or not comp.get('html') or not comp.get('sources'):
                if comp.get('allow_missing') and comp.get('status')=='missing' and comp.get('html') and '—' in comp.get('html'):
                    node=dom.ids.get('component-'+comp['id'])
                    if node is None:errors.append('missing optional component DOM '+comp['id'])
                    continue
                errors.append('missing machine component '+comp['id']);continue
            for src in comp['sources']:
                if digest(contained(root,src['path']))!=src['sha256']:errors.append('component source hash mismatch '+comp['id'])
            node=dom.ids.get('component-'+comp['id'])
            if node is None:errors.append('component absent from DOM '+comp['id'])
            else:
                original=component_source_text(root,d,route,comp)
                model_text=canonical_text(comp['html'])
                rendered=''.join(expanded_dom_text(node,dom).split())
                # Folding adds a single navigational summary, not a new data row.
                strip_fold=lambda text:re.sub(r'更早存档[0-9]+条','',text)
                original_data,model_data=strip_fold(original),strip_fold(model_text)
                same=original_data==model_data
                if not same and comp['id'] in ('POOLLEDGER','LHBLEDGER','LEDGER') and model_data and original_data.endswith(model_data):
                    # P1 may place the ledger's descriptive prefix in a source
                    # claim beside the component. It must remain displayed in
                    # full; every ledger row still matches the producer suffix.
                    prefix=original_data[:-len(model_data)]
                    same=any(prefix in canonical_text(c['text']) and
                        'claim-'+c['id'] in dom.ids and prefix in ''.join(expanded_dom_text(dom.ids['claim-'+c['id']],dom).split())
                        for c in model['claims'])
                if not same:errors.append('machine component changed from producer '+comp['id'])
                if model_text!=rendered:errors.append('machine component differs in DOM '+comp['id'])
        dimensions.append('machine producer revalidation, source hashes and complete DOM content including table aliases')
        for anchor in contract.get('machine_anchors',{}).get(route,{}):
            if raw.count('<!--'+anchor+'-->')!=1 or raw.count('<!--/'+anchor+'-->')!=1:
                errors.append('machine anchor pair '+anchor)
        dimensions.append('required machine anchors exactly paired')
    except Exception as exc:errors.append(str(exc))
    return {'name':route,'status':'fail' if errors else 'pass','errors':errors,'contract':'p1.1','dimensions':dimensions}

def page_contract(root):
    path=contained(root,'_契约/页面契约.v1.json')
    contract=read_json(path)
    if type(contract.get('schema_version')) is not int or contract['schema_version']!=1 or set(contract.get('routes',{}))!=set(ROUTES):
        raise ValueError('page contract schema/routes invalid')
    return contract


def validate_structured_input(root,d):
    errors=[]
    def keys(obj,allowed,label):
        if not isinstance(obj,dict) or set(obj)-set(allowed):raise ValueError(label+' unknown fields/type')
    try:
        doc=read_json(root/'_学习'/f'页面判断_{d}.json')
        keys(doc,('schema_version','d','evidence','pages'),'document')
        if type(doc.get('schema_version')) is not int or doc['schema_version']!=1 or doc.get('d')!=d:raise ValueError('document schema/date')
        if set(doc.get('pages',{}))!=set(ROUTES):raise ValueError('seven structured pages required')
        contract=page_contract(root)
        evidence={}
        for e in doc['evidence']:
            keys(e,('id','d','source','pointer','value','quality'),'evidence')
            valid_date(e['d'])
            if e['d']>d or e['id'] in evidence:raise ValueError('future/duplicate evidence')
            actual=source_value(root,e['source'],e['pointer'])
            if 'value' in e:
                actual=actual.get('value') if isinstance(actual,dict) and 'value' in actual else actual
                if actual!=e['value']:raise ValueError('evidence differs from source: '+e['id'])
            if e.get('quality')=='conflicted':raise ValueError('conflicted evidence')
            evidence[e['id']]=e
        for route,page in doc['pages'].items():
            keys(page,('hero','kpis','claims','sections','limitations'),'page '+route)
            ids={c['id'] for c in page['claims']}
            if not ids or len(ids)!=len(page['claims']):raise ValueError('empty/duplicate claims '+route)
            sections={s['id'] for s in contract['routes'][route]['sections']}
            placed=set()
            for section in page['sections']:
                keys(section,('id','claim_refs'),'section')
                if section['id'] not in sections or not section['claim_refs']:raise ValueError('missing/unknown section')
                for ref in section['claim_refs']:
                    if ref not in ids:raise ValueError('unresolved claim')
                    placed.add(ref)
            if {s['id'] for s in page['sections']}!=sections or placed!=ids:raise ValueError('incomplete placement '+route)
            if not any(c['role']=='cognition' for c in page['claims']):raise ValueError('missing cognition '+route)
            for claim in page['claims']:
                keys(claim,('id','role','text','section','evidence_refs'),'claim')
                if claim['section'] not in sections or not isinstance(claim['text'],str) or not claim['text'].strip():raise ValueError('claim invalid')
                if claim['role'] not in ('verdict','observation','evidence','counterevidence','condition','research','cognition','limitation'):raise ValueError('claim role invalid')
                if not claim['evidence_refs'] or any(ref not in evidence for ref in claim['evidence_refs']):raise ValueError('claim lacks evidence')
            keys(page['hero'],('claim_ref','change_ref'),'hero')
            if page['hero'].get('claim_ref') not in ids:raise ValueError('hero unresolved')
            if len(page['kpis'])!=4 or len({k['id'] for k in page['kpis']})!=4:raise ValueError('four KPI slots required')
            for k in page['kpis']:
                keys(k,('id','label','value','evidence_refs'),'kpi')
                if any(ref not in evidence for ref in k['evidence_refs']):raise ValueError('KPI ref unresolved')
                if k['value'] is not None and not any(evidence[ref].get('value')==k['value'] for ref in k['evidence_refs']):raise ValueError('KPI not backed by source')
    except Exception as exc:errors.append('structured input: '+str(exc))
    return errors


def adapt_p1_report(root,stage,result,d):
    """Explicit p1.1 bridge; preserve failure, verify sidecars, whitelist auxiliary pages."""
    if not isinstance(result,dict):return result
    if result.get('status')=='fail' and 'pages' not in result and (root/'_契约'/'页面契约.v1.json').is_file():
        contract=page_contract(root)
        return dict(result,pages=[],template_version=contract['template_version'],contract='p1.1',contract_snapshot=contract)
    if not isinstance(result.get('pages'),dict):return result
    contract=page_contract(root)
    missing=[route for route in ROUTES if not (stage/'models'/(route+'.json')).is_file()]
    if missing:
        return dict(result,status='fail',pages=[],template_version=contract['template_version'],
            errors=[str(e) for e in result.get('errors',[])]+['P1 models missing: '+', '.join(missing)])
    models={route:read_json(stage/'models'/(route+'.json')) for route in ROUTES}
    errors=[str(e) for e in result.get('errors',[])]+validate_model_sources(root,d,models)
    entries=[]
    for route,path in result['pages'].items():
        status=result.get('page_status',{}).get(route)
        entries.append({'route':route,'path':path,'status':'pass' if status in ('ok','pass') else status,'errors':models.get(route,{}).get('errors',[])})
    auxiliary=[]
    # Stable old auxiliary pages are copied byte-for-byte, never rewritten.
    source_site=root/'复盘'/'盯盘台'
    preserve=[source_site/'intraday.html',source_site/'history.html']
    if (source_site/'archive').exists():preserve += [p for p in (source_site/'archive').rglob('*') if p.is_file()]
    for source in preserve:
        if not source.is_file():continue
        rel=source.relative_to(source_site).as_posix()
        target=contained(stage,rel)
        if target.exists() and digest(target)!=digest(source):
            errors.append('auxiliary conflict: '+rel);continue
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        auxiliary.append({'path':rel,'kind':'preserved','source':source.relative_to(root).as_posix(),'sha256':digest(target)})
    for route,model in models.items():
        claims=[c for c in model['claims'] if c.get('history_ref')]
        if claims:
            rel='history_sources/'+route+'.html'
            page=contained(stage,rel).read_text(encoding='utf-8')
            for c in claims:
                if 'id="claim-'+c['id']+'"' not in page or c.get('legacy_html','') not in page:
                    errors.append('history source coverage missing: '+c['id'])
            auxiliary.append({'path':rel,'kind':'p1_history','model':route,'sha256':digest(stage/rel)})
    return dict(result,status='fail' if errors else 'pass' if result.get('status') in ('ok','pass') else result.get('status'),
                pages=entries,errors=errors,template_version=contract['template_version'],
                contract='p1.1',contract_snapshot=contract,auxiliary_assets=auxiliary)

class _CDP:
    """Small stdlib WebSocket client for a private local Chrome DevTools target."""
    def __init__(self,url):
        u=urlsplit(url)
        self.socket=socket.create_connection((u.hostname,u.port),timeout=15)
        key=base64.b64encode(os.urandom(16)).decode()
        self.socket.sendall((f'GET {u.path} HTTP/1.1\r\nHost: {u.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        self.file=self.socket.makefile('rb')
        header=self.file.readline()
        if b'101' not in header:raise ValueError('CDP upgrade failed: '+repr(header))
        while self.file.readline() not in (b'\r\n',b''):
            pass
        self.seq=0
        self.events=[]
    def call(self,method,params=None):
        self.seq+=1
        raw=json.dumps({'id':self.seq,'method':method,'params':params or {}}).encode()
        n=len(raw);mask=os.urandom(4)
        head=bytes([129,128|n]) if n<126 else bytes([129,254])+struct.pack('!H',n) if n<65536 else bytes([129,255])+struct.pack('!Q',n)
        self.socket.sendall(head+mask+bytes(b^mask[i%4] for i,b in enumerate(raw)))
        while True:
            head=self.file.read(2)
            if len(head)!=2:raise EOFError('CDP closed')
            n=head[1]&127
            if n==126:n=struct.unpack('!H',self.file.read(2))[0]
            elif n==127:n=struct.unpack('!Q',self.file.read(8))[0]
            mask=self.file.read(4) if head[1]&128 else None
            payload=self.file.read(n)
            if mask:payload=bytes(b^mask[i%4] for i,b in enumerate(payload))
            if head[0]&15==8:raise EOFError('CDP close frame')
            msg=json.loads(payload)
            if msg.get('id')==self.seq:
                if 'error' in msg:raise ValueError(str(msg['error']))
                return msg.get('result',{})
            self.events.append(msg)
    def close(self):
        self.file.close();self.socket.close()


def _wait_devtools_port(proc,portfile,timeout=25):
    """Existence is not readiness: Chromium can hold or partially write this file."""
    deadline=time.monotonic()+timeout
    last_error='not ready'
    while time.monotonic()<deadline:
        if proc.poll() is not None:
            raise RuntimeError('Chrome exited before DevTools became ready')
        try:
            lines=portfile.read_text(encoding='utf-8').splitlines()
            if len(lines)>=2 and lines[1].startswith('/devtools/browser/'):
                port=int(lines[0])
                if 0<port<65536:
                    return port
            last_error='incomplete or invalid DevToolsActivePort'
        except (FileNotFoundError,PermissionError,UnicodeError,ValueError) as exc:
            last_error=f'{type(exc).__name__}: {exc}'
        time.sleep(.05)
    raise TimeoutError(f'DevToolsActivePort readiness timeout: {last_error}')


def browser_check(root,stage,d):
    """Real headless Chromium: both viewports, geometry, visible content and toggles."""
    candidates=[os.environ.get('REVIEW_BROWSER'),shutil.which('chrome'),shutil.which('msedge')]
    for base in (os.environ.get('PROGRAMFILES'),os.environ.get('PROGRAMFILES(X86)'),os.environ.get('LOCALAPPDATA')):
        if base:
            candidates.extend(str(Path(base)/suffix) for suffix in ('Google/Chrome/Application/chrome.exe','Microsoft/Edge/Application/msedge.exe'))
    exe=next((x for x in candidates if x and Path(x).is_file()),None)
    if not exe:return {'name':'browser','status':'fail','errors':['Chrome/Edge not found']}
    errors=[];results=[];version=None
    artifacts=stage.parent/'check_artifacts'/'browser'/(stage.name+'-'+uuid.uuid4().hex)
    artifacts.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='profile-',dir=artifacts) as temp:
        log=(artifacts/('chrome-'+uuid.uuid4().hex+'.log')).open('wb')
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
        proc=subprocess.Popen([exe,'--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
            '--disable-background-networking','--disable-extensions','--remote-debugging-port=0',
            '--user-data-dir='+temp,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
        client=None
        try:
            portfile=Path(temp)/'DevToolsActivePort'
            port=_wait_devtools_port(proc,portfile)
            targets=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list',timeout=10))
            client=_CDP(next(t['webSocketDebuggerUrl'] for t in targets if t['type']=='page'))
            version=client.call('Browser.getVersion')
            client.call('Page.enable');client.call('Runtime.enable')
            client.call('Network.enable');client.call('Network.setBlockedURLs',{'urls':['http://*','https://*']})
            for width in (1440,390):
                client.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':900,'deviceScaleFactor':1,'mobile':width==390})
                for route in ROUTES:
                    path=stage/(route+'.html')
                    if not path.is_file():errors.append(route+': missing browser page');continue
                    client.events=[]
                    client.call('Page.navigate',{'url':path.as_uri()})
                    for _ in range(50):
                        ready=client.call('Runtime.evaluate',{'expression':'document.readyState','returnByValue':True})
                        if ready.get('result',{}).get('value')=='complete':break
                        time.sleep(.05)
                    expression="""(async()=>{await new Promise(r=>setTimeout(r,250));
                    const errors=[];const sw=document.documentElement.scrollWidth;
                    if(sw>innerWidth+2)errors.push('overflow '+sw+' > '+innerWidth);
                    const body=getComputedStyle(document.body);
                    if(body.display==='none'||body.visibility==='hidden'||+body.opacity===0)errors.push('body invisible');
                    const nodes=[...document.querySelectorAll('[id]')];const ids=nodes.map(x=>x.id);
                    if(new Set(ids).size!==ids.length)errors.push('duplicate DOM IDs');
                    const toggles=[...document.querySelectorAll('details')];
                    let tested=0;for(const x of toggles){const a=x.open,s=x.querySelector(':scope > summary');if(!s){errors.push('summary missing');continue;}s.click();if(x.open===a)errors.push('details not toggled');s.click();tested++;}
                    const row=document.querySelector('.rowA');
                    if(row){const items=[...row.children].filter(x=>x.matches('.hero,.kpi'));if(items.length!==5||!items[0].matches('.hero')||items.slice(1).some(x=>!x.matches('.kpi')))errors.push('rowA hero/four KPI contract');}
                    return {errors,width:innerWidth,scrollWidth:sw,h2:document.querySelectorAll('h2').length,toggles:tested,title:document.title};})()"""
                    value=client.call('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
                    if value.get('exceptionDetails'):raise ValueError(str(value['exceptionDetails']))
                    result=value['result']['value']
                    errors.extend(f'{route}@{width}: {e}' for e in result['errors'])
                    for event in client.events:
                        if event.get('method') in ('Runtime.exceptionThrown','Network.loadingFailed'):
                            errors.append(f'{route}@{width}: '+event['method']+' '+str(event.get('params',{})))
                    shot=base64.b64decode(client.call('Page.captureScreenshot',{'format':'png'})['data'])
                    image_path=artifacts/f'{route}-{width}.png';image_path.write_bytes(shot)
                    results.append(dict(result,route=route,viewport=width,screenshot=str(image_path),sha256=digest(image_path)))
        except Exception as exc:
            errors.append('browser: '+str(exc))
        finally:
            if client:
                try:client.call("Browser.close")
                except Exception:pass
                client.close()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            log.close()
    return {'name':'browser','status':'fail' if errors else 'pass','errors':errors,'browser_version':version,'pages':results}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify", "_check"))
    parser.add_argument("d")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--allow-degraded", action="store_true")
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--route")
    args = parser.parse_args()
    if args.command == "_check":
        try:
            valid_date(args.d)
            args.root=args.root.resolve()
            if args.stage is None:raise ValueError("--stage required for check")
            args.stage=args.stage.resolve()
            if args.route == "consistency":
                result = run_consistency(args.root, args.stage, args.d)
            elif args.route == "browser":
                result = browser_check(args.root, args.stage, args.d)
            elif args.route == "logic":
                result = view_check(args.root, args.stage, args.d, "logic")
            else:
                result = _check_one(args.root, args.stage, args.d, args.route)
        except Exception as exc:
            result = dict(fail(args.d, [exc]), name=args.route)
    elif args.command == "verify":
        result = verify_release(args.root, args.d)
    else:
        result = build_release(args.root, args.d, publish=args.publish, allow_degraded=args.allow_degraded)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
