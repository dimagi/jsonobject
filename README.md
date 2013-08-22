[![Build Status](https://travis-ci.org/dannyroberts/jsonobject.png)](https://travis-ci.org/dannyroberts/jsonobject)

A python library for handling deeply nested JSON objects
as well-schema'd python objects.

It is supposed to be a simpler, more standalone, and faster version
of the DocumentSchema portion of `couchdbkit`

This is just in the hacking stages and the API is not stable.

##Example##

The code below defines a simple user model, and it's natural mapping to JSON.

```python
from jsonobject import *

class User(JsonObject):
    username = StringProperty()
    name = StringProperty()
    active = BooleanProperty(default=False)
    date_joined = DateTimeProperty()
    tags = ListProperty(unicode)

```

Once it is defined, it can be used to wrap or produce deserialized JSON.

```python
>>> user1 = User(
    name='John Doe',
    username='jdoe',
    date_joined=datetime.datetime.utcnow(),
    tags=['generic', 'anonymous']
)
>>> user1.to_json()
{
    'name': 'John Doe',
    'username': 'jdoe',
    'active': False,
    'date_joined': '2013-08-05T02:46:58Z',
    'tags': ['generic', 'anonymous']
}
```

Notice that the datetime is converted to an ISO format string in JSON, but is a real datetime on the object:

```python
>>> user1.date_joined
datetime.datetime(2013, 8, 5, 2, 46, 58, 451286)
```

##Performance Comparison with Couchdbkit##
In order to do a direct comparison with couchdbkit, the test suite includes a large sample schema originally written with couchdbkit. It is easy to swap in jsonobject for couchdbkit and run the tests with each. Here are the results:
```
$ python -m unittest test.test_couchdbkit
....
----------------------------------------------------------------------
Ran 4 tests in 1.403s

OK
$ python -m unittest test.test_couchdbkit
....
----------------------------------------------------------------------
Ran 4 tests in 0.153s

OK


```
