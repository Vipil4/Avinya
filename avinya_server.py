"""
avinya_server.py  — Avinya proxy server
Handles:
  1. Anthropic API calls (model inference)
  2. Supabase REST proxy (when body contains sb_proxy: true)
     Forwards to real Supabase endpoint server-side — no CORS issues.

Deploy on Render.com as a Web Service:
  Build command: (none)
  Start command: python avinya_server.py
  Environment vars: ANTHROPIC_API_KEY=sk-ant-...
"""

import os, json, urllib.request as ur
from http.server import HTTPServer, BaseHTTPRequestHandler

ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
PORT = int(os.environ.get('PORT', 8080))

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        raw    = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except Exception:
            self.send_response(400)
            self._cors()
            self.end_headers()
            self.wfile.write(b'{"error":"Invalid JSON"}')
            return

        if body.get('sb_proxy'):
            self._handle_supabase(body)
        elif body.get('jb_proxy'):
            self._handle_jsonbin(body)
        else:
            self._handle_anthropic(body)

    def _handle_supabase(self, body):
        sb_url    = body.get('sb_url', '').rstrip('/')
        sb_key    = body.get('sb_key', '')
        sb_path   = body.get('sb_path', '')
        sb_method = body.get('sb_method', 'GET').upper()
        sb_body   = body.get('sb_body')
        sb_token  = body.get('sb_token')
        sb_prefer = body.get('sb_prefer')

        if not sb_url or not sb_key or not sb_path:
            self.send_response(400)
            self._cors()
            self.end_headers()
            self.wfile.write(b'{"error":"Missing sb_url, sb_key or sb_path"}')
            return

        headers = {'apikey': sb_key, 'Content-Type': 'application/json'}
        if sb_token:  headers['Authorization'] = 'Bearer ' + sb_token
        if sb_prefer: headers['Prefer'] = sb_prefer

        data = None
        if sb_body is not None:
            data = (sb_body.encode() if isinstance(sb_body, str)
                    else sb_body if isinstance(sb_body, bytes)
                    else json.dumps(sb_body).encode())

        req = ur.Request(sb_url + sb_path, data=data, headers=headers, method=sb_method)
        try:
            with ur.urlopen(req, timeout=20) as resp:
                result = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self._cors()
                self.end_headers()
                self.wfile.write(result)
        except ur.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_anthropic(self, body):
        if not ANTHROPIC_KEY:
            self.send_response(500)
            self._cors()
            self.end_headers()
            self.wfile.write(b'{"error":"ANTHROPIC_API_KEY not set"}')
            return

        req = ur.Request(
            'https://api.anthropic.com/v1/messages',
            data=json.dumps(body).encode(),
            headers={
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_KEY,
                'anthropic-version': '2023-06-01',
            },
            method='POST',
        )
        try:
            with ur.urlopen(req, timeout=60) as resp:
                result = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._cors()
                self.end_headers()
                self.wfile.write(result)
        except ur.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())



    def _handle_jsonbin(self, body):
        jb_bin    = body.get('jb_bin', '')
        jb_method = body.get('jb_method', 'GET').upper()
        jb_body   = body.get('jb_body')
        jb_key    = body.get('jb_key', '') or os.environ.get('JSONBIN_MASTER_KEY', '')

        # Build URL
        url = 'https://api.jsonbin.io/v3/b'
        if jb_bin:
            url += '/' + jb_bin
        if jb_method == 'GET':
            url += '/latest'

        # Build headers
        headers = {'Content-Type': 'application/json', 'X-Bin-Private': 'false'}
        if jb_key:
            headers['X-Master-Key'] = jb_key
        if jb_method == 'POST' and not jb_bin:
            headers['X-Bin-Name'] = 'avinya-cohort-library'

        # Build body
        data = json.dumps(jb_body).encode() if jb_body is not None else None

        try:
            import urllib.request as ur2
            req = ur2.Request(url, data=data, headers=headers, method=jb_method)
            with ur2.urlopen(req, timeout=20) as resp:
                result = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', 'application/json')
                self._cors()
                self.end_headers()
                self.wfile.write(result)
        except ur.HTTPError as e:
            body_bytes = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(body_bytes)
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e), 'url': url, 'method': jb_method}).encode())


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Avinya proxy running on port {PORT}')
    server.serve_forever()
