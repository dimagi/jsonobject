from setuptools import setup

setup(
    name='jsonobject',
    version='0.2.8',
    author='Danny Roberts',
    author_email='droberts@dimagi.com',
    description='A library for dealing with JSON as python objects',
    long_description=open('README.md').read(),
    url='https://github.com/dannyroberts/jsonobject',
    packages=['jsonobject'],
    install_requires=[],
    tests_require=['unittest2'],
    test_suite='test',
)
