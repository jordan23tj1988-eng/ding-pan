# -*- coding: utf-8 -*-
"""盯盘台服务.py — no-store 静态服务器 (根=市场数据/复盘)
替代裸 http.server: 无 Cache-Control 会启发式缓存旧页面(坑42a)
ThreadingTCPServer 防单连接卡死(坑65)
用法: python 盯盘台服务.py [port=8899]
"""
import http.server, socketserver, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '复盘')

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        super().end_headers()
    def log_message(self, fmt, *args):
        sys.stdout.write('[%s] %s\n' % (self.log_date_time_string(), fmt % args))

class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    with S(('127.0.0.1', port), H) as httpd:
        print('盯盘台服务: http://127.0.0.1:%d/ (root=%s)' % (port, ROOT), flush=True)
        httpd.serve_forever()
