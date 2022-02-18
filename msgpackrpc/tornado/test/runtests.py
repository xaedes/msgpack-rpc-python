#!/usr/bin/env python

from __future__ import absolute_import, division, print_function
import gc
import locale  # system locale module, not tornado.locale
import logging
import operator
import textwrap
import sys
from msgpackrpc.tornado.httpclient import AsyncHTTPClient
from msgpackrpc.tornado.httpserver import HTTPServer
from msgpackrpc.tornado.ioloop import IOLoop
from msgpackrpc.tornado.netutil import Resolver
from msgpackrpc.tornado.options import define, options, add_parse_callback
from msgpackrpc.tornado.test.util import unittest

try:
    reduce  # py2
except NameError:
    from functools import reduce  # py3

TEST_MODULES = [
    'msgpackrpc.tornado.httputil.doctests',
    'msgpackrpc.tornado.iostream.doctests',
    'msgpackrpc.tornado.util.doctests',
    'msgpackrpc.tornado.test.asyncio_test',
    'msgpackrpc.tornado.test.auth_test',
    'msgpackrpc.tornado.test.concurrent_test',
    'msgpackrpc.tornado.test.curl_httpclient_test',
    'msgpackrpc.tornado.test.escape_test',
    'msgpackrpc.tornado.test.gen_test',
    'msgpackrpc.tornado.test.http1connection_test',
    'msgpackrpc.tornado.test.httpclient_test',
    'msgpackrpc.tornado.test.httpserver_test',
    'msgpackrpc.tornado.test.httputil_test',
    'msgpackrpc.tornado.test.import_test',
    'msgpackrpc.tornado.test.ioloop_test',
    'msgpackrpc.tornado.test.iostream_test',
    'msgpackrpc.tornado.test.locale_test',
    'msgpackrpc.tornado.test.locks_test',
    'msgpackrpc.tornado.test.netutil_test',
    'msgpackrpc.tornado.test.log_test',
    'msgpackrpc.tornado.test.options_test',
    'msgpackrpc.tornado.test.process_test',
    'msgpackrpc.tornado.test.queues_test',
    'msgpackrpc.tornado.test.routing_test',
    'msgpackrpc.tornado.test.simple_httpclient_test',
    'msgpackrpc.tornado.test.stack_context_test',
    'msgpackrpc.tornado.test.tcpclient_test',
    'msgpackrpc.tornado.test.tcpserver_test',
    'msgpackrpc.tornado.test.template_test',
    'msgpackrpc.tornado.test.testing_test',
    'msgpackrpc.tornado.test.twisted_test',
    'msgpackrpc.tornado.test.util_test',
    'msgpackrpc.tornado.test.web_test',
    'msgpackrpc.tornado.test.websocket_test',
    'msgpackrpc.tornado.test.windows_test',
    'msgpackrpc.tornado.test.wsgi_test',
]


def all():
    return unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)


class TornadoTextTestRunner(unittest.TextTestRunner):
    def run(self, test):
        result = super(TornadoTextTestRunner, self).run(test)
        if result.skipped:
            skip_reasons = set(reason for (test, reason) in result.skipped)
            self.stream.write(textwrap.fill(
                "Some tests were skipped because: %s" %
                ", ".join(sorted(skip_reasons))))
            self.stream.write("\n")
        return result


class LogCounter(logging.Filter):
    """Counts the number of WARNING or higher log records."""
    def __init__(self, *args, **kwargs):
        # Can't use super() because logging.Filter is an old-style class in py26
        logging.Filter.__init__(self, *args, **kwargs)
        self.warning_count = self.error_count = 0

    def filter(self, record):
        if record.levelno >= logging.ERROR:
            self.error_count += 1
        elif record.levelno >= logging.WARNING:
            self.warning_count += 1
        return True


