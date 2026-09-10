"""Deterministic seven-page renderer. Input root is explicit; no generator side effects."""
from __future__ import annotations
from datetime import datetime
from html import escape
from html.parser import HTMLParser
from hashlib import sha256
import json
import ast
import types
import csv
from pathlib import Path
import re

CONTRACT_PATH = Path(__file__).resolve().parent / "_契约" / "页面契约.v1.json"

# 页面级阅读路径增强：只读取已存在的 section/h2，不引入任何新数据。
VISUAL_JS = r'''<script>
(function(){
  var wrap=document.querySelector('.wrap');
  if(!wrap)return;
  var sections=Array.prototype.filter.call(wrap.children,function(el){return el.tagName==='SECTION';});
  if(sections.length<3)return;
  var map=document.createElement('nav');
  map.className='page-map';
  map.setAttribute('aria-label','本页阅读地图');
  var label=document.createElement('span');
  label.className='page-map-label';
  label.textContent='本页阅读';
  map.appendChild(label);
  var links=[];
  sections.forEach(function(sec,i){
    var h=Array.prototype.find.call(sec.children,function(el){return el.tagName==='H2';});
    if(!h)return;
    if(!sec.id)sec.id='section-'+(i+1);
    var a=document.createElement('a');
    a.href='#'+sec.id;
    a.textContent=h.textContent.replace(/^[一二三四五六七八九十]+\\s*/,'');
    a.setAttribute('data-section',sec.id);
    map.appendChild(a); links.push({a:a,sec:sec});
  });
  if(links.length)wrap.insertBefore(map,sections[0]);
  if(!('IntersectionObserver' in window))return;
  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(!entry.isIntersecting)return;
      links.forEach(function(x){x.a.classList.toggle('active',x.sec===entry.target);});
    });
  },{rootMargin:'-88px 0px -64% 0px',threshold:0});
  links.forEach(function(x){io.observe(x.sec);});
})();
</script>'''

def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

V42_CSS = r'''
/* ── v4.2 reading spine / claim proof layer ── */
.reading-spine{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:14px 0 18px;padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:linear-gradient(90deg,rgba(232,163,61,.08),rgba(255,255,255,.025));color:var(--sub);font-size:11.8px}
.reading-spine .rs-title{color:var(--accent);font-weight:800;letter-spacing:.08em;white-space:nowrap}
.reading-spine .rs-arrow{color:var(--dim);font-family:var(--mono)}
.reading-spine .rs-step{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:8px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.06);white-space:nowrap}
.reading-spine .rs-step b{color:var(--ink);font-family:var(--mono);font-size:10.5px}
.claim-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.claim-role{display:inline-flex;align-items:center;padding:2px 8px;border-radius:8px;font-size:10.8px;font-weight:800;letter-spacing:.04em}
.claim-source{color:var(--dim);font-size:11px}
.role-verdict,.role-observation{color:#f0b6b4;background:rgba(255,95,86,.13)}
.role-evidence{color:var(--hit);background:rgba(47,211,197,.13)}
.role-counterevidence{color:#ffb36b;background:rgba(232,163,61,.14)}
.role-condition,.role-research{color:var(--half);background:rgba(232,163,61,.12)}
.role-cognition{color:#c8b4ff;background:rgba(177,138,255,.13)}
.role-limitation{color:#f0a5a3;background:rgba(255,95,86,.10)}
.claim-proof{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:12px;padding-top:9px;border-top:1px solid rgba(255,255,255,.06);font-size:11.5px;color:var(--dim)}
.claim-proof>a{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent-dim)}
.claim-proof>a:hover{color:var(--ink)}
.claim-proof .proof-label{font-weight:700;color:var(--sub)}
@media(max-width:640px){.reading-spine{align-items:flex-start}.reading-spine .rs-arrow{display:none}.reading-spine .rs-step{flex:1;min-width:132px;justify-content:center}.claim-proof{line-height:1.8}.navbar{align-items:flex-start}.navbar .pills{flex:1 1 100%;width:auto;max-width:100%;min-width:0;flex-wrap:wrap;overflow:visible;row-gap:3px}.navbar .upd{flex:0 0 auto}}
'''

def _page_css(contract):
    base = contract["visual"]["css"]
    return base if 'v4.2 reading spine / claim proof layer' in base else base + V42_CSS

def _check_date(d):
    if not isinstance(d, str) or not re.fullmatch(r"[0-9]{8}", d):
        raise ValueError("d 必须是 YYYYMMDD 八位 ASCII 数字")
    datetime.strptime(d, "%Y%m%d")

def _fail(d, error):
    return {"status": "fail", "errors": [str(error)], "d": d}

def _dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"

def build_page_model(root: Path, d: str, route: str) -> dict:
    try:
        _check_date(d)
        contract = _contract()
        if route not in contract["routes"]:
            raise ValueError("未知 route: " + str(route))
        root = Path(root).resolve()
        spec = contract["routes"][route]
        model = {"schema_version": 1, "d": d, "route": route,
                "template_version": contract["template_version"], "complete": False,
                "status": "degraded", "errors": [], "title": spec["title"],
                "hero": {"text": "当日判断缺失", "claim_refs": []},
                "kpis": [{"id": k, "label": k, "value": None, "evidence_refs": []}
                         for k in ("涨停数", "温度", "最高连板", "成交额亿")],
                "sections": [dict(s, claim_refs=[]) for s in spec["sections"]],
                "claims": [], "limitations": ["当日判断缺失；不重造原决策。"],
                "content_coverage": {"total": 0, "covered": 0, "unmapped": []},
                "role_overlap": [], "editorial_notes": [], "evidence": [], "sources": [], "paper": None}
        source = root / "_学习" / ("页面判断_" + d + ".json")
        if source.exists():
            _structured(model, _read_json(source), source.name, root)
        else:
            _legacy(model, root)
        _paper(model, root)
        _route_kpis(model,root)
        _components(model,root)
        _finish(model)
        return model
    except (ValueError, OSError, TypeError, KeyError) as exc:
        return _fail(d, exc)

ROLES = {"verdict", "observation", "evidence", "counterevidence", "condition", "research", "cognition", "limitation"}
ROLE_LABELS = {"verdict":"结论", "observation":"观察", "evidence":"证据", "counterevidence":"反证", "condition":"条件", "research":"研究", "cognition":"认知", "limitation":"限制"}

EDITORIAL = {
    "index": ["首屏只给总判断及决定性变化，观察点负责次日验证。", "五路看牌保留各自依据，拐点区专列反证与转向条件。", "总裁决交代攻防；Master 专列新问题、线索、指派与认知，不再重复编号。"],
    "cycle": ["量能、先行指标、阶段投票和梯队各自承担一类证据。", "攻防区集中呈现仓位条件，缺周期判断时只回源事实。", "深挖保留新问题，认知保留新验证和下次证伪，历史另行链接。"],
    "auction": ["一池二结算三温度四胜率，池名单和数据表只在所属证据区展开。", "首屏聚焦执行结论；今晨闸门按既定分工链接盘中页。", "深挖负责信号变化与待检验问题，认知负责规则修订和证伪条件。"],
    "lhb": ["综合判断与资金温度分区呈现，席位名单、台账和分档库各归其位。", "S 档小样本、反向资金与条件限定完整保留，不由重复度过滤。", "当日结构化认知优先，标题是否含“我的”不影响可见性。"],
    "theme": ["矩阵按来源原名展示全部判断范围，不将行业归位冒充题材确认。", "龙头与三级判定合并，生命周期另列状态、判据与高低切。", "深挖保留新线问题，认知直接读取条目；没有 tl 类也不丢条目。"],
    "logic": ["荐票、链图库、硬度、前置雷达、中报雷达固定七段中的前五段。", "消息溯源与风险条件在证据区展开；缺失源明确标空，不借未来快照。", "深挖聚焦传导的新问题，认知保留完整日期和规则限制。"],
    "limitup": ["荐票、温度、归位台账与训练库各保留一份数据展示。", "首屏只给质量结论，反证、基准与阈值差异在证据区可回看。", "深挖讲因子和归位的新问题，认知讲验证、修改规则和下次证伪。"],
}

def _read_json(path):
    def reject(value):
        raise ValueError("非法 JSON 非有限数: " + value)
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject)

def _keys(obj, allowed, context):
    if not isinstance(obj, dict):
        raise ValueError(context + " 必须是 object")
    unknown = set(obj) - set(allowed)
    if unknown:
        raise ValueError(context + " 未归位字段: " + ', '.join(sorted(unknown)))

def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("id 必须为 ASCII 字母/数字/下划线/连字符: " + str(value))
    return value

def _verify_evidence(root,item,d):
    source=Path(item['source'])
    if source.is_absolute() or '..' in source.parts:
        raise ValueError('证据路径越界')
    path=(root/source).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('证据路径越界')
    raw=path.read_bytes()
    digest=sha256(raw).hexdigest()
    if item.get('sha256') is not None and item['sha256']!=digest:
        raise ValueError('证据文件哈希不匹配')
    doc=_read_json(path)
    dates=[]
    def remember(value):
        if isinstance(value,dict):
            dates.extend(str(value[k]).replace('-','') for k in ('d','date','日期','日') if k in value)
    remember(doc)
    pointer=item.get('pointer')
    if not isinstance(pointer,str) or (pointer and not pointer.startswith('/')):
        raise ValueError('证据缺少合法 JSON pointer')
    for segment in pointer.split('/')[1:] if pointer else []:
        key=segment.replace('~1','/').replace('~0','~')
        if re.fullmatch(r'20[0-9]{6}',key):dates.append(key)
        try:doc=doc[int(key)] if isinstance(doc,list) else doc[key]
        except (KeyError,IndexError,ValueError,TypeError):raise ValueError('证据 pointer 不存在: '+pointer)
        remember(doc)
    if not dates:
        dates=re.findall(r'20[0-9]{6}',path.name)
    if not dates or any(value!=item['d'] or value>d for value in dates):
        raise ValueError('证据真实来源日期与声明不一致/未来来源')
    if 'value' in item and item['value']!=doc:
        raise ValueError('证据 value 与磁盘真源不一致')
    return dict(item,value=doc,sha256=digest,verified=True)

