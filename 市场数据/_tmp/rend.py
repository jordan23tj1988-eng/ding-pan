import sys, io, os
B = r"D:/股票数据/市场数据"
os.chdir(B)
sys.path.insert(0, B)
import module_render_theme as m
d = "20261020"
t = m.r_reco_table(d)
print("r_reco_table len", len(t), "| rows:", t.count("<tr>"), "| 断档?", "缺失" in t)
body = io.open(os.path.join(B,"_学习/theme_body_20261020.html"), encoding="utf-8").read()
j = m.r_judge(body, d)
print("r_judge len", len(j), "| contains table", "<table" in j, "| insight", "洞察(agent)" in j)
r = m.r_rank(body); l = m.r_life(body); deep = m.r_leader(body); cog = m.r_cog(body, d)
print("rank", len(r), "life", len(l), "deep", len(deep), "cog", len(cog))
ldr, jdg = m._leader_judge(d)
print("leaders lines", list(ldr.keys()))
print("judgments lines", list(jdg.keys()))
lj = m._life_judge(d) if hasattr(m,"_life_judge") else None
print("life judge", list(lj[0].keys()) if lj else "n/a", "| 高低切 len", len(lj[1]) if lj else 0)
print("--- deep head ---")
print(deep[:300])
