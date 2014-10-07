from setuptools import setup
import sys
with open('README.md') as readme_file:
    long_description = readme_file.read()

setup(
    name='jsonobject',
    version='0.7.0b1',
    author='Danny Roberts',
    author_email='droberts@dimagi.com',
    description='A library for dealing with JSON as python objects',
    long_description=long_description,
    url='https://github.com/dannyroberts/jsonobject',
    packages=['jsonobject'],
    install_requires=['six'],
    tests_require=['unittest2'] if sys.version_info[0] == 2 else [],
    test_suite='test',
)