def _structured(model, doc, filename, root):
    _keys(doc, ("schema_version", "d", "evidence", "pages"), filename)
    if type(doc.get("schema_version")) is not int or doc["schema_version"] != 1 or doc.get("d") != model["d"]:
        raise ValueError(filename + " schema_version/d 不匹配")
    _keys(doc["pages"], _contract()["routes"], "pages")
    if model["route"] not in doc["pages"]:
        model["limitations"] = ["结构化输入缺少当日该路；不回退重造判断。"]
        return
    page = doc["pages"][model["route"]]
    _keys(page, ("hero", "kpis", "claims", "sections", "limitations", "matrix"), "page")
    evidence = {}
    for item in doc["evidence"]:
        _keys(item, ("id", "d", "source", "pointer", "value", "quality", "sha256"), "evidence")
        key = _id(item["id"])
        _check_date(item["d"])
        if item["d"] > model["d"] or key in evidence:
            raise ValueError("未来证据或重复证据 ID: " + key)
        if not isinstance(item.get("source"), str):
            raise ValueError("evidence.source 必须为来源字符串")
        evidence[key] = _verify_evidence(root,item,model["d"])
    def refs(values):
        if not isinstance(values, list) or any(v not in evidence for v in values):
            raise ValueError("未解析 evidence_refs: " + str(values))
        return list(values)
    ids = {s["id"] for s in model["sections"]}
    claims = {}
    for c in page["claims"]:
        _keys(c, ("id", "role", "text", "section", "evidence_refs"), "claim")
        key = _id(c["id"])
        if key in claims or c["section"] not in ids or c["role"] not in ROLES or not isinstance(c["text"], str) or not c["text"].strip():
            raise ValueError("重复/未归位/空 claim: " + key)
        claims[key] = dict(c, evidence_refs=refs(c["evidence_refs"]), source=filename,
                           source_pointer="/pages/" + model["route"] + "/claims/" + str(len(claims)))
    placements = {}
    for item in page["sections"]:
        _keys(item, ("id", "claim_refs"), "section")
        sid = item["id"]
        if sid not in ids or sid in placements or not isinstance(item["claim_refs"], list):
            raise ValueError("未归位/重复 section: " + str(sid))
        if any(c not in claims for c in item["claim_refs"]):
            raise ValueError("section 引用未知 claim")
        placements[sid] = item["claim_refs"]
    for c in claims.values():
        if c["id"] not in placements.get(c["section"], []):
            raise ValueError("source claim 未归位: " + c["id"])
    _keys(page["hero"], ("claim_ref", "change_ref"), "hero")
    hero = page["hero"]
    if hero["claim_ref"] not in claims or (hero.get("change_ref") is not None and hero["change_ref"] not in claims):
        raise ValueError("hero 引用未知 claim")
    if not isinstance(page["kpis"], list) or len(page["kpis"]) != 4:
        raise ValueError("kpis 必须恰好四槽")
    kpi_ids = []
    for k in page["kpis"]:
        _keys(k, ("id", "label", "value", "evidence_refs"), "kpi")
        kpi_ids.append(_id(k["id"]))
        refs(k["evidence_refs"])
        if not isinstance(k["label"], str) or isinstance(k["value"], (dict, list)):
            raise ValueError("kpi label/value 类型无效")
        if k["value"] is not None and not k["evidence_refs"]:
            raise ValueError("有值 KPI 必须有证据")
        if k['value'] is not None and not any(evidence[ref].get('value')==k['value'] for ref in k['evidence_refs']):
            raise ValueError('KPI 数值与证据不一致: '+k['id'])
    if len(set(kpi_ids)) != 4:
        raise ValueError("重复 KPI id")
    if not isinstance(page["limitations"], list) or any(not isinstance(x,str) for x in page["limitations"]):
        raise ValueError("limitations 必须为字符串列表")
    if 'matrix' in page and model['route']!='theme':
        raise ValueError('matrix 只属于 theme')
    if model['route']=='theme':
        model['theme_matrix'] = []
        names = []
        for row in page.get('matrix',[]):
            _keys(row,('name','claim_refs','six_you','evidence_refs'),'matrix row')
            if not isinstance(row['name'],str) or not row['name'].strip() or row['name'] in names:
                raise ValueError('题材原名空白或重复')
            names.append(row['name'])
            if not isinstance(row['claim_refs'],list) or any(key not in claims or claims[key]['section']!='matrix' for key in row['claim_refs']):
                raise ValueError('矩阵 claim 未归位')
            refs(row['evidence_refs'])
            value=row['six_you']
            if value is not None and (type(value) is not int or not 0<=value<=6 or not any(evidence[key].get('value')==value for key in row['evidence_refs'])):
                raise ValueError('6有缺证据或数值无效')
            model['theme_matrix'].append(dict(row,data_scope='原名判断范围；不自动合并行业'))
    model["hero"] = {"text": claims[hero["claim_ref"]]["text"], "claim_refs": [hero["claim_ref"]],
                     "change_ref": hero.get("change_ref")}
    model["claims"] = list(claims.values())
    model["kpis"] = page["kpis"]
    model["evidence"] = list(evidence.values())
    model["sources"] = [filename]
    model["limitations"] = list(page["limitations"])
    for s in model["sections"]:
        s["claim_refs"] = placements.get(s["id"], [])
    model["complete"] = all(s["claim_refs"] for s in model["sections"])
    if not model["complete"]:
        model["limitations"].append("结构化判断有空栏目，尚非完整复盘。")

# Legacy import is a one-way adapter. No renderer/build from the old generator is called.
class _Node:
    def __init__(self, tag="", attrs=(), children=None):
        self.tag, self.attrs = tag, dict(attrs)
        self.children = children or []
    def text(self):
        return ''.join(x.text() if isinstance(x, _Node) else x for x in self.children)
    def has(self, tag):
        return self.tag == tag or any(isinstance(x, _Node) and x.has(tag) for x in self.children)

class _Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack = [self.root]
        self.feed(html)
        self.close()
    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"br", "hr", "img", "input", "meta", "link", "wbr", "source", "col"}:
            self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag:
            self.stack.pop()
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break
    def handle_data(self, data):
        self.stack[-1].children.append(data)
    def handle_comment(self, data):
        self.stack[-1].children.append(_Node("comment", {"text": data}))

