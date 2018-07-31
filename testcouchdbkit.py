from __future__ import absolute_import
from __future__ import unicode_literals
from test.couchdbkit.application import Application
import os
import json
from io import open

if __name__ == '__main__':
    name = 'large'
    with open(os.path.join('test', 'couchdbkit', 'data', '{0}.json'.format(name)), encoding='utf-8') as f:
        Application.wrap(json.load(f))
