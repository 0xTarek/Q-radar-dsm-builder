#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSM Builder Server — Python 2.7 compatible
Serves the HTML tool on port 8080
Proxies QRadar API calls to avoid CORS
"""

import sys
import os
import json
import ssl
import urllib2
import BaseHTTPServer
import SimpleHTTPServer

PORT     = 8080
SERVE_DIR = '/opt/dsm-builder'

class DSMHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/qradar-proxy/'):
            self._proxy('GET', None)
        else:
            # Serve static files
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path.startswith('/qradar-proxy/'):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else None
            self._proxy('POST', body)
        else:
            self.send_error(404)

    def _proxy(self, method, body):
        """Forward request to QRadar, inject SEC token, return response"""
        try:
            # Extract QRadar host and path from headers
            qr_host  = self.headers.get('X-QRadar-Host', '').strip()
            qr_token = self.headers.get('X-QRadar-Token', '').strip()

            if not qr_host or not qr_token:
                self._json_error(400, 'Missing X-QRadar-Host or X-QRadar-Token header')
                return

            # Build target URL
            api_path = self.path[len('/qradar-proxy'):]
            target_url = 'https://' + qr_host + api_path

            # Detect content type from browser request
            content_type = self.headers.get('Content-Type', 'application/json')

            # Build request
            req = urllib2.Request(target_url, data=body)
            req.add_header('SEC', qr_token)
            req.add_header('Accept', 'application/json')
            # Forward original Content-Type (important for multipart/form-data)
            if content_type:
                req.add_header('Content-Type', content_type)
            req.get_method = lambda: method

            # Disable SSL verification (QRadar uses self-signed cert)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            resp = urllib2.urlopen(req, context=ctx, timeout=120)
            resp_body = resp.read()
            resp_code = resp.getcode()

            self.send_response(resp_code)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(resp_body)

        except urllib2.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(err_body)

        except Exception as e:
            self._json_error(500, str(e))

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-QRadar-Host, X-QRadar-Token, SEC')

    def _json_error(self, code, msg):
        body = json.dumps({'error': msg})
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stdout.write('[DSM-Server] ' + fmt % args + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    os.chdir(SERVE_DIR)
    httpd = BaseHTTPServer.HTTPServer(('', PORT), DSMHandler)
    print('[DSM-Server] Running on http://0.0.0.0:' + str(PORT))
    print('[DSM-Server] Serving files from: ' + SERVE_DIR)
    print('[DSM-Server] QRadar proxy at: /qradar-proxy/api/...')
    sys.stdout.flush()
    httpd.serve_forever()
