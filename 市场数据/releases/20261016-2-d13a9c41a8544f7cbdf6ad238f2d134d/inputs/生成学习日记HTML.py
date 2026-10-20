# -*- coding: utf-8 -*-
"""生成学习日记HTML.py —— 把 _学习/日记.md 渲染成 学习日记页
结构(2026-07-07v4):
  ① 「当日记录入口」: 最新日期块(5维度渲染)
  ② 「学习笔记」板块: 历史日期块归档(5维度渲染)
  ③ 「验证台账」: 由 verifier.py 生成的实核块(独立段, 表格渲染)
输出 复盘/学习日记.html。用法: python 生成学习日记HTML.py"""
import os, glob, re, html, datetime, json, collections
BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

# 5 维度顺序与配色(标签) + 第6项「复盘总结」闭环区块(loop 标记)
DIMS = [
    ("一、盘面观察", "盘面观察", "#4361ee", False),
    ("二、系统验证", "系统验证", "#e63946", False),
    ("三、认知迭代", "认知迭代", "#2a9d8f", False),
    ("四、升级反馈点", "升级反馈点", "#f4a261", False),
    ("五、认知追踪", "认知追踪", "#9b5de5", False),
    ("六、复盘总结", "复盘总结(T+1回顾)", "#06d6a0", True),
]

def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s

def render_sub(title, body_lines):
    """渲染一个 ### 子章节。支持正文 + 嵌套 #### 子章节（分析体系）。"""
    # 按 #### 拆成若干组：{sub: None 或 子章节标题, lines: [...]}
    groups = [{"sub": None, "lines": []}]
    for ln in body_lines:
        st = ln.strip()
        if not st:
            continue
        if st.startswith("#### "):
            groups.append({"sub": st[4:].strip(), "lines": []})
        else:
            groups[-1]["lines"].append(ln)

    def emit(items, paras):
        s = []
        for p in paras:
            s.append("<p>%s</p>" % md_inline(p))
        if items:
            s.append("<ul>")
            for it in items:
                s.append("<li>%s</li>" % md_inline(it))
            s.append("</ul>")
        return s

    out = ["<div class=sub>"]
    out.append("<div class=dimtag>%s</div>" % html.escape(title))
    for g in groups:
        items, paras = [], []
        for ln in g["lines"]:
            s2 = ln.strip()
            if s2.startswith("- ") or s2.startswith("· "):
                items.append(s2[2:].strip())
            elif s2:
                paras.append(s2)
        if g["sub"] is not None:
            out.append("<div class=subsub>")
            out.append("<div class=subsubh>%s</div>" % md_inline(g["sub"]))
        out.extend(emit(items, paras))
        if g["sub"] is not None:
            out.append("</div>")
    out.append("</div>")
    return "\n".join(out)

def parse_block(block):
    lines = block.splitlines()
    header = lines[0].strip() if lines else ""
    meta = ""
    i = 1
    if i < len(lines) and lines[i].strip().startswith(">"):
        meta = lines[i].strip()[1:].strip()
        i += 1
    subs = []
    cur_title, cur_body = None, []
    for ln in lines[i:]:
        s = ln.rstrip()
        if s.startswith("### "):
            if cur_title is not None:
                subs.append((cur_title, cur_body))
            cur_title = s[4:].strip()
            cur_body = []
        elif s.startswith("## "):
            continue
        else:
            cur_body.append(s)
    if cur_title is not None:
        subs.append((cur_title, cur_body))
    return header, meta, subs