def _safe_html(node):
    if isinstance(node, str):
        return escape(node)
    if node.tag == "comment":
        return ''  # Machine anchors are emitted once by the fixed template.
    children = ''.join(_safe_html(x) for x in node.children)
    if node.tag == "root":
        return children
    if node.tag in {"script", "style", "iframe", "object", "embed", "form"}:
        return '<pre>' + escape(node.text()) + '</pre>'
    allowed = {"div", "span", "p", "b", "strong", "i", "em", "small", "br", "hr", "ul", "ol", "li", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "details", "summary", "h1", "h2", "h3", "h4", "a", "pre", "code", "sup", "sub", "dl", "dt", "dd", "section", "article", "svg", "g", "path", "rect", "circle", "line", "polyline", "polygon", "text", "defs", "lineargradient", "stop", "colgroup", "col"}
    if node.tag not in allowed:
        return children
    attrs = ''
    for key, value in node.attrs.items():
        if value is None:
            if key == 'open': attrs += ' open'
            continue
        if key not in {'id', 'data-theme-name', 'scope', 'class', 'title', 'style', 'href', 'colspan', 'rowspan', 'data-v', 'data-date', 'aria-hidden', 'viewbox', 'xmlns', 'd', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'width', 'height', 'rx', 'ry', 'cx', 'cy', 'r', 'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'points', 'font-size', 'text-anchor', 'opacity', 'offset', 'stop-color', 'transform'}:
            continue
        if key == 'href' and (re.match(r'(?i)\s*(?:javascript|data|vbscript):', value) or any(ord(c)<32 for c in value)):
            continue
        if key == 'style' and re.search(r'(?i)url|expression|@import|behavior|binding|\\', value):
            continue
        attrs += ' ' + ('viewBox' if key=='viewbox' else key) + '="' + escape(value, quote=True) + '"'
    # Legacy headings cannot change the page skeleton.
    tag = 'h3' if node.tag in {'h1','h2'} else node.tag
    return '<' + tag + attrs + '>' + children + ('' if tag in {'br','hr','col'} else '</' + tag + '>')

def _history_day(label, d):
    m = re.search(r'(?:([0-9]{4})-)?([0-9]{2})-([0-9]{2})', label)
    return (m[1] or d[:4]) + m[2] + m[3] if m else None

ANCHORS = {
 'index': {'IDXTEMP':'observations','IDXLEAD':'turning','IDXVOTE':'routes'},
 'cycle': {'VOLSTEP':'volume','LEADIND':'leading','MACHVOTE':'stages','VOTEBOARD':'stages','LADDER':'ladder'},
 'auction': {'SCORECARD':'pool','MACHSCORE':'pool','POOLLEDGER':'settlement','MACHPOOL':'settlement','MACHSIG':'winrate'},
 'lhb': {'FUNDTEMP':'temperature','LHBLEDGER':'ledger','SEATCARD':'seats'},
 'theme': {'THEMEBATTLE':'matrix','6YOU':'matrix','FOURDIM':'matrix','LIFECYCLE':'lifecycle'},
 'logic': {'MACHCHAIN':'chains','MACHRADAR':'earnings','MACHHIST':'hardness'},
 'limitup': {'LEDGER':'ledger','TEMPCARD':'temperature','SCORECARD':'recommendations'},
}

def _leaf_items(value, pointer=""):
    if isinstance(value, dict) and value:
        for key, item in value.items():
            yield from _leaf_items(item, pointer + '/' + str(key).replace('~','~0').replace('/','~1'))
    elif isinstance(value, list) and value:
        for i, item in enumerate(value):
            yield from _leaf_items(item, pointer + '/' + str(i))
    else:
        yield pointer, value

def _add(model, text, section, role, source, pointer, fragment=None):
    key = model['route'] + '-' + sha256((source + '#' + pointer).encode()).hexdigest()[:16]
    ev = 'ev-' + key
    claim = {'id': key, 'role': role, 'text': text if isinstance(text,str) else _dump(text).strip(),
             'section': section, 'evidence_refs': [ev], 'source': source, 'source_pointer': pointer}
    if fragment is not None:
        claim['legacy_html'] = fragment
    model['claims'].append(claim)
    model['evidence'].append({'id':ev,'d':model['d'],'source':source,'pointer':pointer})
    next(s for s in model['sections'] if s['id']==section)['claim_refs'].append(key)
    return key

def _dated(root, filename, d):
    path = root / '_学习' / filename
    if not path.exists():
        return None
    data = _read_json(path)
    if not isinstance(data, dict):
        raise ValueError(filename + ' 必须是 object')
    dates = [data[k] for k in ('日期','date','d') if k in data]
    if not dates or any(str(value) != d for value in dates):
        raise ValueError(filename + ' 日期不匹配/缺失')
    return data

def _facts(model, root):
    d = model['d']
    filename = 'fact_' + d + '.json'
    fact = _dated(root, filename, d)
    facts = fact.get('facts',{}) if fact else {}
    if not fact:
        table_path = root / '_学习' / '_市场温度表.json'
        table = _read_json(table_path) if table_path.exists() else {}
        row = table.get(d, {})
        aliases = {'最高连板':'最高板','成交额亿':'成交额亿'}
        facts = {k: {'value': row.get(k, row.get(aliases.get(k,k))), 'source':'_市场温度表.json#/'+d} for k in [x['id'] for x in model['kpis']]}
        filename = '_市场温度表.json'
    for k in model['kpis']:
        data = facts.get(k['id'], {})
        if not isinstance(data,dict):
            raise ValueError('fact 字段格式错误: ' + k['id'])
        if data.get('quality') == 'conflicted':
            raise ValueError('事实来源冲突: ' + k['id'])
        k['value'] = data.get('value')
        if k['value'] is not None:
            ev = 'fact-' + str(len(model['evidence']))
            model['evidence'].append({'id':ev,'d':d,'source':filename,'pointer':'/facts/'+k['id'] if fact else '/'+d+'/'+k['id'],'value':k['value']})
            k['evidence_refs'] = [ev]
    if model['route']=='cycle' and not model['claims']:
        volume = next(k for k in model['kpis'] if k['id']=='成交额亿')['value']
        if volume is not None:
            _add(model,'当日成交额：'+str(volume)+' 亿','volume','evidence',filename,'/facts/成交额亿/value' if fact else '/'+d+'/成交额亿')
        lead_path = root/'_学习'/'_情绪先行指标.json'
        if lead_path.exists():
            lead = _read_json(lead_path).get(d)
            if lead is not None:
                for pointer,value in _leaf_items(lead,'/'+d):
                    _add(model,value,'leading','evidence',lead_path.name,pointer)
        temp_path = root/'_学习'/'_市场温度表.json'
        temp = _read_json(temp_path).get(d,{}) if temp_path.exists() else {}
        for level,count in temp.get('梯队',{}).items():
            _add(model,str(level)+'板'+str(count)+'家','ladder','evidence',temp_path.name,'/'+d+'/梯队/'+str(level))
        model['limitations'] = ['当日周期判断缺失；仅呈现当日事实，不从其他日期重造决策。']

HEADING_MAP = {
 'index': [('总判断','observations'),('核心观察','observations'),('环境','observations'),('周期与攻防','turning'),('五路看牌','routes'),('五路','routes'),('明日观察','turning'),('拐点预警','turning'),('拐点','turning'),('检查四项','turning'),('总裁决','verdict'),('Master','master'),('深挖','master'),('认知','master'),('指派','master')],
 'cycle': [('量能','volume'),('先行','leading'),('五阶段','stages'),('周期投票','stages'),('连板梯队','ladder'),('梯队','ladder'),('攻防','position'),('深挖','research'),('认知','cognition')],
 'auction': [('竞价选股池','pool'),('当日','pool'),('昨日池','settlement'),('温度','temperature'),('胜率','winrate'),('深挖','research'),('认知','cognition')],
 'lhb': [('今日S/A动向','temperature'),('训练库','research'),('席位荐票','seats'),('席位综合','seats'),('资金温度','temperature'),('台账','ledger'),('分档','tiers'),('深挖','research'),('认知','cognition')],
 'theme': [('荐票','recommendations'),('三级','matrix'),('龙头','matrix'),('生命周期','lifecycle'),('深挖','research'),('认知','cognition')],
 'logic': [('承接Master指派','research'),('产业逻辑·业绩腿命门','recommendations'),('产业逻辑判断','hardness'),('产业逻辑','hardness'),('荐票','recommendations'),('链条','chains'),('产业链','chains'),('逻辑硬度','hardness'),('前置','forward'),('风险日历','forward'),('中报','earnings'),('深挖','research'),('认知','cognition')],
 'limitup': [('荐票','recommendations'),('温度','temperature'),('台账','ledger'),('训练','training'),('质量库','training'),('深挖','research'),('认知','cognition')],
}

def _body_import(model, body, filename):
    route = model['route']
    tree = _Tree(body).root
    section = model['sections'][0]['id']
    counter = 0
    heading = '原首屏补充'
    seen_fragments = {}
    def visit(node):
        nonlocal section, counter, heading
        if isinstance(node,str):
            if node.strip():
                counter += 1
                _add(model,node.strip(),section,'evidence',filename,'/bodies/'+route+'/text/'+str(counter))
            return
        if node.tag == 'comment':
            return
        if node.tag == 'h2':
            heading = node.text().strip()
            # Only the heading label determines mapping; hints can mention other topics.
            label = ''.join(x if isinstance(x,str) else '' for x in node.children).strip() or heading
            if route=='auction' and ('今晨闸门' in label or '今晨初读' in label):
                section = 'pool'
                model['limitations'].append('旧今晨栏已迁盘中作战；仅保留来源审计链接。')
            else:
                match = next((sid for keyword,sid in HEADING_MAP[route] if keyword in label), None)
                if match is None:
                    raise ValueError('旧 HTML 标题未归位: ' + label)
                section = match
            # Preserve scope qualifiers in source heading, not a second physical h2.
            counter += 1
            _add(model,heading,section,'evidence',filename,'/bodies/'+route+'/heading/'+str(counter))
            return
        classes = node.attrs.get('class','').split()
        atomic = node.tag in {'p','li','table','h1','h3','h4','pre','dl'} or any(c in classes for c in ('obs','tli','gauge','chain','kpi','routes','cols','ladbar','stages','posmeter','rowE','hb')) or ('card' in classes and (route!='theme' or not node.has('table')))
        if node.tag == 'details' and not node.has('h2'):
            atomic = True
        if atomic and not node.has('h2'):
            text = node.text().strip()
            if not text:
                return
            counter += 1
            fragment = ('<p>' + escape(text) + '</p>') if 'kpi' in classes else _safe_html(node)
            role = 'cognition' if section=='cognition' or (route=='index' and '认知' in heading) else 'research' if section=='research' else 'observation' if 'obs' in classes else 'evidence'
            # Collapse only identical full imported markup in identical semantic scope.
            identity = (section, fragment)
            if identity in seen_fragments:
                key = seen_fragments[identity]
                claim = next(c for c in model['claims'] if c['id']==key)
                claim.setdefault('source_occurrences',[]).append('/bodies/'+route+'/block/'+str(counter))
                return
            key = _add(model,text,section,role,filename,'/bodies/'+route+'/block/'+str(counter),fragment)
            seen_fragments[identity] = key
            model['claims'][-1]['context'] = heading
            summary = next((x.text().strip() for x in node.children if isinstance(x,_Node) and x.tag=='summary'), '')
            if node.tag=='details' and '存档' in summary and '最新' not in summary:
                model['claims'][-1]['history_ref'] = 'history_sources/' + route + '.html#claim-' + key
                model['claims'][-1]['history_label'] = summary
                model['claims'][-1]['source_day'] = _history_day(summary,model['d'])
            if node.tag=='h1' and not model['hero']['claim_refs']:
                model['hero'] = {'text':text,'claim_refs':[key]}
            return
        for child in node.children:
            visit(child)
    visit(tree)
    model.setdefault('legacy_audit',[]).append({'source':filename,'pointer':'/bodies/'+route,'raw':body})

def _legacy(model, root):
    d, route = model['d'], model['route']
    filename = ('总审' if route=='index' else route+'判断') + '_' + d + '.json'
    data = _dated(root, filename, d)
    first = model['sections'][0]['id']
    evidence_section = 'hardness' if route=='logic' else model['sections'][1]['id']
    if data:
        allowed = ('日期','date','路','来源','结论','五路裁决','总裁决','检查四项','分歧裁决','分歧点','综合深挖','认知迭代','线索跟踪','指派清单','schema_version','昨日战绩验收','环境加权依据','页面合同') if route=='index' else ('日期','date','路','来源','判断','荐票','认知迭代','认知迭代_条目','深挖')
        _keys(data,allowed,filename)
        if '路' in data and data['路']!=route:
            raise ValueError(filename+' 路不匹配')
        for top,value in data.items():
            if top in ('日期','date','路','来源','schema_version','昨日战绩验收','环境加权依据','页面合同'):
                continue
            if route=='index':
                section = {'结论':'verdict','五路裁决':'routes','总裁决':'verdict','检查四项':'turning','分歧裁决':'turning','分歧点':'turning','综合深挖':'master','认知迭代':'master','线索跟踪':'master','指派清单':'master'}[top]
                role = 'cognition' if top=='认知迭代' else 'research' if top=='综合深挖' else 'counterevidence' if top in ('分歧裁决','分歧点') else 'verdict' if top in ('结论','总裁决') else 'evidence'
            else:
                section = 'cognition' if top.startswith('认知迭代') else 'research' if top=='深挖' else first if top=='荐票' else evidence_section
                role = 'cognition' if top.startswith('认知迭代') else 'research' if top=='深挖' else 'observation' if top=='荐票' else 'evidence'
            for pointer,text in _leaf_items(value,'/'+top):
                item_role = 'limitation' if '盲区' in pointer else 'condition' if '可证伪' in pointer else role
                key = _add(model,text,section,item_role,filename,pointer)
                if (top=='结论' and route=='index') or pointer=='/判断/结论':
                    model['claims'][-1]['role']='verdict'
                    model['hero'] = {'text':text,'claim_refs':[key]}
        model['sources'].append(filename)
    body_filename = 'judgment_'+d+'.json'
    judgment = _dated(root,body_filename,d)
    body = (judgment.get('bodies',{}).get(route) or '') if judgment else ''

    if judgment and judgment.get('ticker'):
        model['ticker'] = _safe_html(_Tree(judgment['ticker']).root)
        model['legacy_ticker'] = judgment['ticker']
    if body:
        _body_import(model,body,body_filename)
        model['sources'].append(body_filename)
    if route=='theme':
        _theme(model,root)
    _facts(model,root)
    if model['hero']['claim_refs']:
        key = model['hero']['claim_refs'][0]
        full = model['hero']['text']
        excerpt = re.split(r'[。；;：:\n]',full,maxsplit=1)[0].strip()
        model['hero'] = {'text':excerpt or full,'claim_refs':[], 'summary_of':key}
    optional = {('cycle','research'), ('logic','forward')}
    model['complete'] = bool(data or body) and all(s['claim_refs'] or (route,s['id']) in optional for s in model['sections'])
    if data or body:
        model['limitations'] = ['兼容导入旧判断；原文立场未重新验证。']
        if not model['complete']:
            model['limitations'].append('部分固定栏目缺少当日来源，保留空槽。')
    if body:
        model['limitations'].append('旧 HTML 补充按原栏目职责归位；相似判断仅提示重叠，不作语义删除。')

def _theme(model, root):
    d=model['d']
    leaders = _dated(root,'题材龙头判断_'+d+'.json',d)
    life = _dated(root,'题材生命周期判断_'+d+'.json',d)
    model['theme_matrix'] = []
    if leaders:
        _keys(leaders,('日期','路','龙头标的','判断'),'题材龙头判断')
        names = list(leaders.get('判断',{}))
        names += [n for n in leaders.get('龙头标的',{}) if n not in names]
        for name in names:
            row = {'name':name,'claim_refs':[], 'six_you':None,'data_scope':'原判断聚类名称；不自动等同归位行业'}
            for top in ('判断','龙头标的'):
                if name not in leaders.get(top,{}):
                    continue
                for pointer,value in _leaf_items(leaders[top][name],'/'+top+'/'+name.replace('~','~0').replace('/','~1')):
                    row['claim_refs'].append(_add(model,value,'matrix','evidence','题材龙头判断_'+d+'.json',pointer))
            model['theme_matrix'].append(row)
    six_name = '主流题材6有_'+d+'.json'
    six = _dated(root,six_name,d)
    if six:
        same_names = {row.get('题材(题材聚类口径)'): (i,row) for i,row in enumerate(six.get('题材_聚类口径',[]))}
        for row in model['theme_matrix']:
            row['evidence_refs'] = []
            if row['name'] in same_names:
                index, original = same_names[row['name']]
                row['six_you'] = original.get('得分')
                ev = 'six-' + str(len(model['evidence']))
                model['evidence'].append({'id':ev,'d':d,'source':six_name,'pointer':'/题材_聚类口径/'+str(index)+'/得分','value':row['six_you']})
                row['evidence_refs'].append(ev)
    if life:
        _keys(life,('日期','路','来源','逐线判断','高低切'),'题材生命周期判断')
        for top in ('来源','逐线判断','高低切'):
            if top in life:
                for pointer,value in _leaf_items(life[top],'/'+top):
                    _add(model,value,'lifecycle','condition' if '判据' in pointer else 'evidence','题材生命周期判断_'+d+'.json',pointer)

def _source_record(path,root):
    return {'path':path.relative_to(root).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest()}

def _pure_renderer(route,root,d):
    path=Path(__file__).resolve().parent/('module_render_'+route+'.py')
    # Load pure definitions and literal visual constants only. No legacy top-level
    # filesystem probes, sys.path mutations, local imports, build or CLI entrypoints.
    tree=ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
    body=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef):body.append(node)
        elif isinstance(node,ast.Import) and all(x.name in {'re','os','sys','json','csv'} for x in node.names):body.append(node)
        elif isinstance(node,ast.ImportFrom) and node.module in {'collections','datetime','html'}:body.append(node)
        elif isinstance(node,ast.Assign):
            try:ast.literal_eval(node.value)
            except (ValueError,TypeError):continue
            if any(isinstance(t,ast.Name) and t.id in {'BASE','R','L','CD'} for t in node.targets):continue
            body.append(node)
    module=types.ModuleType('_p1_pure_'+route)
    module.__file__=str(path)
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),module.__dict__)
    module.BASE=str(root);module.R=str(root);module.L=str(root/'_学习')
    reads=[]
    def load(name,date=None):
        filename=name if date is None else name % date
        path=root/'_学习'/filename
        if not path.exists():return None
        if path not in reads:reads.append(path)
        data=_read_json(path)
        if isinstance(data,dict):
            if filename=='链条纵深库.json':
                return {k:v for k,v in data.items() if isinstance(v,dict) and str(v.get('最后更新','99999999'))<=d}
            return {k:v for k,v in data.items() if not re.fullmatch(r'20[0-9]{6}',k) or k<=d}
        return data
    module.load_json=load
    module._source_reads=reads
    return module

