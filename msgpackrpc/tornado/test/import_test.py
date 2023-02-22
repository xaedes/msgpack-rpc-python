# flake8: noqa
from __future__ import absolute_import, division, print_function
from msgpackrpc.tornado.test.util import unittest


class ImportTest(unittest.TestCase):
    def test_import_everything(self):
        # Some of our modules are not otherwise tested.  Import them
        # all (unless they have external dependencies) here to at
        # least ensure that there are no syntax errors.
        import msgpackrpc.tornado.auth
        import msgpackrpc.tornado.autoreload
        import msgpackrpc.tornado.concurrent
        import msgpackrpc.tornado.escape
        import msgpackrpc.tornado.gen
        import msgpackrpc.tornado.http1connection
        import msgpackrpc.tornado.httpclient
        import msgpackrpc.tornado.httpserver
        import msgpackrpc.tornado.httputil
        import msgpackrpc.tornado.ioloop
        import msgpackrpc.tornado.iostream
        import msgpackrpc.tornado.locale
        import msgpackrpc.tornado.log
        import msgpackrpc.tornado.netutil
        import msgpackrpc.tornado.options
        import msgpackrpc.tornado.process
        import msgpackrpc.tornado.simple_httpclient
        import msgpackrpc.tornado.stack_context
        import msgpackrpc.tornado.tcpserver
        import msgpackrpc.tornado.tcpclient
        import msgpackrpc.tornado.template
        import msgpackrpc.tornado.testing
        import msgpackrpc.tornado.util
        import msgpackrpc.tornado.web
        import msgpackrpc.tornado.websocket
        import msgpackrpc.tornado.wsgi

    # for modules with dependencies, if those dependencies can be loaded,
    # load them too.

    def test_import_pycurl(self):
        try:
            import pycurl  # type: ignore
        except ImportError:
            pass
        else:
            import msgpackrpc.tornado.curl_httpclient
