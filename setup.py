from setuptools import setup
import io

with io.open('README.md', 'rt', encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name='jsonobject',
    version='0.7.1',
    author='Danny Roberts',
    author_email='droberts@dimagi.com',
    description='A library for dealing with JSON as python objects',
    long_description=long_description,
    url='https://github.com/dannyroberts/jsonobject',
    packages=['jsonobject'],
    install_requires=['six'],
    tests_require=['unittest2'],
    test_suite='test',
)