def _leading_lights(root,d):
    """Re-render dated source facts in a disposable output dir; never rewrite frozen inputs."""
    import os, tempfile, shutil
    learn=root/'_学习';source=root/'情绪先行指标.py'
    paths=[learn/'_情绪先行指标.json',learn/'_市场温度表.json',source]
    data=_read_json(paths[0])
    data={k:v for k,v in data.items() if k<=d}
    if d not in data:raise ValueError('当日先行指标缺失')
    tree=ast.parse(source.read_text(encoding='utf-8-sig'))
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('card','triggers')]
    if {n.name for n in body}!={'card','triggers'}:raise ValueError('先行指标卡接口缺失')
    with tempfile.TemporaryDirectory(prefix='review-leading-') as tmp:
        shutil.copy2(paths[1],Path(tmp)/paths[1].name)
        ns={'os':os,'json':json,'L':tmp,'__name__':'review_leading_readonly'}
        exec(compile(ast.Module(body=body,type_ignores=[]),str(source),'exec'),ns)
        from contextlib import redirect_stdout
        from io import StringIO
        with redirect_stdout(StringIO()):
            ns['card'](d,data)
        return (Path(tmp)/f'先行指标灯_{d}.html').read_text(encoding='utf-8'),paths


def _components(model,root):
    """Only dated producer artifacts or explicitly read-only renderer functions enter slots."""
    d,route=model['d'],model['route'];learn=root/'_学习'
    model['components']=[]
    def record(key,section,producer,paths,html,anchors=None,issue=None,allow_missing=False):
        sources=[_source_record(p,root) for p in paths if p.exists()]
        valid=bool(html and sources) and not issue
        if valid and re.search(r'<(?:script|iframe|object|embed)\b|\bon[a-z]+\s*=|javascript\s*:',html,re.I):
            valid=False;issue='机器片段包含主动内容'
        clean=re.sub(r'<!--/?[A-Z0-9_]+-->', '', html or '')
        clean=re.sub(r'<h2\b[^>]*>','<h3>',clean).replace('</h2>','</h3>')
        if allow_missing and not valid:
            clean='<div class="card"><span class="mut">当日权威机器源缺失：—</span></div>'
        comp={'id':key,'section':section,'producer':producer,'status':'ok' if valid else 'missing',
              'sources':sources,'html':clean if valid else None,'anchors':anchors or [key],
              'issue':issue or (None if valid else '当日权威机器源缺失'), 'allow_missing':allow_missing}
        if allow_missing and not valid:
            comp['html']=clean
        model['components'].append(comp)
        return comp
    def artifact(key,section,name,producer,anchors=None):
        p=learn/name
        if key=='FUNDTEMP' and not p.exists():
            table=_read_json(learn/'_资金温度.json') if (learn/'_资金温度.json').exists() else []
            rows=[x for x in table if isinstance(x,dict) and str(x.get('日',''))<=d][-5:][::-1] if isinstance(table,list) else []
            if rows:
                cells=lambda x: ''.join('<td>%s</td>'%escape(str(x.get(k,'—'))) for k in ('机构席次','量化席次','知名游资席次','北向席次'))
                html='<div class="card"><b>资金温度 · 分位</b><table><tbody>'+''.join('<tr><td>%s</td>%s<td>%s亿</td><td>%s</td></tr>'%(escape(str(x.get('日',''))[4:6]+'-'+str(x.get('日',''))[6:]),cells(x),escape(str(x.get('总金额亿','—'))),escape(str(x.get('温度分位','—')))) for x in rows)+'</tbody></table></div>'
                return record(key,section,'_资金温度.json', [learn/'_资金温度.json'], html, anchors)
        comp=record(key,section,producer,[p],p.read_text(encoding='utf-8-sig') if p.exists() else None,anchors)
        comp['preserve_html']=True
        return comp
    def generated(key,section,mod,func,files,anchors=None):
        paths=[learn/n for n in files]
        if not all(p.exists() for p in paths):return record(key,section,func,paths,None,anchors)
        try:
            module=_pure_renderer(mod,root,d)
            html=getattr(module,func)(d)
            paths += [p for p in module._source_reads if p not in paths]
            if mod=='theme' and func=='r_chart_matrix' and (root/d/'zt_pool.csv').exists():paths.append(root/d/'zt_pool.csv')
            comp=record(key,section,'module_render_'+mod+'.py:'+func,paths,html,anchors)
            comp['producer_sha256']=sha256(Path(module.__file__).read_bytes()).hexdigest()
            return comp
        except (ValueError,KeyError,TypeError,IndexError,OSError) as exc:
            return record(key,section,func,paths,None,anchors,str(exc))
    def ledger(anchor,section):
        p=learn/('judgment_'+d+'.json')
        try:doc=_read_json(p) if p.exists() else {}
        except (ValueError,OSError) as exc:return record(anchor,section,'冻结 body 锚区',[p],None,issue=str(exc))
        raw=doc.get('bodies',{}).get(route,'')
        match=re.search(r'<!--'+anchor+r'-->(.*?)<!--/'+anchor+r'-->',raw,re.S)
        comp=record(anchor,section,'归档台账脚本注入的冻结 body 锚区',[p],match[1] if match else None,allow_missing=not bool(match))
        if comp['html']:
            comp['html']=_fold_machine_history(comp['html'])
        return comp
    if route=='index':
        table=_read_json(learn/'_市场温度表.json') if (learn/'_市场温度表.json').exists() else {}
        if d in table:generated('IDXTEMP','observations','index','r_mach_temp',['_市场温度表.json'])
        else:record('IDXTEMP','observations','module_render_index.r_mach_temp',[],None)
        if (root/'情绪先行指标.py').exists() and (learn/'_情绪先行指标.json').exists() and (learn/'_市场温度表.json').exists():
            try:
                raw,paths=_leading_lights(root,d)
                comp=record('IDXLEAD','turning','情绪先行指标.py:card（只读事实重渲染）',paths,raw)
                comp['preserve_html']=True
                comp['producer_sha256']=sha256((root/'情绪先行指标.py').read_bytes()).hexdigest()
            except (ValueError,KeyError,TypeError,IndexError,OSError) as exc:
                record('IDXLEAD','turning','情绪先行指标.py:card',[],None,issue=str(exc))
        else:
            artifact('IDXLEAD','turning','先行指标灯_'+d+'.html','情绪先行指标.py')
        artifact('IDXVOTE','routes','周期投票牌_'+d+'.html','周期投票.py')
        _engine_books(model,root,record)
    elif route=='cycle':
        # The approved dual-track contract is structural, not cosmetic:
        # when the dated cycle body exists, its seven LLM sections own the
        # narrative and the machine cards must be absent (golden shape).  The
        # machine cards are only the honest fallback for a missing body.
        judgment = learn / ('judgment_' + d + '.json')
        try:
            cycle_body = (_read_json(judgment).get('bodies', {}).get('cycle', '')
                          if judgment.exists() else '')
        except (ValueError, OSError, TypeError):
            cycle_body = ''
        has_cycle_body = bool(cycle_body and re.search(r'<h2\b[^>]*>\s*一(?:\s|<)', cycle_body))
        if not has_cycle_body:
            table=_read_json(learn/'_市场温度表.json') if (learn/'_市场温度表.json').exists() else {}
            if d in table:generated('VOLSTEP','volume','cycle','r_mach_volstep',['_市场温度表.json'])
            else:record('VOLSTEP','volume','module_render_cycle.r_mach_volstep',[],None)
            artifact('LEADIND','leading','先行指标卡_'+d+'.html','情绪先行指标.py')
            artifact('VOTEBOARD','stages','周期投票牌_'+d+'.html','周期投票.py',['MACHVOTE','VOTEBOARD'])
            if (root/d/'zt_pool.csv').exists():
                comp=generated('LADDER','ladder','cycle','r_mach_ladder',['_市场温度表.json'])
                comp['sources'].append(_source_record(root/d/'zt_pool.csv',root))
            else:record('LADDER','ladder','module_render_cycle.r_mach_ladder',[],None)
    elif route=='auction':
        artifact('SCORECARD','pool','竞价评分卡_'+d+'.html','竞价评分.py',['SCORECARD','MACHSCORE'])
        ledger('POOLLEDGER','settlement')['anchors']=['POOLLEDGER','MACHPOOL']
        artifact('MACHSIG','winrate','竞价评分库卡_'+d+'.html','竞价评分.py')
    elif route=='lhb':
        artifact('SEATCARD','seats','席位荐票卡_'+d+'.html','席位荐票.py')
        artifact('FUNDTEMP','temperature','资金温度卡_'+d+'.html','资金温度.py')
        ledger('LHBLEDGER','ledger')
        _seat_library(model,root,record)
    elif route=='theme':
        generated('THEMEBATTLE','matrix','theme','r_chart_matrix',['主流题材6有_'+d+'.json','_题材四维.json','题材龙头判断_'+d+'.json','题材归位_'+d+'.json','涨停对链条_'+d+'.json'],['THEMEBATTLE','6YOU','FOURDIM'])
        generated('LIFECYCLE','lifecycle','theme','r_chart_lifeaxis',['题材生命周期_'+d+'.json','主流题材6有_'+d+'.json','题材生命周期判断_'+d+'.json','题材龙头判断_'+d+'.json'])
    elif route=='logic':
        generated('MACHCHAIN','chains','logic','r_mach_chain',['链条纵深库.json'])
        comp=generated('MACHRADAR','earnings','logic','r_mach_radar',['中报预增雷达_'+d+'.json'])
        if comp['status']!='ok' and not (learn / ('中报预增雷达_' + d + '.json')).exists():
            comp['allow_missing']=True
            comp['html']='<div class="card"><span class="mut">当日权威机器源缺失：—</span></div>'
        generated('MACHHIST','hardness','logic','r_mach_hist',['_逻辑荐票结算.jsonl'])
    elif route=='limitup':
        artifact('SCORECARD','recommendations','涨停质量荐票卡_'+d+'.html','涨停质量荐票.py')
        artifact('TEMPCARD','temperature','市场温度卡_'+d+'.html','市场温度.py')
        ledger('LEDGER','ledger')
        artifact('QUALITYLIB','training','质量库折叠_'+d+'.html','涨停质量训练.py')
    model['judgment_complete']=model['complete']
    missing=[c['id'] for c in model['components'] if (c['status']!='ok' and not c.get('allow_missing')) or c.get('missing_values')]
    model['machine_complete']=not missing
    if missing:
        model['complete']=False
        model['limitations'].append('当日机器组件未齐：'+'、'.join(missing))
    # A claim is represented in a producer component only if its full exact text is present.
    # Source paths/IDs remain separately reachable; no approximate financial-text matching.
    for comp in model['components']:
        if comp['status']!='ok':continue
        plain=_Tree(comp['html']).root.text()
        for claim in model['claims']:
            if claim['section']!=comp['section']:continue
            if claim['text'] and claim['text'] in plain:
                claim['component_ref']=comp['id']

