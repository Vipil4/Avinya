#!/usr/bin/env python3
"""
Avinya Backend — Anthropic API Proxy
Deploy on Render or Railway (free tier).
Set ANTHROPIC_KEY as an environment variable in the platform dashboard.

Local test:
  ANTHROPIC_KEY=sk-ant-... python backend/avinya_server.py
"""
import os
import json
import http.server
import urllib.request
import urllib.error

PORT          = int(os.environ.get('PORT', 3000))
ANTHROPIC_KEY = os.environ.get('ANTHROPIC_KEY', '')
ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
MAX_BYTES     = 25 * 1024 * 1024

CORS = {
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, anthropic-beta',
    'Access-Control-Max-Age':       '86400',
}

class AviHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _cors(self, status, ctype='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def _json(self, status, obj):
        self._cors(status)
        self.wfile.write(json.dumps(obj).encode())

    def do_OPTIONS(self):
        self._cors(204)

    def do_GET(self):
        self._json(200, {
            'status':  'ok',
            'service': 'Avinya Proxy',
            'version': '2.0',
            'key_set': bool(ANTHROPIC_KEY)
        })

    def do_POST(self):
        if not ANTHROPIC_KEY:
            self._json(401, {'error': {'message': 'ANTHROPIC_KEY not set on server'}})
            return

        length = int(self.headers.get('Content-Length', 0))
        if length > MAX_BYTES:
            self._json(413, {'error': {'message': 'Request too large (max 25 MB)'}})
            return

        chunks = []
        remaining = length
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b''.join(chunks)

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._json(400, {'error': {'message': 'Invalid JSON body'}})
            return

        fwd_headers = {
            'Content-Type':      'application/json',
            'x-api-key':         ANTHROPIC_KEY,
            'anthropic-version': '2023-06-01',
        }
        beta = self.headers.get('anthropic-beta', '')
        if beta:
            fwd_headers['anthropic-beta'] = beta

        try:
            body = json.dumps(payload).encode('utf-8')
            req  = urllib.request.Request(
                ANTHROPIC_URL,
                data=body,
                headers=fwd_headers,
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                self._cors(resp.getcode())
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self._cors(e.code)
            self.wfile.write(e.read())
        except Exception as e:
            self._json(502, {'error': {'message': str(e)}})


if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), AviHandler)
    print(f'Avinya proxy on port {PORT} — key set: {bool(ANTHROPIC_KEY)}')
    server.serve_forever()
