# -*- coding: utf-8 -*-
"""
QGIS Server HTTP wrapper

This script launches a QGIS Server listening on port 8081 or on the port
specified on the environment variable QGIS_SERVER_PORT.
QGIS_SERVER_HOST (defaults to 127.0.0.1)

For testing purposes, HTTP Basic can be enabled by setting the following
environment variables:

  * QGIS_SERVER_HTTP_BASIC_AUTH (default not set, set to anything to enable)
  * QGIS_SERVER_USERNAME (default ="username")
  * QGIS_SERVER_PASSWORD (default ="password")

PKI authentication with HTTPS can be enabled with:

  * QGIS_SERVER_PKI_CERTIFICATE (server certificate)
  * QGIS_SERVER_PKI_KEY (server private key)
  * QGIS_SERVER_PKI_AUTHORITY (root CA)
  * QGIS_SERVER_PKI_USERNAME (valid username)

 Sample run:

 QGIS_SERVER_PKI_USERNAME=Gerardus QGIS_SERVER_PORT=47547 QGIS_SERVER_HOST=localhost \
    QGIS_SERVER_PKI_KEY=/home/dev/QGIS/tests/testdata/auth_system/certs_keys/localhost_ssl_key.pem \
    QGIS_SERVER_PKI_CERTIFICATE=/home/dev/QGIS/tests/testdata/auth_system/certs_keys/localhost_ssl_cert.pem \
    QGIS_SERVER_PKI_AUTHORITY=/home/dev/QGIS/tests/testdata/auth_system/certs_keys/chains_subissuer-issuer-root_issuer2-root2.pem \
    python /home/dev/QGIS/tests/src/python/qgis_wrapped_server.py

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

__author__ = 'Alessandro Pasotti'
__date__ = '05/15/2016'
__copyright__ = 'Copyright 2016, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'


import os
import sys
import ssl
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from qgis.server import QgsServer, QgsServerFilter
from qgis.core import QgsMessageLog

QGIS_SERVER_PORT = int(os.environ.get('QGIS_SERVER_PORT', '8081'))
QGIS_SERVER_HOST = os.environ.get('QGIS_SERVER_HOST', '127.0.0.1')
# PKI authentication
QGIS_SERVER_PKI_CERTIFICATE = os.environ.get('QGIS_SERVER_PKI_CERTIFICATE')
QGIS_SERVER_PKI_KEY = os.environ.get('QGIS_SERVER_PKI_KEY')
QGIS_SERVER_PKI_AUTHORITY = os.environ.get('QGIS_SERVER_PKI_AUTHORITY')
QGIS_SERVER_PKI_USERNAME = os.environ.get('QGIS_SERVER_PKI_USERNAME')

# Check if PKI - https is enabled
https = (QGIS_SERVER_PKI_CERTIFICATE is not None and
         os.path.isfile(QGIS_SERVER_PKI_CERTIFICATE) and
         QGIS_SERVER_PKI_KEY is not None and
         os.path.isfile(QGIS_SERVER_PKI_KEY) and
         QGIS_SERVER_PKI_AUTHORITY is not None and
         os.path.isfile(QGIS_SERVER_PKI_AUTHORITY) and
         QGIS_SERVER_PKI_USERNAME)

qgs_server = QgsServer()

if os.environ.get('QGIS_SERVER_HTTP_BASIC_AUTH') is not None:
    import base64

    class HTTPBasicFilter(QgsServerFilter):

        def responseComplete(self):
            request = self.serverInterface().requestHandler()
            if self.serverInterface().getEnv('HTTP_AUTHORIZATION'):
                username, password = base64.b64decode(self.serverInterface().getEnv('HTTP_AUTHORIZATION')[6:]).split(':')
                if (username == os.environ.get('QGIS_SERVER_USERNAME', 'username')
                        and password == os.environ.get('QGIS_SERVER_PASSWORD', 'password')):
                    return
            # No auth ...
            request.clearHeaders()
            request.setHeader('Status', '401 Authorization required')
            request.setHeader('WWW-Authenticate', 'Basic realm="QGIS Server"')
            request.clearBody()
            request.appendBody('<h1>Authorization required</h1>')

    filter = HTTPBasicFilter(qgs_server.serverInterface())
    qgs_server.serverInterface().registerFilter(filter)


from filters.wpsFilter import wpsFilter
try:
    filter = wpsFilter(qgs_server.serverInterface())
    qgs_server.serverInterface().registerFilter(filter, 100)
    QgsMessageLog.logMessage("wps4server - Loaded successfully")
except Exception, e:
    QgsMessageLog.logMessage("wps4server - Error loading filter wps : %s" % e )


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # For PKI: check the username from client certificate
        if https:
            try:
                ssl.match_hostname(self.connection.getpeercert(), QGIS_SERVER_PKI_USERNAME)
            except Exception as ex:
                print("SSL Exception %s" % ex)
                self.send_response(401)
                self.end_headers()
                self.wfile.write('UNAUTHORIZED')
                return
        # CGI vars:
        for k, v in self.headers.items():
            # Uncomment to print debug info about env vars passed into QGIS Server env
            #print('Setting ENV var %s to %s' % ('HTTP_%s' % k.replace(' ', '-').replace('-', '_').replace(' ', '-').upper(), v))
            qgs_server.putenv('HTTP_%s' % k.replace(' ', '-').replace('-', '_').replace(' ', '-').upper(), v)
        qgs_server.putenv('SERVER_PORT', str(self.server.server_port))
        qgs_server.putenv('SERVER_NAME', self.server.server_name)
        qgs_server.putenv('REQUEST_URI', self.path)
        parsed_path = urllib.parse.urlparse(self.path)
        headers, body = qgs_server.handleRequest(parsed_path.query)
        headers_dict = dict(h.split(': ', 1) for h in headers.decode().split('\n') if h)
        try:
            self.send_response(int(headers_dict['Status'].split(' ')[0]))
        except:
            self.send_response(200)
        for k, v in headers_dict.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)
        return

    def do_POST(self):
        content_len = int(self.headers.get('content-length', 0))
        post_body = self.rfile.read(content_len).decode()
        request = post_body[1:post_body.find(' ')]
        self.path = self.path + '&REQUEST_BODY=' + \
            post_body.replace('&amp;', '') + '&REQUEST=' + request
        return self.do_GET()


if __name__ == '__main__':
    server = HTTPServer((QGIS_SERVER_HOST, QGIS_SERVER_PORT), Handler)
    if https:
        server.socket = ssl.wrap_socket(server.socket,
                                        certfile=QGIS_SERVER_PKI_CERTIFICATE,
                                        keyfile=QGIS_SERVER_PKI_KEY,
                                        ca_certs=QGIS_SERVER_PKI_AUTHORITY,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        server_side=True,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
    message = 'Starting server on %s://%s:%s, use <Ctrl-C> to stop' % \
              ('https' if https else 'http', QGIS_SERVER_HOST, server.server_port)
    try:
        print(message, flush=True)
    except:
        print(message)
        sys.stdout.flush()
    server.serve_forever()