def render_day(header, meta, subs, highlight=False):
    cls = "card day cur" if highlight else "card day"
    H = ["<div class='%s'>" % cls]
    H.append("<h3 class=dayh>%s</h3>" % md_inline(header[3:] if header.startswith("## ") else header))
    if meta:
        H.append("<div class=meta>%s</div>" % md_inline(meta))
    rendered = set()
    for key, label, color, is_loop in DIMS:
        for title, body in subs:
            # loop 区块精确匹配（含"T+1 回顾"唯一标识），避免误吞同名前缀旧块
            matched = ("T+1 回顾" in title) if is_loop else title.startswith(key[:2])
            if matched:
                if is_loop:
                    H.append(render_loop(body))
                else:
                    H.append("<div class=subwrap style='border-left:4px solid %s'>" % color)
                    H.append(render_sub(label, body))
                    H.append("</div>")
                rendered.add(title)
                break
    for title, body in subs:
        if title not in rendered:
            H.append("<div class=subwrap>")
            H.append(render_sub(title, body))
            H.append("</div>")
    H.append("</div>")
    return "\n".join(H)

def render_loop(body):
    """渲染「六、复盘总结（T+1 回顾）」闭环区块。
    待复盘(含'待 T+1')→灰框+⏳徽标; 已回填→青绿实框+（1）复盘总结 /（2）验证 子段。"""
    raw = [l.rstrip() for l in body]
    status, content = "", []
    for l in raw:
        if l.strip() == "---":
            continue
        st = l.lstrip()
        if st.startswith(">") and not status:
            status = st[1:].strip()
            continue
        content.append(l)
    text = "\n".join(content).strip()
    pending = ("待 T+1" in text) or ("待 T+1" in status)
    if pending:
        m = re.search(r"待 T\+1（(\d{4}-\d{2}-\d{2})）", status + text)
        tgt = m.group(1) if m else ""
        badge = ("⏳ 待 %s 复盘验证" % tgt) if tgt else "⏳ 待 T+1 复盘验证"
        out = ["<div class='loopbox pending'>",
               "<div class=looptag>🔄 复盘总结区块（T+1 回顾）</div>",
               "<div class=loopbadge>%s</div>" % badge]
        # 渲染(1)/(2)占位提示, 让 T+1 清楚需回填什么
        parts, cur = [], None
        for ln in content:
            s = ln.rstrip()
            if s.startswith("#### "):
                if cur:
                    parts.append(cur)
                cur = [s[4:].strip(), []]
            elif cur is not None:
                cur[1].append(s)
        if cur:
            parts.append(cur)
        for subt, subb in parts:
            out.append("<div class=loopsub><span class=loopsubh>%s</span></div>" % md_inline(subt))
            out.append("<div class=loopmut>" + render_sub(subt, subb) + "</div>")
        out.append("<div class=loopmut style='margin-top:6px'>本区块在 T+1 当日复盘时回填「复盘总结」与「验证」，完成「记录 → 次日验证」闭环。</div>")
        out.append("</div>")
        return "\n".join(out)
    parts, cur = [], None
    for ln in content:
        s = ln.rstrip()
        if s.startswith("#### "):
            if cur:
                parts.append(cur)
            cur = [s[4:].strip(), []]
        elif cur is not None:
            cur[1].append(s)
    if cur:
        parts.append(cur)
    out = ["<div class='loopbox'>", "<div class=looptag>🔄 复盘总结区块（T+1 回顾）</div>"]
    if status:
        out.append("<div class=loopstatus>%s</div>" % md_inline(status))
    for subt, subb in parts:
        out.append("<div class=loopsub><span class=loopsubh>%s</span></div>" % md_inline(subt))
        out.append(render_sub(subt, subb))
    out.append("</div>")
    return "\n".join(out)

def is_day_block(b):
    return bool(re.match(r"^##\s+\d{4}-\d{2}-\d{2}\b", b.strip()))

def render_md_table(rows):
    def cells(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]
    data = [cells(r) for r in rows if r.strip().startswith("|")]
    if not data:
        return ""
    head = data[0]
    body = data[2:] if len(data) > 2 else []
    out = ["<table class=ledg>"]
    out.append("<tr>" + "".join("<th>%s</th>" % md_inline(c) for c in head) + "</tr>")
    for r in body:
        out.append("<tr>" + "".join("<td>%s</td>" % md_inline(c) for c in r) + "</tr>")
    out.append("</table>")
    return "\n".join(out)