def main():
    # The -W command-line option does not work in a virtualenv with
    # python 3 (as of virtualenv 1.7), so configure warnings
    # programmatically instead.
    import warnings
    # Be strict about most warnings.  This also turns on warnings that are
    # ignored by default, including DeprecationWarnings and
    # python 3.2's ResourceWarnings.
    warnings.filterwarnings("error")
    # setuptools sometimes gives ImportWarnings about things that are on
    # sys.path even if they're not being used.
    warnings.filterwarnings("ignore", category=ImportWarning)
    # Tornado generally shouldn't use anything deprecated, but some of
    # our dependencies do (last match wins).
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("error", category=DeprecationWarning,
                            module=r"tornado\..*")
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("error", category=PendingDeprecationWarning,
                            module=r"tornado\..*")
    # The unittest module is aggressive about deprecating redundant methods,
    # leaving some without non-deprecated spellings that work on both
    # 2.7 and 3.2
    warnings.filterwarnings("ignore", category=DeprecationWarning,
                            message="Please use assert.* instead")
    # unittest2 0.6 on py26 reports these as PendingDeprecationWarnings
    # instead of DeprecationWarnings.
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning,
                            message="Please use assert.* instead")
    # Twisted 15.0.0 triggers some warnings on py3 with -bb.
    warnings.filterwarnings("ignore", category=BytesWarning,
                            module=r"twisted\..*")
    # The __aiter__ protocol changed in python 3.5.2.
    # Silence the warning until we can drop 3.5.[01].
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning,
                            message=".*legacy __aiter__ protocol")
    # 3.5.2's PendingDeprecationWarning became a DeprecationWarning in 3.6.
    warnings.filterwarnings("ignore", category=DeprecationWarning,
                            message=".*legacy __aiter__ protocol")

    logging.getLogger("tornado.access").setLevel(logging.CRITICAL)

    define('httpclient', type=str, default=None,
           callback=lambda s: AsyncHTTPClient.configure(
               s, defaults=dict(allow_ipv6=False)))
    define('httpserver', type=str, default=None,
           callback=HTTPServer.configure)
    define('ioloop', type=str, default=None)
    define('ioloop_time_monotonic', default=False)
    define('resolver', type=str, default=None,
           callback=Resolver.configure)
    define('debug_gc', type=str, multiple=True,
           help="A comma-separated list of gc module debug constants, "
           "e.g. DEBUG_STATS or DEBUG_COLLECTABLE,DEBUG_OBJECTS",
           callback=lambda values: gc.set_debug(
               reduce(operator.or_, (getattr(gc, v) for v in values))))
    define('locale', type=str, default=None,
           callback=lambda x: locale.setlocale(locale.LC_ALL, x))

    def configure_ioloop():
        kwargs = {}
        if options.ioloop_time_monotonic:
            from msgpackrpc.tornado.platform.auto import monotonic_time
            if monotonic_time is None:
                raise RuntimeError("monotonic clock not found")
            kwargs['time_func'] = monotonic_time
        if options.ioloop or kwargs:
            IOLoop.configure(options.ioloop, **kwargs)
    add_parse_callback(configure_ioloop)

    log_counter = LogCounter()
    add_parse_callback(
        lambda: logging.getLogger().handlers[0].addFilter(log_counter))

    import msgpackrpc.tornado.testing
    kwargs = {}
    if sys.version_info >= (3, 2):
        # HACK:  unittest.main will make its own changes to the warning
        # configuration, which may conflict with the settings above
        # or command-line flags like -bb.  Passing warnings=False
        # suppresses this behavior, although this looks like an implementation
        # detail.  http://bugs.python.org/issue15626
        kwargs['warnings'] = False
    kwargs['testRunner'] = TornadoTextTestRunner
    try:
        msgpackrpc.tornado.testing.main(**kwargs)
    finally:
        # The tests should run clean; consider it a failure if they logged
        # any warnings or errors. We'd like to ban info logs too, but
        # we can't count them cleanly due to interactions with LogTrapTestCase.
        if log_counter.warning_count > 0 or log_counter.error_count > 0:
            logging.error("logged %d warnings and %d errors",
                          log_counter.warning_count, log_counter.error_count)
            sys.exit(1)


if __name__ == '__main__':
    main()
