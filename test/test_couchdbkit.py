import json
import os
from unittest2 import TestCase
from test.couchdbkit.application import Application


class CouchdbkitTestCase(TestCase):
    def _test(self, name):
        with open(os.path.join('test', 'couchdbkit', 'data', '{0}.json'.format(name))) as f:
            Application.wrap(json.load(f))

    def test_basic(self):
        self._test('basic')

    def test_medium(self):
        self._test('medium')

    def test_large(self):
        self._test('large')