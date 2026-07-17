import socket; socket.setdefaulttimeout(20)
import sys, runpy
sys.argv=["涨停质量训练.py"]+sys.argv[1:]
runpy.run_path("涨停质量训练.py", run_name="__main__")
