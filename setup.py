from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from sys import argv

from setuptools import setup
import io
import six

from setuptools.extension import Extension

try:
    # Only use Cython if it's installed in the environment, otherwise use the provided C
    import Cython
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

if six.PY2:
    ext = b'.pyx' if USE_CYTHON else b'.c'
    extensions = [
        Extension(b'jsonobject.api', [b"jsonobject/api" + ext],),
        Extension(b'jsonobject.base', [b"jsonobject/base" + ext],),
        Extension(b'jsonobject.base_properties', [b"jsonobject/base_properties" + ext],),
        Extension(b'jsonobject.containers', [b"jsonobject/containers" + ext],),
        Extension(b'jsonobject.properties', [b"jsonobject/properties" + ext],),
        Extension(b'jsonobject.utils', [b"jsonobject/utils" + ext],),
    ]
else:
    ext = '.pyx' if USE_CYTHON else '.c'
    extensions = [
        Extension('jsonobject.api', ["jsonobject/api" + ext],),
        Extension('jsonobject.base', ["jsonobject/base" + ext],),
        Extension('jsonobject.base_properties', ["jsonobject/base_properties" + ext],),
        Extension('jsonobject.containers', ["jsonobject/containers" + ext],),
        Extension('jsonobject.properties', ["jsonobject/properties" + ext],),
        Extension('jsonobject.utils', ["jsonobject/utils" + ext],),
    ]

CYTHON_REQUIRES = ['cython==0.27.3']
if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)
else:
    print("You are running without Cython installed. It is highly recommended to run\n"
          "  pip install {}\n"
          "before you continue".format(' '.join(CYTHON_REQUIRES)))


with io.open('README.md', 'rt', encoding="utf-8") as readme_file:
    long_description = readme_file.read()


setup(
    name='jsonobject',
    version='0.9.2',
    author='Danny Roberts',
    author_email='droberts@dimagi.com',
    description='A library for dealing with JSON as python objects',
    long_description=long_description,
    url='https://github.com/dimagi/jsonobject',
    packages=['jsonobject'],
    setup_requires=CYTHON_REQUIRES,
    install_requires=['six'],
    tests_require=['unittest2'],
    ext_modules=extensions,
    test_suite='test' if six.PY3 else b'test',
)
