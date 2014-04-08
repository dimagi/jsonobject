from __future__ import absolute_import
from test.couchdbkit.application import Application
import os
import json

if __name__ == '__main__':
    name = 'large'
    with open(os.path.join('test', 'couchdbkit', 'data', '{0}.json'.format(name))) as f:
        Application.wrap(json.load(f))