def _engine_books(model,root,record):
    """Six-book presentation reads engine NAV; no trades/positions/PnL are recomputed."""
    d=model['d'];paths=[];rows='';values={};missing=[]
    for route,title in [('auction','竞价'),('lhb','龙虎榜席位'),('theme','主线题材'),('logic','产业逻辑'),('limitup','涨停质量'),('master','总 Master')]:
        path=root/'_学习/_模拟盘'/route/'净值.json'
        data=_read_json(path) if path.exists() else {}
        nav=data.get(d,{}).get('nav')
        if path.exists():paths.append(path)
        if not isinstance(nav,(int,float)):
            missing.append(route);value='—';width=0;percent='—';direction=''
        else:
            values[route]=nav;value=format(nav,'.6f')
            # Unit formatting only: engine NAV 1.000000 is base 100%; never rebuild NAV.
            percent=format((nav-1)*100,'+.2f')+'%';width=min(48,abs((nav-1)*100)*23);direction='pos' if nav>=1 else 'neg'
        rows+='<div class="hb"><span class="hbl">'+title+'</span><div class="hbt"><i class="'+direction+'" style="width:'+str(round(width,3))+'%"></i></div><span class="hbv">'+percent+'</span><span class="hbs">净值 '+value+'</span></div>'
    raw='<div class="rowE"><div class="card"><h3>六账本 · 当日引擎净值</h3>'+rows+'<p class="mut">日期 '+d+' · 各账本独立核算；读取当日引擎净值，未重算交易收益。</p></div></div>'
    comp=record('ENGINEBOOKS','verdict','模拟盘引擎 / 各路净值.json',paths,raw)
    comp['missing_values']=missing;comp['as_of']=d;comp['engine_nav']=values
    for claim in model['claims']:
        raw=claim.get('legacy_html','')
        if not raw or raw.count('class="hb"')<6:continue
        tree=_Tree(raw).root
        def find(node):
            if not isinstance(node,_Node):return
            if 'hb' in node.attrs.get('class','').split():yield node;return
            for c in node.children:yield from find(c)
        old=list(find(tree));conflicts=[]
        for (route,nav),node in zip(values.items(),old):
            expected=format((nav-1)*100,'+.2f')+'%'
            if expected not in node.text():conflicts.append({'route':route,'engine_nav':nav,'source_text':node.text()})
        claim['legacy_engine_snapshot']=True
        if conflicts:
            model.setdefault('data_conflicts',[]).append({'kind':'engine_books','claim_id':claim['id'],'items':conflicts})
            claim['snapshot_conflict']=True
    if model.get('data_conflicts'):
        model['limitations'].append('原稿六账本战绩与当日引擎不一致；当前值以引擎净值为准，原稿快照保留待核查。')


def _seat_library(model,root,record):
    d=model['d'];path=root/'_学习/_席位分档快照.jsonl'
    rows=[]
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip():
                row=json.loads(line)
                if row.get('日')==d:rows.append(row)
    if not rows:
        record('SEATLIB','tiers','席位分档快照',[path],None);return
    row=rows[-1];window=row.get('窗口');counts=row.get('档分布',{})
    if not window or window.split('~')[-1]>d:
        record('SEATLIB','tiers','席位分档快照',[path],None,issue='窗口日期越界');return
    e=lambda x:escape(str(x))
    raw='<details class="chain"><summary><b>席位分档库</b><span class="chip">'+ '/'.join(k+e(counts[k]) if k!='P' else '预备'+e(counts[k]) for k in ['S','A','B','C','P'] if k in counts)+'</span></summary><div class="inner"><p>窗口'+e(window)+' '+e(row.get('笔数','—'))+'笔 · 当日冻结快照</p>'
    raw+='<p>S榜首：'+e('；'.join(row.get('S榜首',[])))+'</p>'
    current=root/'_学习/_席位分档.json';paths=[path]
    lib=_read_json(current) if current.exists() else None
    if lib and lib.get('更新')==d and lib.get('窗口')==window:
        paths.append(current)
        raw+='<p>'+e(lib.get('口径',''))+'</p><table><tr><th>营业部</th><th>档</th><th>样本</th><th>执1胜率</th><th>执1均涨</th></tr>'
        for name,item in lib.get('席位',{}).items():
            raw+='<tr><th>'+e(name)+'</th>'+''.join('<td>'+e('—' if item.get(k) is None else item[k])+'</td>' for k in ['档','样本','执1胜率','执1均涨'])+'</tr>'
        raw+='</table>'
    else:raw+='<p class="mut">当日逐营业部完整分档表未留存，仅展示当日冻结汇总；没有使用较新窗口补历史。</p>'
    raw+='</div></details>'
    comp=record('SEATLIB','tiers','_席位分档快照.jsonl / 同日分档表',paths,raw)
    comp['window_id']=window;comp['as_of']=d


