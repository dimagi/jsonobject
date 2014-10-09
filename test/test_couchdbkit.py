from __future__ import absolute_import
import json
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from .couchdbkit.application import Application


class CouchdbkitTestCase(unittest.TestCase):
    def _test(self, name):
        with open(os.path.join('test', 'couchdbkit', 'data', '{0}.json'.format(name))) as f:
            Application.wrap(json.load(f))

    def test_basic(self):
        self._test('basic')

    def test_medium(self):
        self._test('medium')

    def test_large(self):
        self._test('large')

    def test_multimedia_map(self):
        self._test('multimedia_map')
