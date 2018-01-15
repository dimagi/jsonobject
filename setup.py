from setuptools import setup
import io

from setuptools.extension import Extension

try:
    # Only use Cython if it's installed in the environment, otherwise use the provided C
    import Cython
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

ext = '.pyx' if USE_CYTHON else '.c'
extensions = [
    Extension('jsonobject.api', ["jsonobject/api" + ext],),
    Extension('jsonobject.base', ["jsonobject/base" + ext],),
    Extension('jsonobject.base_properties', ["jsonobject/base_properties" + ext],),
    Extension('jsonobject.containers', ["jsonobject/containers" + ext],),
    Extension('jsonobject.properties', ["jsonobject/properties" + ext],),
    Extension('jsonobject.utils', ["jsonobject/utils" + ext],),
]

if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)


with io.open('README.md', 'rt', encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name='jsonobject',
    version='0.8.0a2',
    author='Danny Roberts',
    author_email='droberts@dimagi.com',
    description='A library for dealing with JSON as python objects',
    long_description=long_description,
    url='https://github.com/dannyroberts/jsonobject',
    packages=['jsonobject'],
    setup_requires=['cython'],
    install_requires=['six'],
    tests_require=['unittest2'],
    ext_modules=extensions,
    test_suite='test',
)