def _fold_machine_history(html):
    tree=_Tree(html).root
    # Daily source blocks are peers; one archive fold contains their original contents.
    daily=[]
    def collect(node):
        if isinstance(node,_Node):
            if node.tag=='details' and any(isinstance(x,_Node) and x.tag=='summary' for x in node.children):
                daily.append(node);return
            for child in node.children:collect(child)
    collect(tree)
    if len(daily)<2 or 'foldarchive' in html:return html
    history=''.join(_safe_html(x) for x in daily[1:])
    folded=_Tree('<details class="chain foldarchive"><summary><b>更早存档</b><span class="chip">'+str(len(daily)-1)+'条</span></summary><div class="inner">'+history+'</div></details>').root.children[0]
    def replace(node):
        if not isinstance(node,_Node):return
        result=[]
        for child in node.children:
            if child is daily[1]:result.append(folded)
            elif any(child is old for old in daily[2:]):continue
            else:
                replace(child);result.append(child)
        node.children=result
    replace(tree)
    return _safe_html(tree)


def _route_kpis(model,root):
    d,route=model['d'],model['route'];learn=root/'_学习'
    def get(name):
        p=learn/name
        try:
            if not p.exists():return None
            if p.suffix=='.jsonl':return [json.loads(line) for line in p.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
            return _read_json(p)
        except (ValueError,OSError):return None
    market=(get('_市场温度表.json') or {}).get(d,{})
    leading=(get('_情绪先行指标.json') or {}).get(d,{}).get('晋级',{})
    labels={
      'index':['情绪温度 · 250日分位','两市量能 · 亿','涨停 / 跌停','一进二率'],
      'cycle':['两市量能 · 亿','周期投票主判','市场温度 · 250日分位','执行仓位上限'],
      'auction':['一字占比 · 今日池','当日池数','评分Top1','昨日池终结算 · 执1'],
      'lhb':['资金温度 · 分位','机构席次 / 金额亿','席位荐票Top1','昨席位路结算 · 执1'],
      'theme':['最强线宽度','缩圈警报','新增题材线数','昨题材路结算 · 执1'],
      'logic':['A共振池 · 成色A','链条库 · 线数','透支警示 · 均60日','昨产逻结算 · 执1'],
      'limitup':['涨停数 · 剔ST退','最高连板','市场温度 · 250日分位','昨Top5结算 · 执1']}
    values=[None]*4;paths=[]
    if route=='index':
        values=[market.get('温度'),market.get('成交额亿'),str(market['涨停数'])+'/'+str(market['跌停数']) if all(k in market for k in ('涨停数','跌停数')) else None,leading.get('一进二率')]
        paths=['_市场温度表.json','_情绪先行指标.json']
    elif route=='cycle':
        vote=next((x for x in reversed(get('_周期投票台账.jsonl') or []) if x.get('d')==d),{})
        values=[market.get('成交额亿'),vote.get('主判',{}).get('stage'),market.get('温度'),None];paths=['_市场温度表.json','_周期投票台账.jsonl']
    elif route=='auction':
        name='竞价评分_'+d+'.json';data=get(name) or {};rows=data.get('明细')
        if rows:
            top=max(rows,key=lambda x:x.get('竞价分') if x.get('竞价分') is not None else -1)
            values=[str(sum(str(x.get('信号','')).startswith('一字') for x in rows))+'/'+str(len(rows)),len(rows),top.get('名称'),None]
        paths=[name]
    elif route=='lhb':
        rows=get('_资金温度.json') or [];row=next((x for x in rows if str(x.get('日'))==d),{})
        picks=(get('席位荐票_'+d+'.json') or {}).get('top5',[])
        values=[row.get('温度分位'),str(row['机构席次'])+'席 / '+str(row['机构金额亿'])+'亿' if all(k in row for k in ('机构席次','机构金额亿')) else None,picks[0].get('名称') if picks else None,None];paths=['_资金温度.json','席位荐票_'+d+'.json']
    elif route=='theme':
        row=(get('_题材四维.json') or {}).get(d,{})
        widths=[x['宽度'] for x in row.values() if isinstance(x,dict) and x.get('宽度') is not None]
        values=[max(widths) if widths else None,'；'.join(row.get('_警报',[])) or None,None,None];paths=['_题材四维.json']
    elif route=='logic':
        data=get('中报预增雷达_'+d+'.json') or {};lib=get('链条纵深库.json')
        valid={k:v for k,v in (lib or {}).items() if isinstance(v,dict) and str(v.get('最后更新','99999999'))<=d}
        values=[data.get('统计',{}).get('成色A共振'),len(valid) if lib is not None else None,None,None];paths=['中报预增雷达_'+d+'.json','链条纵深库.json']
    elif route=='limitup':
        values=[market.get('涨停数'),market.get('最高板'),market.get('温度'),None];paths=['_市场温度表.json']
    model['kpis']=[]
    for index,(label,value) in enumerate(zip(labels[route],values)):
        refs=[]
        for name in paths:
            p=learn/name
            if p.exists():
                key='kpi-source-'+str(index)+'-'+str(len(refs))
                model['evidence'].append({'id':key,'d':d,'source':'_学习/'+name,'sha256':sha256(p.read_bytes()).hexdigest(),'verification':'file_hash'})
                refs.append(key)
        sparkline=None
        if '量能' in label:
            history=get('_市场温度表.json') or {}
            points=[(day,history[day].get('成交额亿')) for day in sorted(history) if day<=d and isinstance(history[day],dict)][-5:]
            valid=[(day,x) for day,x in points if isinstance(x,(int,float))]
            if len(valid)>1:
                lo=min(x for _,x in valid);hi=max(x for _,x in valid);span=hi-lo or 1
                sparkline={'source':'_学习/_市场温度表.json','points':[{'d':day,'value':x} for day,x in valid],
                           'svg_points':' '.join(str(round(i*180/(len(valid)-1),2))+','+str(round(38-(x-lo)*32/span,2)) for i,(_,x) in enumerate(valid))}
        display=str(value) if value is not None else '—'
        if label=='一进二率' and isinstance(value,(int,float)):display=format(value*100,'.1f')+'%'
        model['kpis'].append({'display':display,'sparkline':sparkline,'id':'slot-'+str(index),'label':label,'value':value,'evidence_refs':refs,
            'gauge':value if '温度' in label and isinstance(value,(int,float)) else None,
            'sub':'当日真源读数' if value is not None else '当日该口径数据缺失，未填补','chip':d[4:6]+'-'+d[6:]})
    # 结构化 judgment 正文可能保留旧单位/旧最高板；这里追加只读真源 ticker，
    # 让哨兵和读者都能看到与当日输入一致的口径，不覆盖原判断正文。
    facts=[]
    if route=='cycle':
        amount=market.get('成交额亿')
        if isinstance(amount,(int,float)):
            wan=('%0.2f'%(amount/10000)).rstrip('0').rstrip('.')
            tier=next((nm for th,nm in [(3.8,'主升2确认'),(3.5,'突破压力'),(3.3,'强修'),(3.0,'过渡'),(0.0,'弱修')] if amount/10000>=th),'弱修')
            facts.append('量能%s万亿·%s'%(wan,tier))
        try:
            with (root/d/'zt_pool.csv').open(encoding='utf-8-sig',newline='') as fh:
                rows=list(csv.DictReader(fh))
            top=max(rows,key=lambda r:(int(float(r.get('连板数',1) or 1)),str(r.get('涨停统计','')))) if rows else None
            if top: facts.append('最高%s板·%s'%(top.get('连板数','—'),top.get('名称','—')))
        except (OSError,ValueError,TypeError): pass
        vote=next((x for x in reversed(get('_周期投票台账.jsonl') or []) if x.get('d')==d),{})
        z=vote.get('主判') or {}
        if z.get('stage') and z.get('direction'): facts.append('主判=%s·%s'%(z['stage'],z['direction']))
    elif route=='limitup':
        names=[]
        try:
            with (root/d/'zt_pool.csv').open(encoding='utf-8-sig',newline='') as fh:
                rows=list(csv.DictReader(fh))
            hi=max((int(float(r.get('连板数',1) or 1)) for r in rows),default=None)
            names=[str(r.get('名称','')) for r in rows if int(float(r.get('连板数',1) or 1))==hi]
            if hi is not None: facts.append('最高%s板·%s'%(hi,'/'.join(names[:5])))
        except (OSError,ValueError,TypeError): pass
        if market.get('涨停数') is not None: facts.append('涨停%s'%market['涨停数'])
        if market.get('温度') is not None: facts.append('温度%s'%market['温度'])
    if facts:
        model['ticker']=(model.get('ticker') or '')+'<span class="source-ticker">'+'｜'.join(escape(str(x)) for x in facts)+'</span>'

def _paper(model,root):
    route = 'master' if model['route']=='index' else model['route']
    path = root / '_学习' / '_模拟盘' / route / ('看板_'+model['d']+'.html')
    if path.exists():
        raw = path.read_text(encoding='utf-8-sig')
        if re.search(r'<(?:script|iframe|object|embed)\b|\bon[a-z]+\s*=|javascript\s*:',raw,re.I):
            raise ValueError('引擎看板含主动内容，须核查源产物: '+path.name)
        # Trusted engine artifact, kept byte-for-byte. Never calculate its financial values here.
        model['paper'] = {'source':path.relative_to(root).as_posix(),'sha256':sha256(raw.encode()).hexdigest(),'html':raw}
    else:
        model['paper'] = None

def _finish(model):
    model['paper_applicable']=model['route']!='cycle'
    model['paper_complete']=not model['paper_applicable'] or model.get('paper') is not None
    if not model['paper_complete']:
        model['complete']=False
        model['limitations'].append('当日引擎看板缺失；收益与持仓显示 —，未手算。')
    if model.get('data_conflicts'):model['complete']=False
    claims = {c["id"]: c for c in model["claims"]}
    placements = {key: [] for key in claims}
    for s in model["sections"]:
        for key in s["claim_refs"]:
            placements[key].append(s["id"])
    missing = [key for key, locations in placements.items() if not locations]
    model["content_coverage"] = {"total": len(claims), "covered": len(claims) - len(missing),
        "unmapped": missing, "items": [{"id": key, "sections": places, "status": "displayed_or_referenced" if places else "unmapped"} for key, places in placements.items()]}
    model["role_overlap"] = [{"id": key, "sections": places, "warning": "同一 claim 多槽位引用；不截断判断。"} for key, places in placements.items() if len(places)>1]
    for c in model['claims']:
        expected = 'master' if model['route']=='index' else c['role']
        if c['role'] in ('cognition','research') and c['section']!=expected:
            model['role_overlap'].append({'id':c['id'],'sections':[c['section']],
                'warning':'角色与栏目职责重叠，保留原文并提示编辑复核。'})
    model["editorial_notes"] = EDITORIAL[model["route"]]
    source_items = []
    for c in model['claims']:
        pointers = [c.get('source_pointer',c['id'])] + c.get('source_occurrences',[])
        for n, pointer in enumerate(pointers):
            source_items.append({'source':c.get('source'), 'pointer':pointer,'claim_id':c['id'],
                'status':'referenced' if n or c.get('history_ref') else 'displayed'})
    model['content_coverage']['source_items'] = source_items
    model['content_coverage']['source_total'] = len(source_items)
    model['machine_anchors'] = {a:c['section'] for c in model.get('components',[]) if c['status']=='ok' for a in c['anchors']}
    if missing:
        model["errors"].append("未归位 source claims: " + ', '.join(missing))
    model["status"] = "fail" if model["errors"] else "ok" if model["complete"] else "degraded"

def _table_views(fragment, seen):
    tree = _Tree(fragment).root
    def visit(node):
        if isinstance(node,str):
            return escape(node)
        if node.tag=='table':
            raw = _safe_html(node)
            key = 'table-' + sha256(raw.encode()).hexdigest()[:16]
            if raw in seen:
                return '<p><a href="#'+seen[raw]+'">回看同一份数据表</a></p>'
            seen[raw] = key
            return '<div id="'+key+'">'+raw+'</div>'
        # Preserve the already-sanitized outer tag; only replace table descendants.
        if not node.has('table'):
            return _safe_html(node)
        if node.tag=='root':
            return ''.join(visit(x) for x in node.children)
        empty = _Node(node.tag,node.attrs.items())
        outer = _safe_html(empty)
        closing = '</'+node.tag+'>'
        if outer.endswith(closing):
            return outer[:-len(closing)] + ''.join(visit(x) for x in node.children) + closing
        return _safe_html(node)
    return visit(tree)

def _shared_cells(fragment,scope,registry):
    """Share only typed rule cells/statistics in the same source date/window.

    Exact definitions stay visible at first use. Stock rows, negations, amounts,
    risk cells, and every occurrence's source claim remain independently present.
    Unclassified prose is deliberately never factored by text similarity.
    """
    root=_Tree(fragment).root
    def definition(node,window,kind):
        raw=_safe_html(node);text=node.text().strip()
        if not text:return
        key=(window,kind,raw)
        if key in registry:
            record=registry[key];record['references']+=1
            label='同窗口席位统计' if kind=='seat-window' else '同口径规则与完整限制'
            node.children=_Tree('<a href="#'+record['id']+'">'+label+'</a>').root.children
        else:
            ident='shared-'+sha256((window+'|'+kind+'|'+raw).encode()).hexdigest()[:16]
            registry[key]={'id':ident,'scope':window,'kind':kind,'text':text,'references':0,'source_html':raw}
            node.children.insert(0,_Node('span',{'id':ident}.items()))
    def walk(node,window):
        if not isinstance(node,_Node):return
        if node.tag=='details':
            summary=next((x for x in node.children if isinstance(x,_Node) and x.tag=='summary'),None)
            if summary:
                explicit=re.search(r'窗口\s*(20[0-9]{6}~20[0-9]{6})',summary.text())
                day=re.search(r'(?<![0-9])(20[0-9]{6})(?![0-9])',summary.text())
                short=re.search(r'(?<![0-9])([01][0-9]-[0-3][0-9])(?![0-9])',summary.text())
                if explicit:window='window:'+explicit.group(1)
                elif day:window=day.group(1)
                elif short:window=scope[:4]+short.group(1).replace('-','')
        if node.tag=='table':
            def rows(n):
                if not isinstance(n,_Node):return
                if n.tag=='tr':yield n;return
                for c in n.children:yield from rows(c)
            table_rows=list(rows(node));indices={}
            for row in table_rows:
                cells=[c for c in row.children if isinstance(c,_Node) and c.tag in ('td','th')]
                if cells and all(c.tag=='th' for c in cells):
                    indices={i:c.text().strip() for i,c in enumerate(cells) if any(k in c.text() for k in ('主导因子','命中规则','次日买入/放弃条件','开盘分桶','席位(滚动战绩)'))}
                    continue
                for index,kind in indices.items():
                    if index<len(cells):definition(cells[index],window,'seat-window' if '滚动战绩' in kind else 'rule:'+kind)
        if node.tag=='p' and re.match(r'^\[[SABCP]\].+滚动执1.+n=',node.text().strip()) and not any(k in node.text() for k in ('净买','净卖')):
            definition(node,window,'seat-window');return
        for child in node.children:walk(child,window)
    walk(root,scope)
    def emit(node):
        if isinstance(node,_Node) and node.tag=='comment':return '<!--'+node.attrs['text']+'-->'
        if isinstance(node,str):return escape(node)
        if node.tag=='root':return ''.join(emit(c) for c in node.children)
        shell=_safe_html(_Node(node.tag,node.attrs.items()))
        tag='h3' if node.tag in ('h1','h2') else node.tag
        closing='</'+tag+'>'
        if shell.endswith(closing):return shell[:-len(closing)]+''.join(emit(c) for c in node.children)+closing
        return shell
    return emit(root)


def _claim_label(claim):
    pointer = claim.get('source_pointer','')
    parts = [p.replace('~1','/').replace('~0','~') for p in pointer.split('/') if p and not p.isdigit()]
    if pointer.startswith('/bodies/'):
        return '旧版原文补充'
    return ' · '.join(parts[-2:]) or claim['role']

def _fold_cognition(html,d,claim_ids):
    """Organize only the cognition section; preserve every claim and its source order."""
    tree=_Tree(html).root
    units=[]
    def collect(node):
        if not isinstance(node,_Node):return
        if node.attrs.get('id') in claim_ids:
            units.append(node);return
        for child in node.children:collect(child)
    collect(tree)
    if len(units)<2:return '<div class="tl">'+html+'</div>'
    # Sources already order equal-date entries newest first. Explicit dates can
    # move a newer historical item ahead without changing any financial text.
    def date(node):
        m=re.search(r'(20[0-9]{2})-?([0-9]{2})-?([0-9]{2})',node.text()[:35])
        if m:return ''.join(m.groups())
        m=re.search(r'([0-9]{2})-([0-9]{2})',node.text()[:15])
        return d[:4]+''.join(m.groups()) if m else d
    ordered=sorted(units,key=date,reverse=True)
    unit_ids={id(n) for n in units}
    def remove(node):
        if not isinstance(node,_Node):return
        node.children=[c for c in node.children if id(c) not in unit_ids]
        for c in node.children:remove(c)
    remove(tree)
    # Flatten pre-existing timeline folds inside source claims, retaining their
    # summary wording as ordinary text, so the section owns exactly one fold.
    def flatten(node):
        if not isinstance(node,_Node):return
        if node.tag=='details' and 'tlfold' in node.attrs.get('class','').split():
            node.tag='div';node.attrs.pop('class',None)
            for c in node.children:
                if isinstance(c,_Node) and c.tag=='summary':c.tag='p'
        for c in node.children:flatten(c)
    for node in ordered:flatten(node)
    return ('<div class="tl">'+_safe_html(tree)+_safe_html(ordered[0])+
        '<details class="chain tlfold"><summary><b>其余认知与原文证据</b><span class="chip">'+str(len(ordered)-1)+
        '条</span></summary><div class="inner">'+''.join(_safe_html(n) for n in ordered[1:])+'</div></details></div>')


def _render(model,contract):
    e = lambda v: escape(str(v), quote=True)
    d, route = model["d"], model["route"]
    nav = '<nav class="navbar"><span class="brand"><span class="logo">盯</span>情绪盯盘台</span><div class="pills">'
    nav += ''.join('<a class="' + ('on' if h == route + '.html' else '') + '" href="' + e(h) + '">' + e(t) + '</a>' for h, t in contract["visual"]["nav"])
    nav += '</div><span class="upd">更新 ' + d + '</span></nav>'
    claims = {c["id"]: c for c in model["claims"]}
    shown = set()
    shown_tables = {}
    shared_definitions = {}
    def reference(key):
        return '<a href="#claim-' + e(key) + '" title="' + e(key) + '">回看完整判断与证据</a>'
    def render_claim(key):
        if key in shown:
            return '<p class="mut">' + reference(key) + '</p>'
        shown.add(key)
        c = claims[key]
        cls = 'tli' if c["role"] == 'cognition' else 'obs' if c["role"] == 'observation' else 'card'
        links = ' '.join('<a href="#evidence-' + e(ref) + '" title="' + e(ref) + '">来源</a>' for ref in c["evidence_refs"])
        if c.get('legacy_engine_snapshot'):
            content='<details class="chain"><summary>原稿六账本快照'+(' · 与当日引擎不同，待核查' if c.get('snapshot_conflict') else ' · 原稿留存')+'</summary><div class="inner">'+_table_views(c['legacy_html'],shown_tables)+'</div></details>'
        elif c.get('component_ref'):
            content = '<p><a href="#component-' + e(c['component_ref']) + '">回看本段权威组件中的原条目</a></p>'
        elif c.get('history_ref'):
            content = '<p><a href="' + e(c['history_ref']) + '">历史来源 · ' + e(c['history_label']) + '</a></p>'
        else:
            content = _table_views(c['legacy_html'],shown_tables) if c.get('legacy_html') else '<p>' + e(c['text']) + '</p>'
        if not c.get('legacy_html') and c.get('source_pointer','').startswith('/') and not c['source_pointer'].startswith(('/bodies/','/pages/')):
            content='<p class="mut">'+e(_claim_label(c))+'</p>'+content
        if not c.get('legacy_html') and c['role']=='observation':
            content='<div class="obs-head"><span class="obs-nm">观察与验证</span></div><div class="obs-watch"><span class="obs-lab">依据</span>'+content+'</div>'
        if c.get('legacy_html') or c['role'] not in ('observation','cognition'):
            cls=''
        role = c.get('role','limitation')
        role_label = ROLE_LABELS.get(role, role)
        role_head = '<div class="claim-head"><span class="claim-role role-' + e(role) + '">' + e(role_label) + '</span><span class="claim-source">' + e(_claim_label(c)) + '</span></div>'
        proof = ('<div class="claim-proof"><span class="proof-label">证据回链</span>' + links + '</div>') if links else ''
        return '<div class="' + cls + '" id="claim-' + e(key) + '" data-role="' + e(role) + '">' + role_head + content + proof + '</div>'
    hero_ids = model["hero"]["claim_refs"]
    hero_id = hero_ids[0] if hero_ids else None
    if hero_id:
        shown.add(hero_id)
    ticker=model.get('ticker','')
    ticker_html='<div class="ticker"><div class="in"><div class="grp">'+ticker+'</div><div class="grp">'+ticker+'</div></div></div>'
    reading_spine = '<nav class="reading-spine" aria-label="阅读顺序"><span class="rs-title">阅读顺序</span><span class="rs-step"><b>01</b>结论</span><span class="rs-arrow">→</span><span class="rs-step"><b>02</b>指标</span><span class="rs-arrow">→</span><span class="rs-step"><b>03</b>分段证据</span><span class="rs-arrow">→</span><span class="rs-step"><b>04</b>来源审计</span></nav>'
    body = ticker_html + reading_spine + '<div class="rowA"><div class="hero"><div class="kick">' + e(model["title"]) + ' · ' + d + ' · ' + e(model["status"]) + '</div><h1' + (' id="claim-' + e(hero_id) + '"' if hero_id else '') + '>' + e(model["hero"]["text"]) + '</h1>'
    change = model["hero"].get("change_ref")
    if change and change != hero_id:
        shown.add(change)
        body += '<p id="claim-' + e(change) + '">' + e(claims[change]["text"]) + '</p>'
    if model['hero'].get('summary_of'):
        body += '<p>' + reference(model['hero']['summary_of']) + ' · 原判完整依据、反证与条件</p>'
    body += '</div>'
    for k in model["kpis"]:
        gauge=''
        if k.get('gauge') is not None:
            gauge='<div class="gauge"><div class="gtrack"><i class="gmark" style="left:'+e(k['gauge'])+'%"></i></div><div class="gl"><span>冷</span><span>中性</span><span>热</span></div></div>'
        spark='<svg class="spark" viewBox="0 0 180 44" aria-hidden="true"><polyline fill="none" stroke="#e8a33d" stroke-width="2" points="'+e(k['sparkline']['svg_points'])+'"/></svg>' if k.get('sparkline') else ''
        body += '<div class="kpi"><div class="top"><span class="ico"><svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M2 14V10M7 14V6M12 14V2" fill="none" stroke="currentColor" stroke-width="2"/></svg></span><span class="chip2 c-half">'+e(k.get('chip',d))+'</span></div><span class="lab">'+e(k['label'])+'</span><span class="big">'+e(k.get('display','—' if k['value'] is None else k['value']))+'</span>'+gauge+spark+'<span class="sub2">'+e(k.get('sub','当日来源'))+'</span></div>'
    body += '</div>'
    if model.get('paper'):
        body += '<!--PAPERTRADE-->\n' + model['paper']['html'] + '\n<!--/PAPERTRADE-->\n'
    elif model.get('paper_applicable',True):
        body += '<div class="card">模拟盘当日引擎看板缺失：—</div>'
    if model["limitations"]:
        body += '<div class="card"><b>数据边界</b><ul>' + ''.join('<li>' + e(x) + '</li>' for x in model["limitations"]) + '</ul></div>'
    for number, s in zip('一二三四五六七', model["sections"]):
        body += '<section id="' + e(s["id"]) + '"><h2>' + number + ' ' + e(s["title"]) + '</h2>'
        inner = ''
        for comp in model.get('components',[]):
            if comp['section']!=s['id']:continue
            if comp['status']=='ok':
                if comp.get('preserve_html'):
                    fragment=comp['html']
                    def register(node):
                        if not isinstance(node,_Node):return
                        if node.tag=='table':shown_tables[_safe_html(node)]='component-'+comp['id']
                        for child in node.children:register(child)
                    register(_Tree(fragment).root)
                else:fragment=_table_views(comp['html'],shown_tables)
                inner += '<div id="component-'+e(comp['id'])+'">'+''.join('<!--'+a+'-->' for a in comp['anchors'])+fragment+''.join('<!--/'+a+'-->' for a in reversed(comp['anchors']))+'</div>'
            else:
                if comp.get('allow_missing') and comp.get('html'):
                    inner += '<div id="component-'+e(comp['id'])+'">'+''.join('<!--'+a+'-->' for a in comp['anchors'])+comp['html']+''.join('<!--/'+a+'-->' for a in reversed(comp['anchors']))+'</div>'
                else:
                    inner += '<div class="card"><b>当日组件缺失</b><p>'+e(comp['id']+'：'+str(comp['issue']))+'</p></div>'
        if s['id']=='matrix' and model['route']=='theme' and not any(c['id']=='THEMEBATTLE' and c['status']=='ok' for c in model.get('components',[])):
            inner += '<p class="mut">判断范围：原龙头判断全部条目。数据口径：原名聚类与归位行业分开核对；6有未取得同名原值时显示 —。</p><div class="card"><table id="theme-judgment-matrix"><thead><tr><th>原判断题材</th><th>龙头与判断</th><th>6有</th></tr></thead><tbody>'
            for row in model.get('theme_matrix',[]):
                inner += '<tr data-theme-name="' + e(row['name']) + '"><th scope="row">' + e(row['name']) + '</th><td>' + ''.join(render_claim(key) for key in row['claim_refs']) + '</td><td>' + e('—' if row['six_you'] is None else str(row['six_you'])+'/6') + '</td></tr>'
            if not model.get('theme_matrix'):
                inner += '<tr><td colspan="3">当日结构化逐线矩阵未提供，判断证据列于下方；不推测归位。</td></tr>'
            inner += '</tbody></table></div>'
        pending=''
        for key in s['claim_refs']:
            if key in shown and any(key in row['claim_refs'] for row in model.get('theme_matrix',[])):continue
            c=claims[key]
            if not c.get('legacy_html') and c['role'] not in ('observation','cognition'):
                pending+=render_claim(key)
            else:
                if pending:inner+='<div class="card">'+pending+'</div>';pending=''
                inner+=render_claim(key)
        if pending:inner+='<div class="card">'+pending+'</div>'
        if not inner:
            inner = '<div class="card">当日材料缺失，保留栏目等待补齐。</div>'
        anchors = [] # Real producer components own their anchors above.
        inner = ''.join('<!--'+a+'-->' for a in anchors) + inner + ''.join('<!--/'+a+'-->' for a in reversed(anchors))
        inner = _shared_cells(inner,d,shared_definitions)
        body += (_fold_cognition(inner,d,{'claim-'+c['id'] for c in model['claims'] if c['section']=='cognition' and c['role']=='cognition'}) if s["id"] == 'cognition' else inner) + '</section>'
    model['shared_definitions'] = list(shared_definitions.values())
    body += '<details class="chain"><summary>编辑说明与来源审计</summary><div class="inner"><ul>'
    body += ''.join('<li>' + e(note) + '</li>' for note in model["editorial_notes"]) + '</ul>'
    for ev in model["evidence"]:
        body += '<div id="evidence-' + e(ev["id"]) + '"><b>' + e(ev["id"]) + '</b><pre>' + e(_dump(ev)) + '</pre></div>'
    body += '<p><a href="audit/' + e(route) + '.json">原文审计与来源条目</a> · <a href="models/' + e(route) + '.json">结构化页面模型</a></p></div></details>'
    return '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>' + e(model["title"]) + '</title><style>' + _page_css(contract) + '</style></head><body data-route="' + e(route) + '" data-template-version="' + e(contract["template_version"]) + '">' + nav + '<div class="wrap">' + body + contract["visual"]["foot"] + '</div>' + VISUAL_JS + '</body></html>\n'

def build_site(root: Path, d: str, out: Path) -> dict:
    """Render only to caller-owned staging out; never publish or edit history."""
    try:
        _check_date(d)
        root = Path(root).resolve()
        out = Path(out).resolve()
        if out==root or root.is_relative_to(out) or any(out.is_relative_to(root / name) for name in ('_学习','_契约','tests')):
            raise ValueError('out 不得覆盖输入目录/祖先目录')
        contract = _contract()
        models = {r: build_page_model(root, d, r) for r in contract["routes"]}
        errors = [r + ': ' + err for r, m in models.items() for err in m["errors"]]
        if errors:
            return {"status": "fail", "errors": errors, "d": d}
        out = Path(out).resolve()
        (out / "models").mkdir(parents=True, exist_ok=True)
        (out / 'audit').mkdir(exist_ok=True)
        (out / 'history_sources').mkdir(exist_ok=True)
        pages = {}
        for r, m in models.items():
            path = out / (r + '.html')
            path.write_text(_render(m, contract), encoding="utf-8", newline="\n")
            (out / "models" / (r + '.json')).write_text(_dump(m), encoding="utf-8", newline="\n")
            audit = {'schema_version':1,'d':d,'route':r,'legacy_bodies':m.get('legacy_audit',[]),
                     'claims':m['claims'],'content_coverage':m['content_coverage'],'legacy_ticker':m.get('legacy_ticker')}
            (out/'audit'/(r+'.json')).write_text(_dump(audit),encoding='utf-8',newline='\n')
            history = [c for c in m['claims'] if c.get('history_ref')]
            if history:
                contents = ''.join('<article id="claim-'+escape(c['id'])+'">'+c['legacy_html']+'</article>' for c in history)
                html = '<!DOCTYPE html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>历史来源摘录</title><style>'+_page_css(contract)+'</style><body><div class="wrap"><p>仅供追溯本次导入的历史源块；原发出版未更改。</p><a href="../'+r+'.html">返回当日页</a>'+contents+'</div></body></html>'
                (out/'history_sources'/(r+'.html')).write_text(html,encoding='utf-8',newline='\n')
            pages[r] = str(path)
        return {"status": "ok" if all(m["complete"] for m in models.values()) else "degraded",
                "errors": [], "d": d, "pages": pages,
                "page_status": {r: m["status"] for r, m in models.items()}}
    except (ValueError, TypeError, OSError) as exc:
        return _fail(d, exc)