def render_ledger(block):
    lines = block.splitlines()
    title = lines[0].strip()[3:].strip() if lines and lines[0].startswith("## ") else "验证台账"
    meta = ""
    i = 1
    if i < len(lines) and lines[i].strip().startswith(">"):
        meta = lines[i].strip()[1:].strip(); i += 1
    out = ["<div class=card>"]
    out.append("<h3 class=dayh style='color:#9b5de5'>%s</h3>" % md_inline(title))
    if meta:
        out.append("<div class=meta style='background:#f6f0ff'>%s</div>" % md_inline(meta))
    buf, table_buf, in_table = [], [], False
    def flush_para():
        if buf:
            out.append("<p>%s</p>" % md_inline(" ".join(buf).strip())); buf.clear()
    def flush_table():
        if table_buf:
            out.append(render_md_table(table_buf)); table_buf.clear()
    for ln in lines[i:]:
        s = ln.rstrip()
        if s.strip().startswith("|") and ("---" in s):
            in_table = True; table_buf.append(s); continue
        if in_table:
            if s.strip().startswith("|"):
                table_buf.append(s); continue
            else:
                in_table = False; flush_table()
        if not s.strip():
            flush_para(); continue
        if re.match(r"^\d+\.\s", s.strip()):
            flush_para()
            out.append("<p style='margin:4px 0'>%s</p>" % md_inline(s.strip())); continue
        if s.strip().startswith("- "):
            flush_para()
            out.append("<p style='margin:3px 0 3px 14px'>• %s</p>" % md_inline(s.strip()[2:].strip())); continue
        buf.append(s.strip())
    flush_para(); flush_table()
    out.append("</div>")
    return "\n".join(out)

def render_ledger_json():
    """渲染 verifier.py 输出的 _验证台账.json 为表格（40项 ✓/✗/△ 实核）。"""
    p = os.path.join(BASE, "_学习", "_验证台账.json")
    if not os.path.isfile(p):
        return ""
    try:
        data = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        return "<div class=card><div class=mut>验证台账读取失败: %s</div></div>" % html.escape(str(e))
    if not isinstance(data, list) or not data:
        return ""
    cnt = collections.Counter(x.get("状态", "?") for x in data)
    n_ok = cnt.get("✓", 0); n_err = cnt.get("✗", 0); n_pend = cnt.get("△", 0)
    out = ["<div class=card>"]
    out.append("<h3 class=dayh style='color:#9b5de5'>验证台账（verifier.py 系统性实核 · 共 %d 项）</h3>" % len(data))
    out.append("<div class=meta style='background:#f6f0ff'>✓ 已验证 <b style='color:#06a88a'>%d</b> · ✗ 原错已修正 <b style='color:#e63946'>%d</b> · △ 待核/待真机 <b style='color:#b26a00'>%d</b> —— 每日管道自动实核，不嘴上验证。</div>" % (n_ok, n_err, n_pend))
    out.append("<table class=ledg>")
    out.append("<tr><th>ID</th><th>维度</th><th>技术点 claim</th><th>状态</th><th>实测</th><th>备注</th></tr>")
    cmap = {"✓": "#06a88a", "✗": "#e63946", "△": "#b26a00"}
    for x in data:
        st = x.get("状态", "?")
        color = cmap.get(st, "#555")
        out.append("<tr>")
        out.append("<td>%s</td>" % html.escape(str(x.get("id", ""))))
        out.append("<td>%s</td>" % html.escape(str(x.get("维度", ""))))
        out.append("<td>%s</td>" % md_inline(str(x.get("claim", ""))))
        out.append("<td style='color:%s;font-weight:700'>%s</td>" % (color, html.escape(st)))
        out.append("<td>%s</td>" % md_inline(str(x.get("实测", ""))))
        out.append("<td>%s</td>" % md_inline(str(x.get("备注", ""))))
        out.append("</tr>")
    out.append("</table>")
    out.append("</div>")
    return "\n".join(out)

