# -*- coding: utf-8 -*-
"""从 judgment_{d}.json 提取「龙头标的」+「判断」→ 题材龙头判断_{d}.json
零编造: 数据全部来自 LLM 原文(板块四龙头识别 + 板块二 tds 判断句), 只结构化, 不新造。
龙头标的题材归属: 名称反查(题材归位映射+zt_pool) → 大方向; 反查失败用原文题材关键词归一化。
身份标签: 从板块四原文该龙头短语提取(候选龙/质量锚/封单质量龙/退位龙/残余身位/晋级龙/残余/孤高标)。
"""
import json, re, os, csv, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 市场数据/


def load_json(name, d):
    p = os.path.join(BASE, '_学习', name % d if '%s' in name else name)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else '20260814'
    jud = load_json('judgment_%s.json', d)
    if not jud:
        print('FAIL judgment 缺失'); return 1
    bt = (jud.get('bodies') or {}).get('theme') or ''
    if not bt:
        print('FAIL bodies.theme 缺失'); return 1

    # ===== 1. 判断句: 板块二 tds (每条题材 "=判断句") =====
    i2 = bt.find('<h2>二'); k2 = bt.find('<h2>三')
    seg2 = bt[i2:k2] if i2 >= 0 else ''
    tnms = re.findall(r'<span class="tnm">(.*?)</span>', seg2)
    tdss = re.findall(r'<div class="tds">(.*?)</div>', seg2, re.S)
    judge = {}
    for n in range(min(len(tnms), len(tdss))):
        txt = re.sub(r'<[^>]+>', '', tdss[n])
        eq = txt.rfind('=')
        jt = txt[eq + 1:].strip() if eq > 0 else txt
        jt = jt.split('四维:')[0].strip().rstrip('。')
        judge[tnms[n]] = jt

    # ===== 2. 龙头标的: 板块四 <b>名称</b> + 身份标签 =====
    i4 = bt.find('<h2>四'); k4 = bt.find('<h2>五')
    seg4 = bt[i4:k4] if i4 >= 0 else ''

    # 2a. 题材线名(6有聚类口径) → 用于前缀归一化
    s6 = load_json('主流题材6有_%s.json', d)
    line_names = []
    if s6:
        for x in (s6.get('题材_聚类口径') or []):
            nm = x.get('题材(题材聚类口径)') or x.get('题材') or ''
            if nm:
                line_names.append(nm)

    # 2b. 名称 → 大方向 反查表(题材归位映射: 代码→大方向; zt_pool: 名称→代码)
    name2dir = {}
    rg = load_json('题材归位_%s.json', d)
    mp = (rg or {}).get('映射') or {}
    code2dir = {c: (v or {}).get('大方向') for c, v in mp.items() if isinstance(v, dict)}
    # 名称→代码: 需要 zt_pool 或 归位映射里有没有名称字段
    zt_path = os.path.join(BASE, d, 'zt_pool.csv')
    if os.path.isfile(zt_path):
        with open(zt_path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                code = (row.get('代码') or '').zfill(6)
                nm = row.get('名称') or ''
                if nm and code in code2dir:
                    name2dir[nm] = code2dir[code]

    # 题材关键词 → 完整线名(前缀匹配)
    def norm_line(kw):
        for ln in line_names:
            if ln.startswith(kw):
                return ln
        return kw

    # 2c. 提取龙头: 板块四原文按 <b> 切分, 提取名称 + 身份
    # 原文结构: 身份短语=名称(...) 或 /名称(...); 分号分隔
    leaders = {}  # {题材线: [(名称, 身份)]}
    # 逐 <b> 标签提取, 并带上下文(前 40 字符)判断题材关键词 + 身份
    for m in re.finditer(r'<b>([^<]+)</b>', seg4):
        raw = m.group(1).strip()
        name = raw
        identity = ''
        # 标签内含 "题材身份=名称" 形式
        if '=' in raw:
            left, name = raw.split('=', 1)
            left = left.strip()
            # left 如 "AI算力候选龙头" → 身份=去掉题材关键词后的部分
            identity = left
        # 上下文前 60 字符(含身份短语/题材关键词)
        ctx = seg4[max(0, m.start() - 60):m.start()]
        ctx_txt = re.sub(r'<[^>]+>', '', ctx)
        # 题材归属: 反查优先
        line = name2dir.get(name.strip())
        if not line:
            # 兜底: 从上下文或 left 找题材关键词
            for kw in ('AI算力', '创新药', '机器人', '环保', '地产链', '半导体', '军工'):
                if kw in ctx_txt or kw in identity:
                    line = norm_line(kw)
                    break
        if not line:
            line = '未归属'
        # 身份精简: 从 identity 或 ctx_txt 提取
        ident = ''
        for tag in ('候选龙头', '封单质量龙', '退位龙', '残余身位', '晋级龙', '质量锚', '孤高标', '残余', '高度龙'):
            if tag in identity or tag in ctx_txt:
                ident = tag
                break
        leaders.setdefault(line, []).append((name.strip(), ident))

    out = {'日期': d, '龙头标的': leaders, '判断': judge}
    op = os.path.join(BASE, '_学习', '题材龙头判断_%s.json' % d)
    json.dump(out, open(op, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('已生成:', op)
    print('题材线数:', len(line_names))
    print('判断条数:', len(judge))
    for ln, lst in leaders.items():
        print(f'  龙头[{ln}]:', ' / '.join(f'{n}({i or "—"})' for n, i in lst))
    for k, v in judge.items():
        print(f'  判断[{k}]:', v[:40])


if __name__ == '__main__':
    sys.exit(main())
