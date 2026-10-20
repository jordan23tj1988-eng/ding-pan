# -*- coding: utf-8 -*-
"""把 `_学习/_运维/可观测性_最新.json` 渲染成只读运维面板。

数据只来自 observability.py，不在渲染层重算任何指标。
"""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(r"D:\股票数据\市场数据")
SRC = ROOT / "_学习" / "_运维" / "可观测性_最新.json"
OUT_DIR = ROOT / "_诊断"


def esc(v) -> str:
    return html.escape("" if v is None else str(v))


def pct(v) -> str:
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def badge(text: str, kind: str = "muted") -> str:
    return f'<span class="tag {kind}">{esc(text)}</span>'


def card(label: str, value: str, sub: str = "", kind: str = "") -> str:
    return (f'<div class="card"><div class="kpi {kind}">{value}</div>'
            f'<div class="label">{esc(label)}</div><div class="sub">{sub}</div></div>')


def table(headers: list[str], rows: list[list[str]], empty: str = "无数据") -> str:
    if not rows:
        return f'<p class="muted">{esc(empty)}</p>'
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build() -> Path:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    guard = d.get("guard") or {}
    issues = guard.get("issues") or []
    assigns = d.get("assignments") or {}
    counts = assigns.get("counts") or {}
    cog = d.get("cognition") or {}
    pred = d.get("predictions") or {}
    totals = pred.get("totals") or {}
    fresh = d.get("freshness") or {}
    releases = d.get("releases") or {}
    cron = d.get("cron") or {}
    stage = guard.get("staging") or {}
    weekly = d.get("ledger_weekly") or {}
    weekly_routes = weekly.get("routes") or {}

    issue_rows = []
    for x in issues:
        issue_rows.append([badge(x.get("kind", "issue"), "bad"), esc(x.get("detail", "")), esc(x.get("day", ""))])
    issue_html = table(["类型", "详情", "日期"], issue_rows, "无告警")

    fresh_rows = []
    for name, info in (fresh.get("files") or {}).items():
        if name == "daily_dir":
            continue
        ok = info.get("exists")
        fresh_rows.append([esc(name), badge("在位" if ok else "缺失", "ok" if ok else "bad"),
                           esc(info.get("mtime") or "—")])
    day_dir = (fresh.get("files") or {}).get("daily_dir") or {}
    fresh_rows.append(["当日目录", badge("在位" if day_dir.get("exists") else "缺失",
                                      "ok" if day_dir.get("exists") else "bad"),
                       f'{esc(day_dir.get("files", 0))} 个文件'])

    owner_rows = []
    for owner, c in sorted((assigns.get("by_owner") or {}).items()):
        owner_rows.append([esc(owner), esc(c.get("critical", 0)), esc(c.get("warn", 0)),
                           esc(c.get("open", 0)), esc(c.get("done", 0))])

    cog_rows = [[esc(k), esc(v)] for k, v in sorted((cog.get("counts") or {}).items())]

    days = pred.get("days") or []
    coverage = pred.get("coverage")
    if totals.get("rows"):
        coverage = (totals.get("machine") or 0) / totals["rows"]
    bad_days = sorted([x for x in days if isinstance(x.get("coverage"), (int, float))],
                      key=lambda x: x.get("coverage", 0))[:8]
    pred_rows = [[esc(x.get("d")), esc(x.get("rows")), esc(x.get("machine")),
                  pct(x.get("coverage")), pct(x.get("judgeable")),
                  esc((x.get("status") or {}).get("ambiguous", 0))] for x in bad_days]

    release_rows = [[esc(x.get("id")), esc(x.get("created_at", "")[:19]),
                     badge(x.get("release_state") or "legacy",
                           "ok" if x.get("release_state") == "pass" else "warn" if x.get("release_state") == "conditional" else "muted"),
                     esc(x.get("tests_baseline") or "—")] for x in (releases.get("items") or [])]

    cron_rows = []
    for x in (cron.get("recent") or [])[:15]:
        kind = "ok" if x.get("status") == "completed" else "bad" if x.get("status") == "failed" else "muted"
        cron_rows.append([esc(x.get("name") or x.get("job_id")), badge(x.get("status", ""), kind),
                          esc((x.get("started_at") or "")[:19]), esc(x.get("duration_s")),
                          esc((x.get("error") or "")[:90])])

    ledger_rows = []
    for route, r in sorted(weekly_routes.items()):
        ledger_rows.append([esc(route), esc(r.get("n")), badge(r.get("status", ""),
                            "ok" if r.get("status") == "ok" else "warn")])

    guard_kind = "ok" if not issues else "warn"
    issue_kinds = " / ".join(sorted({x.get("kind", "") for x in issues})) or "无"
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>运维可观测性 · {esc(d.get('as_of'))}</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--line:#30363d;--text:#e6edf3;--muted:#8b949e;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--blue:#58a6ff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:36px 26px 70px}}h1{{font-size:26px;margin:0 0 4px}}
h2{{font-size:18px;margin:32px 0 10px;padding-bottom:7px;border-bottom:1px solid var(--line)}}
.sub,.muted,.label{{color:var(--muted);font-size:13px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.kpi{{font-size:26px;font-weight:700;line-height:1.2}}.kpi.warn{{color:var(--warn)}}.kpi.bad{{color:var(--bad)}}
table{{width:100%;border-collapse:collapse;font-size:14px;margin:6px 0}}th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{color:var(--muted);font-size:12.5px;font-weight:600}}tr:last-child td{{border-bottom:none}}
.tag{{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid}}
.tag.ok{{color:var(--ok);border-color:#238636}}.tag.warn{{color:var(--warn);border-color:#9e6a03}}.tag.bad{{color:var(--bad);border-color:#da3633}}.tag.muted{{color:var(--muted);border-color:var(--line)}}
a{{color:var(--blue)}}code{{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;color:#c9d1d9}}
@media(max-width:760px){{.grid{{grid-template-columns:repeat(2,1fr)}}.wrap{{padding:22px 14px}}}}
</style></head><body><div class="wrap">
<h1>运维可观测性</h1>
<div class="sub">交易日 {esc(d.get('as_of'))} · 生成 {esc(d.get('generated_at'))} · 数据源 <code>_学习/_运维/可观测性_最新.json</code></div>
<div class="grid">
{card('守卫告警', str(len(issues)), issue_kinds, guard_kind)}
{card('critical 指派', str(counts.get('critical', '—')), f"共 {assigns.get('total','—')} 条 · 来源 {assigns.get('sources','—')} 份总审", 'bad' if counts.get('critical', 0) > 50 else '')}
{card('预测机器覆盖', pct(coverage), f"可判定 {pct(pred.get('judgeable'))} · {totals.get('rows','—')} 行", 'warn' if (coverage or 0) < 0.7 else 'ok')}
{card('staging', f"{stage.get('gb','—')} GiB", f"{stage.get('count','—')} 个构建 · 最早 {stage.get('oldest_days','—')} 天")}
</div>

<h2>一、守卫告警</h2>
{issue_html}
<p class="sub">守卫状态：<code>{esc(guard.get('checked_at') or '—')}</code>；磁盘剩余 {esc((guard.get('disk') or {}).get('free_gb', '—'))} GB。</p>

<h2>二、源新鲜度</h2>
{table(['对象', '状态', '最后修改'], fresh_rows)}
<p class="sub">距交付截止（{esc(d.get('as_of'))} 20:00）已 {esc(fresh.get('hours_since_cutoff', '—'))} 小时；周末/节假日会自然拉长。</p>

<h2>三、指派与逾期</h2>
<div class="sub">critical {esc(counts.get('critical', 0))} · warn {esc(counts.get('warn', 0))} · open {esc(counts.get('open', 0))} · done {esc(counts.get('done', 0))}</div>
{table(['owner', 'critical', 'warn', 'open', 'done'], owner_rows)}

<h2>四、认知清算</h2>
{table(['清算状态', '条数'], cog_rows)}
<p class="sub">总计 {esc(cog.get('total', '—'))} 条；verified 必须同时有规格、到期日和 true/false 结果，当前为 0 不伪造。</p>

<h2>五、预测覆盖（最差日期）</h2>
{table(['日期', '行数', '机器可判', '覆盖率', '可判定率', 'ambiguous'], pred_rows)}
<p class="sub">coverage=机器行/全部行；judgeable=(true+false)/到期样本。新格式覆盖率 &lt;70% 由 <code>verify_tuiyan.py</code> 直接 FAIL。</p>

<h2>六、发布</h2>
{table(['build', '创建时间', '状态', '测试基线'], release_rows)}

<h2>七、账本周统计</h2>
{table(['路', 'n', '样本状态'], ledger_rows)}
<p class="sub">n&lt;10 一律 <code>insufficient</code>，不把 1–2 笔当周考核结论。</p>

<h2>八、Cron 最近运行</h2>
{table(['任务', '状态', '开始', '耗时(s)', '错误'], cron_rows)}

<p class="sub" style="margin-top:28px">相关：<a href="../复盘/盯盘台/index.html">今日盯盘台</a> ·
<a href="修复验收_20261018.html">修复验收页</a> ·
变更登记 <code>_变更总账.md #239</code></p>
</div></body></html>"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"运维可观测性_{d.get('as_of')}.html"
    out.write_text(html_doc, encoding="utf-8")
    (OUT_DIR / "运维可观测性_最新.html").write_text(html_doc, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build())
