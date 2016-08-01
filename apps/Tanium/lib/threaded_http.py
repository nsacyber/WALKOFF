#!/usr/bin/env python
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
"""Simple HTTP server for testing purposes"""

from __future__ import print_function

import sys
import cgi
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading

# disable python from creating .pyc files everywhere
sys.dont_write_bytecode = True


class CustomHTTPHandler(BaseHTTPRequestHandler):
    ENABLE_LOGGING = True

    def do_GET(self):  # noqa
        self.send_response(200)
        self.end_headers()
        message = threading.currentThread().getName()
        self.wfile.write(message)
        self.wfile.write('\n')
        return

    def do_POST(self):  # noqa
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-Type'],
            }
        )

        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %s\n' % str(self.client_address))
        self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        self.wfile.write('Path: %s\n' % self.path)
        self.wfile.write('Form data:\n')

        # Echo back information about what was posted in the form
        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # The field contains an uploaded file
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                self.wfile.write(
                    '\tUploaded %s as "%s" (%d bytes)\n' % (field, field_item.filename, file_len)
                )
            else:
                # Regular form value
                self.wfile.write('\t%s=%s\n' % (field, form[field].value))
        return

    # turn off logging messages so we don't see the get requests in console
    # during unittests
    def log_message(self, format, *args):
        if self.ENABLE_LOGGING:
            BaseHTTPRequestHandler.log_message(self, format, *args)
        else:
            pass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def threaded_http(host='localhost', port=4443, verbosity=2):
    '''establishes an HTTP server on host:port in a thread'''
    server = ThreadedHTTPServer((host, port), CustomHTTPHandler)

    if verbosity >= 3:
        server.RequestHandlerClass.ENABLE_LOGGING = True
    else:
        server.RequestHandlerClass.ENABLE_LOGGING = False

    t = threading.Thread(target=server.serve_forever)
    t.setDaemon(True)
    t.start()
    if verbosity >= 2:
        m = 'Threaded HTTP server started on {}:{}'.format(host, port)
        print(m, file=sys.stderr)
    return server