def main():
    dp = os.path.join(BASE, "_学习", "日记.md")
    if not os.path.isfile(dp):
        print("无日记"); return
    txt = open(dp, encoding="utf-8").read()
    blocks = re.split(r"(?=^## (?!#))", txt, flags=re.M)  # 仅切 `## `（日期块），不切 `###`/`####` 子章节
    day_blocks = [b for b in blocks if is_day_block(b)]
    if not day_blocks:
        print("无日记块"); return

    # 复盘闭环状态: 统计每块「六、复盘总结（T+1 回顾）」是否已回填
    loop_done, loop_pending = 0, 0
    for b in day_blocks:
        _, _, subs = parse_block(b)
        for t, body in subs:
            if "T+1 回顾" in t:  # 精确匹配新增闭环区块，不误算旧块
                if "待 T+1" in "\n".join(body):
                    loop_pending += 1
                else:
                    loop_done += 1
                break

    H = []
    H.append("<!doctype html><html lang=zh><head><meta charset=utf-8>")
    H.append("<meta name=viewport content='width=device-width,initial-scale=1'>")
    H.append("<title>学习日记</title><style>:root{color-scheme:light}")
    H.append("body{font-family:-apple-system,'Microsoft YaHei',sans-serif;background:#f5f6f8;color:#1a1a2e;margin:0;padding:16px;font-size:14px}")
    H.append(".wrap{max-width:960px;margin:0 auto}")
    H.append(".card{background:#fff;border-radius:12px;padding:14px 20px;margin:12px 0;box-shadow:0 1px 4px rgba(0,0,0,.06)}")
    H.append("h1{font-size:22px;margin:0 0 4px}")
    H.append("h2.sec{font-size:17px;color:#222;margin:22px 0 6px;padding-left:10px;border-left:5px solid #4361ee}")
    H.append(".day{border:1px solid #eef}")
    H.append(".day.cur{box-shadow:0 2px 10px rgba(67,97,238,.18);border-color:#4361ee}")
    H.append(".dayh{font-size:16px;color:#4361ee;margin:2px 0 4px}")
    H.append(".meta{color:#555;font-size:12.5px;background:#f0f3ff;padding:6px 10px;border-radius:6px;margin-bottom:8px}")
    H.append(".subwrap{margin:10px 0;padding:2px 0 2px 12px}")
    H.append(".sub{margin:0}")
    H.append(".dimtag{display:inline-block;font-size:12px;font-weight:700;color:#fff;background:#4361ee;padding:2px 10px;border-radius:20px;margin-bottom:4px}")
    H.append(".sub p{margin:3px 0;line-height:1.6}")
    H.append(".sub ul{margin:4px 0 4px 18px;padding:0} .sub li{margin:3px 0;line-height:1.65}")
    H.append(".subsub{margin:8px 0 4px;padding:4px 0 4px 12px;border-left:3px solid #c9d2ff;background:#fafbff}")
    H.append(".subsubh{font-size:13px;font-weight:700;color:#4361ee;margin-bottom:2px}")
    H.append(".nav a{display:inline-block;padding:6px 14px;background:#4361ee;color:#fff;border-radius:8px;text-decoration:none;font-size:13px;margin-right:8px}")
    H.append(".nav a.alt{background:#6c757d}")
    H.append(".mut{color:#888;font-size:12px}")
    H.append("b{color:#e63946}")
    H.append(".ledg{border-collapse:collapse;width:100%;margin:8px 0;font-size:13px}")
    H.append(".ledg th,.ledg td{border:1px solid #e3e3ef;padding:6px 8px;text-align:left;vertical-align:top}")
    H.append(".ledg th{background:#f0f3ff;color:#333}")
    H.append(".loopbox{margin:14px 0;padding:12px 14px;border:2px dashed #06d6a0;border-radius:10px;background:#f3fbf8}")
    H.append(".loopbox.pending{opacity:.85;background:#f7f7f9;border-color:#cfd3d8}")
    H.append(".looptag{font-size:12.5px;font-weight:700;color:#06a88a;margin-bottom:6px}")
    H.append(".loopbadge{display:inline-block;background:#fff4e0;color:#b26a00;padding:4px 12px;border-radius:20px;font-size:13px;font-weight:700;margin:2px 0 6px}")
    H.append(".loopmut{color:#888;font-size:12px;line-height:1.6}")
    H.append(".loopstatus{color:#555;font-size:12px;background:#eafaf4;padding:4px 8px;border-radius:6px;margin:2px 0 6px}")
    H.append(".loopsub{margin:8px 0}")
    H.append(".loopsubh{display:inline-block;font-size:13px;font-weight:700;color:#089b7d;margin-bottom:2px}")
    H.append("</style></head><body><div class=wrap>")
    H.append("<div class=nav><a href='latest.html'>← 回当日复盘面板</a><a class=alt href='集合竞价训练.html'>集合竞价训练</a><a class=alt href='龙虎榜训练.html'>龙虎榜训练</a></div>")
    H.append("<h1>📓 学习日记（5 维度深度框架 · 已系统性实核）</h1>")
    H.append("<div class=mut>结构：① 当日记录入口（最新日期块，5 维度 + 复盘总结闭环区块）② 学习笔记（历史日期块归档）③ 验证台账（verifier.py 实核）。共 %d 字。</div>" % len(txt))
    H.append("<div class=mut>🔄 复盘闭环状态：已回填 <b style='color:#06a88a'>%d</b> / 待 T+1 复盘 <b style='color:#b26a00'>%d</b> —— 待复盘块在 T+1 当日复盘时回填「复盘总结 + 验证」。</div>" % (loop_done, loop_pending))

    # ① 当日记录入口 = 最新日期块(末尾)
    latest_block = day_blocks[-1]
    lh, lm, ls = parse_block(latest_block)
    H.append("<h2 class=sec>一、当日记录入口（最新）</h2>")
    H.append(render_day(lh, lm, ls, highlight=True))

    # ② 学习笔记(历史日期块, 倒序)
    H.append("<h2 class=sec>二、学习笔记（历史归档）</h2>")
    hist = day_blocks[:-1]
    if not hist:
        H.append("<div class=card><div class=mut>（暂无历史归档，最新块即上方「当日记录入口」）</div></div>")
    else:
        for b in reversed(hist):
            h, m, s = parse_block(b)
            H.append(render_day(h, m, s, highlight=False))

    # ③ 验证台账(从 verifier.py 的 _验证台账.json 渲染, 独立段不混入日期块)
    ledger_html = render_ledger_json()
    if ledger_html:
        H.append("<h2 class=sec style='border-left-color:#9b5de5'>三、验证台账（系统性实核）</h2>")
        H.append(ledger_html)

    H.append("<div class=mut style='text-align:center;margin:16px'>学习日记 · 生成于 %s</div>" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    H.append("</div></body></html>")
    outp = os.path.join(BASE, "复盘", "学习日记.html")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    open(outp, "w", encoding="utf-8").write("\n".join(H))
    print("生成:", outp, "| 当日入口:", lh[:40] if len(lh)>40 else lh, "| 历史归档块:", len(hist), "| 验证台账: 已渲染(%d项)" % len(json.load(open(os.path.join(BASE,"_学习","_验证台账.json"),encoding="utf-8")) if os.path.isfile(os.path.join(BASE,"_学习","_验证台账.json")) else 0))

if __name__ == "__main__":
    main()
