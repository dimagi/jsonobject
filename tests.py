from copy import deepcopy
import unittest
from jsonobject.base import JsonObject, JsonArray
from jsonobject import *


class Features(JsonObject):
    hair = StringProperty()
    eyes = StringProperty()


class Person(JsonObject):
    first_name = StringProperty()
    last_name = StringProperty()
    brothers = ListProperty(lambda: Person)
    features = ObjectProperty(Features)
    favorite_numbers = ListProperty(int)

    @property
    def full_name(self):
        return u'{self.first_name} {self.last_name}'.format(self=self)


class JunkCD(JsonObject):
    c_property = IntegerProperty(name='c')
    d_property = StringProperty(name='d')


class JunkAB(JsonObject):
    a_property = ListProperty(int, name='a')
    b_property = ObjectProperty(JunkCD, name='b')

class JsonObjectTestCase(unittest.TestCase):
    def test_wrap(self):
        data = {
            'first_name': 'Danny',
            'last_name': 'Roberts',
            'brothers': [{
                'first_name': 'Alex',
                'last_name': 'Roberts',
            }, {
                'first_name': 'Nicky',
                'last_name': 'Roberts',
            }],
            'features': {'hair': 'brown', 'eyes': 'brown'},
            'favorite_numbers': [1, 1, 2, 3, 5, 8],
        }
        danny = Person.wrap(data)
        self.assertEqual(danny.first_name, 'Danny')
        self.assertEqual(danny.last_name, 'Roberts')
        self.assertEqual(danny.brothers[0].full_name, 'Alex Roberts')
        self.assertEqual(danny.brothers[1].full_name, 'Nicky Roberts')
        self.assertEqual(danny.features.hair, 'brown')
        self.assertEqual(danny.features.eyes, 'brown')

        danny.brothers[1].first_name = 'Nick'
        self.assertEqual(danny.brothers[1].full_name, 'Nick Roberts')

        brothers = [{
            'first_name': 'Alex',
            'last_name': 'Roberts',
        }, {
            'first_name': 'Nicky',
            'last_name': 'Roberts',
        }]
        with self.assertRaises(AssertionError):
            danny.brothers = brothers

        brothers = map(Person.wrap, brothers)
        danny.brothers = brothers

        self.assertEqual(danny.brothers, brothers)
        self.assertTrue(isinstance(danny.brothers, JsonArray))
        self.assertEqual(danny.to_json(), data)

        danny.features.hair = 'green'
        self.assertEqual(danny.features.hair, 'green')

        features = {'hair': 'blue', 'eyes': 'blue'}
        with self.assertRaises(AssertionError):
            danny.features = features

        features = Features.wrap(features)
        danny.features = features
        self.assertEqual(danny.features, {'hair': 'blue', 'eyes': 'blue'})

        numbers = [1, 2, 3, 4, 5]
        danny.favorite_numbers = numbers
        self.assertEqual(danny.favorite_numbers, numbers)
        self.assertEqual(danny.to_json()['favorite_numbers'], numbers)

    def test_default(self):
        p = Person()
        self.assertEqual(p.to_json(), {
            'first_name': None,
            'last_name': None,
            'brothers': [],
            'features': {'hair': None, 'eyes': None},
            'favorite_numbers': [],
        })

    def test_name(self):
        class Wack(JsonObject):
            underscore_obj = StringProperty(name='_obj')
        w = Wack()
        self.assertEqual(w.to_json(), {'_obj': None})
        w.underscore_obj = 'new_value'
        self.assertEqual(w.underscore_obj, 'new_value')
        self.assertEqual(w.to_json(), {'_obj': 'new_value'})

    def test_mapping(self):

        json_end = {
            'a': [1, 2, 3],
            'b': {
                'c': 1,
                'd': 'string',
            }
        }

        p = JunkAB(deepcopy(json_end))
        self.assertEqual(p.to_json(), json_end)
        p.a_property.append(4)
        self.assertEqual(p.to_json(), {'a': [1, 2, 3, 4], 'b': json_end['b']})
        p.a_property = []
        self.assertEqual(p.to_json(), {'a': [], 'b': json_end['b']})
        p.a_property = None
        self.assertEqual(p.to_json(), {'a': None, 'b': json_end['b']})
        p['a'] = [1, 2, 3]
        self.assertEqual(p.to_json(), json_end)
        self.assertEqual(p.keys(), p.to_json().keys())

    def test_competing_names(self):
        with self.assertRaises(AssertionError):
            class Bad(JsonObject):
                a = IntegerProperty(name='ay')
                eh = StringProperty(name='ay')

    def test_init(self):
        self.assertEqual(JunkCD(c_property=1, d_property='yyy').to_json(),
                         JunkCD({'c': 1, 'd': 'yyy'}).to_json())
        with self.assertRaises(AssertionError):
            JunkCD(non_existent_property=2)

        ab = JunkAB(a_property=[1, 2, 3],
                    b_property=JunkCD({'c': 1, 'd': 'string'}))
        self.assertEqual(ab.to_json(), {
            'a': [1, 2, 3],
            'b': {
                'c': 1,
                'd': 'string',
            }
        })


class PropertyTestCase(unittest.TestCase):
    def test_date(self):
        import datetime
        p = DateProperty()
        for string, date in [('1988-07-07', datetime.date(1988, 7, 7))]:
            self.assertEqual(p.wrap(string), date)
            self.assertEqual(p.unwrap(date), string)
        with self.assertRaises(ValueError):
            p.wrap('1234-05-90')
        with self.assertRaises(ValueError):
            p.wrap('2000-01-01T00:00:00Z')

    def test_datetime(self):
        import datetime
        p = DatetimeProperty()
        for string, dt in [('2011-01-18T12:38:09Z', datetime.datetime(2011, 1, 18, 12, 38, 9))]:
            self.assertEqual(p.wrap(string), dt)
            self.assertEqual(p.unwrap(dt), string)
        with self.assertRaises(ValueError):
            p.wrap('1234-05-90T00:00:00Z')
        with self.assertRaises(ValueError):
            p.wrap('1988-07-07')


if __name__ == '__main__':
    unittest.main()
