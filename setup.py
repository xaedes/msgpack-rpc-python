#!/usr/bin/env python
# coding: utf-8

# Define __version__ without importing msgpackrpc.
# This allows building sdist without installing any 3rd party packages.
exec(open('msgpackrpc/_version.py').read())

import platform

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.core import Extension

# The following code is copied from
# https://github.com/mongodb/mongo-python-driver/blob/master/setup.py
# to support installing without the extension on platforms where
# no compiler is available.
from distutils.command.build_ext import build_ext


class custom_build_ext(build_ext):
    """Allow C extension building to fail.
    The C extension speeds up websocket masking, but is not essential.
    """

    warning_message = """
********************************************************************
WARNING: %s could not
be compiled. No C extensions are essential for Tornado to run,
although they do result in significant speed improvements for
websockets.
%s
Here are some hints for popular operating systems:
If you are seeing this message on Linux you probably need to
install GCC and/or the Python development package for your
version of Python.
Debian and Ubuntu users should issue the following command:
    $ sudo apt-get install build-essential python-dev
RedHat and CentOS users should issue the following command:
    $ sudo yum install gcc python-devel
Fedora users should issue the following command:
    $ sudo dnf install gcc python-devel
If you are seeing this message on OSX please read the documentation
here:
http://api.mongodb.org/python/current/installation.html#osx
********************************************************************
"""

    def run(self):
        try:
            build_ext.run(self)
        except Exception:
            e = sys.exc_info()[1]
            sys.stdout.write('%s\n' % str(e))
            warnings.warn(self.warning_message % ("Extension modules",
                                                  "There was an issue with "
                                                  "your platform configuration"
                                                  " - see above."))

    def build_extension(self, ext):
        name = ext.name
        try:
            build_ext.build_extension(self, ext)
        except Exception:
            e = sys.exc_info()[1]
            sys.stdout.write('%s\n' % str(e))
            warnings.warn(self.warning_message % ("The %s extension "
                                                  "module" % (name,),
                                                  "The output above "
                                                  "this warning shows how "
                                                  "the compilation "
                                                  "failed."))

kwargs = {}
if (platform.python_implementation() == 'CPython' and
        os.environ.get('MSGPACKRPC_TORNADO_EXTENSION') != '0'):
    # This extension builds and works on pypy as well, although pypy's jit
    # produces equivalent performance.
    kwargs['ext_modules'] = [
        Extension('msgpackrpc.tornado.speedups',
                  sources=['msgpackrpc/tornado/speedups.c']),
    ]

    if os.environ.get('MSGPACKRPC_TORNADO_EXTENSION') != '1':
        # Unless the user has specified that the extension is mandatory,
        # fall back to the pure-python implementation on any build failure.
        kwargs['cmdclass'] = {'build_ext': custom_build_ext}

tornado_install_requires = []
if setuptools is not None:
    # If setuptools is not available, you're on your own for dependencies.
    if sys.version_info < (2, 7):
        # Only needed indirectly, for singledispatch.
        tornado_install_requires.append('ordereddict')
    if sys.version_info < (2, 7, 9):
        tornado_install_requires.append('backports.ssl_match_hostname')
    if sys.version_info < (3, 4):
        tornado_install_requires.append('singledispatch')
        # Certifi is also optional on 2.7.9+, although making our dependencies
        # conditional on micro version numbers seems like a bad idea
        # until we have more declarative metadata.
        tornado_install_requires.append('certifi')
    if sys.version_info < (3, 5):
        tornado_install_requires.append('backports_abc>=0.4')

setup(name='msgpack-rpc-python',
      version=__version__,
      author='Masahiro Nakagawa',
      author_email='repeatedly@gmail.com',
      url="https://github.com/msgpack-rpc/msgpack-rpc-python",
      description="MessagePack RPC",
      long_description="""\
MessagePack RPC for Python.

This implementation uses Tornado framework as a backend.
""",
      packages=['msgpackrpc', 'msgpackrpc/transport', 'msgpackrpc/tornado', 'msgpackrpc/tornado/test', 'msgpackrpc/tornado/platform'],
      install_requires=['msgpack-python'] + tornado_install_requires,
      license="Apache Software License",
      classifiers=[
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'License :: OSI Approved :: Apache Software License'
      ],
      **kwargs
      )
