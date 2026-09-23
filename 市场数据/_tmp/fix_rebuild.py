from pathlib import Path
p=Path(r'D:\股票数据\市场数据\_tmp\rebuild_limitup.py');x=p.read_text(encoding='utf8').replace('`)n','`)\n');p.write_text(x,encoding='utf8');compile(x,str(p),'exec');
