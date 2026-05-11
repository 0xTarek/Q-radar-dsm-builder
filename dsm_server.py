#!/usr/bin/env python
# -- coding: utf-8 -- 
"""
DSM Builder Server — Python 2.7 compatible
Serves the HTML tool on port 8080
Proxies QRadar API calls to avoid CORS
"""

import sys
import os
import io
import json
import ssl
import zipfile
import httplib
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
        if self.path == '/build-and-import':
            self._build_and_import()
        elif self.path.startswith('/qradar-proxy/'):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else None
            self._proxy('POST', body)
        else:
            self.send_error(404)

    def _build_and_import(self):
        try:
            length      = int(self.headers.get('Content-Length', 0))
            body        = self.rfile.read(length)
            data        = json.loads(body.decode('utf-8'))
            qr_host     = data.get('qr_host', '').strip()
            qr_token    = data.get('qr_token', '').strip()
            dsm_name    = data.get('dsm_name', 'DSM').strip()
            content_xml = data.get('content_xml', '')

            if not qr_host or not qr_token or not content_xml:
                self._json_error(400, 'Missing qr_host, qr_token or content_xml')
                return

            # Build ZIP using Python zipfile — no binary corruption
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zf:
                zf.writestr(dsm_name + '.xml', content_xml.encode('utf-8'))
            zip_bytes = zip_buffer.getvalue()

            # Build multipart/form-data manually
            boundary = 'DSMBuilderBoundary'
            filename = dsm_name + '.zip'
            mp_body  = b''
            mp_body += ('--' + boundary + '\r\n').encode('utf-8')
            mp_body += ('Content-Disposition: form-data; name="file"; filename="' + filename + '"\r\n').encode('utf-8')
            mp_body += b'Content-Type: application/zip\r\n\r\n'
            mp_body += zip_bytes
            mp_body += ('\r\n--' + boundary + '--\r\n').encode('utf-8')

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode    = ssl.CERT_NONE

            conn = httplib.HTTPSConnection(qr_host, context=ctx, timeout=120)
            conn.request('POST',
                '/api/config/extension_management/extensions?overwrite=true',
                body=mp_body,
                headers={
                    'SEC'          : qr_token,
                    'Accept'       : 'application/json',
                    'Content-Type' : 'multipart/form-data; boundary=' + boundary,
                    'Version'      : '14.0',
                })
            resp      = conn.getresponse()
            resp_body = resp.read()
            resp_code = resp.status
            conn.close()

            body_out = json.dumps(json.loads(resp_body.decode('utf-8', 'replace')))
            self.send_response(resp_code)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body_out.encode('utf-8'))

        except Exception as e:
            self._json_error(500, str(e))

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


if _name_ == '_main_':
    os.chdir(SERVE_DIR)
    httpd = BaseHTTPServer.HTTPServer(('', PORT), DSMHandler)
    print('[DSM-Server] Running on http://0.0.0.0:' + str(PORT))
    print('[DSM-Server] Serving files from: ' + SERVE_DIR)
    print('[DSM-Server] QRadar proxy at: /qradar-proxy/api/...')
    sys.stdout.flush()
    httpd.serve_forever()
