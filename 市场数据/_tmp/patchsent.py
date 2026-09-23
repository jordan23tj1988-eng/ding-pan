from pathlib import Path
p=Path(r'D:\股票数据\市场数据\复盘一致性哨兵.py');x=p.read_text(encoding='utf8');x=x.replace("capture_output=True, text=True, encoding='utf-8',","capture_output=True, text=True, encoding='utf-8', errors='replace',");p.write_text(x,encoding='utf8')
