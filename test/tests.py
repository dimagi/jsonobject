from copy import deepcopy
import unittest2
from jsonobject.base import JsonObject, JsonArray
from jsonobject import *


class Features(JsonObject):
    hair = StringProperty(choices=['brown', 'blond', 'grey'])
    eyes = StringProperty()


class Document(JsonObject):

    @StringProperty()
    def doc_type(self):
        return self.__class__.__name__


class Person(Document):

    first_name = StringProperty(required=True)
    last_name = StringProperty()
    features = ObjectProperty(Features)
    favorite_numbers = ListProperty(int)
    tags = ListProperty(unicode)

    @property
    def full_name(self):
        return u'{self.first_name} {self.last_name}'.format(self=self)


class FamilyMember(Person):
    base_doc = 'Person'
    brothers = ListProperty(lambda: Person)


class JunkCD(JsonObject):
    c_property = IntegerProperty(name='c')

    @StringProperty(name='d')
    def d_property(self):
        return None


class JunkAB(JsonObject):
    a_property = ListProperty(int, name='a')
    b_property = ObjectProperty(JunkCD, name='b')


class ObjectWithDictProperty(JsonObject):
    mapping = DictProperty()


class JsonObjectTestCase(unittest2.TestCase):
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
            'tags': ['happy', 'know it'],
        }
        danny = FamilyMember.wrap(data)
        self.assertEqual(danny.doc_type, 'FamilyMember')
        self.assertEqual(danny.first_name, 'Danny')
        self.assertEqual(danny.last_name, 'Roberts')
        self.assertEqual(danny.brothers[0].full_name, 'Alex Roberts')
        self.assertEqual(danny.brothers[1].full_name, 'Nicky Roberts')
        self.assertEqual(danny.features.hair, 'brown')
        self.assertEqual(danny.features.eyes, 'brown')
        self.assertEqual(danny.favorite_numbers, [1, 1, 2, 3, 5, 8])
        self.assertEqual(danny.tags, ['happy', 'know it'])

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

        danny.features.hair = 'blond'
        self.assertEqual(danny.features.hair, 'blond')
        with self.assertRaises(ValueError):
            danny.features.hair = 'green'

        features = {'hair': 'grey', 'eyes': 'blue'}
        with self.assertRaises(AssertionError):
            danny.features = features

        features = Features.wrap(features)
        danny.features = features
        self.assertEqual(danny.features, {'hair': 'grey', 'eyes': 'blue'})

        numbers = [1, 2, 3, 4, 5]
        danny.favorite_numbers = numbers
        self.assertEqual(danny.favorite_numbers, numbers)
        self.assertEqual(danny.to_json()['favorite_numbers'], numbers)

    def test_default(self):
        p = FamilyMember(first_name='PJ')
        self.assertEqual(p.to_json(), {
            'doc_type': 'FamilyMember',
            'base_doc': 'Person',
            'first_name': 'PJ',
            'last_name': None,
            'brothers': [],
            'features': {'hair': None, 'eyes': None},
            'favorite_numbers': [],
            'tags': [],
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

    def test_choices(self):

        with self.assertRaises(ValueError):
            Features(hair='blue')
        with self.assertRaises(ValueError):
            Features.wrap({'hair': 'blue'})
        with self.assertRaises(ValueError):
            f = Features()
            f.hair = 'blue'

    def test_required(self):
        with self.assertRaises(ValueError):
            Person()
        with self.assertRaises(ValueError):
            Person(first_name='')
        Person(first_name='James')


class PropertyTestCase(unittest2.TestCase):
    def test_date(self):
        import datetime
        p = DateProperty()
        for string, date in [('1988-07-07', datetime.date(1988, 7, 7))]:
            self.assertEqual(p.wrap(string), date)
            self.assertEqual(p.unwrap(date), (date, string))
        with self.assertRaises(ValueError):
            p.wrap('1234-05-90')
        with self.assertRaises(ValueError):
            p.wrap('2000-01-01T00:00:00Z')

    def test_datetime(self):
        import datetime
        p = DateTimeProperty()
        for string, dt in [('2011-01-18T12:38:09Z', datetime.datetime(2011, 1, 18, 12, 38, 9))]:
            self.assertEqual(p.wrap(string), dt)
            self.assertEqual(p.unwrap(dt), (dt, string))
        with self.assertRaises(ValueError):
            p.wrap('1234-05-90T00:00:00Z')
        with self.assertRaises(ValueError):
            p.wrap('1988-07-07')

    def test_dict(self):
        mapping = {'one': 1, 'two': 2}
        o = ObjectWithDictProperty(mapping=mapping)
        self.assertEqual(o.mapping, mapping)


class User(JsonObject):
    username = StringProperty()
    name = StringProperty()
    active = BooleanProperty(default=False)
    date_joined = DateTimeProperty()
    tags = ListProperty(unicode)


class TestReadmeExamples(unittest2.TestCase):
    def test(self):
        import datetime
        user1 = User(
            name='John Doe',
            username='jdoe',
            date_joined=datetime.datetime(2013, 8, 5, 2, 46, 58),
            tags=['generic', 'anonymous']
        )
        self.assertEqual(
            user1.to_json(), {
                'name': 'John Doe',
                'username': 'jdoe',
                'active': False,
                'date_joined': '2013-08-05T02:46:58Z',
                'tags': ['generic', 'anonymous']
            }
        )
