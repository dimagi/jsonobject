from copy import deepcopy
import unittest2
from jsonobject.base import JsonObject, JsonArray
from jsonobject import *
from jsonobject.exceptions import DeleteNotAllowed, BadValueError


class Features(JsonObject):
    """
    Make sure doc string isn't treated as a property called __doc__!

    """

    hair = StringProperty(choices=['brown', 'blond', 'grey'])
    eyes = StringProperty()


class FeatureMap(JsonObject):
    feature_map = DictProperty(Features)


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
        with self.assertRaises(BadValueError):
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
        from jsonobject.base import get_dynamic_properties
        self.assertEqual(JunkCD(c_property=1, d_property='yyy').to_json(),
                         JunkCD({'c': 1, 'd': 'yyy'}).to_json())
        x = JunkCD(non_existent_property=2)
        self.assertEqual(get_dynamic_properties(x),
                         {'non_existent_property': 2})


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

        with self.assertRaises(BadValueError):
            Features(hair='blue')
        with self.assertRaises(BadValueError):
            Features.wrap({'hair': 'blue'})
        with self.assertRaises(BadValueError):
            f = Features()
            f.hair = 'blue'

    def test_required(self):
        with self.assertRaises(BadValueError):
            Person()
        Person(first_name='')
        Person(first_name='James')

    def test_dynamic_properties(self):
        p = Features.wrap({'platypus': 'James'})
        p.marmot = 'Sally'
        p._nope = 10
        self.assertEqual(p.to_json(), {
            'platypus': 'James',
            'marmot': 'Sally',
            'eyes': None,
            'hair': None,
        })
        self.assertEqual(p.platypus, 'James')
        self.assertEqual(p.marmot, 'Sally')
        self.assertEqual(p._nope, 10)

    def test_delete_dynamic(self):
        def assertReallyThere():
            self.assertEqual(p.a, 1)
            self.assertEqual(p['a'], 1)
            self.assertEqual(p.to_json()['a'], 1)

        def assertReallyDeleted():
            with self.assertRaises(AttributeError):
                p.a
            with self.assertRaises(KeyError):
                p['a']
            with self.assertRaises(KeyError):
                p.to_json()['a']

        # delete attribute
        p = Features.wrap({'a': 1})
        assertReallyThere()
        del p.a
        assertReallyDeleted()

        # delete dict item
        p = Features.wrap({'a': 1})
        assertReallyThere()
        del p['a']
        assertReallyDeleted()

        with self.assertRaises(DeleteNotAllowed):
            del p.hair

        with self.assertRaises(DeleteNotAllowed):
            del p['hair']

    def test_dict_clear(self):
        class Foo(JsonObject):
            dct = DictProperty()
        dct = {'mydict': 'yay'}
        foo = Foo(dct=dct)
        json_dict = foo.dct
        self.assertEqual(json_dict, dct)
        json_dict.clear()
        self.assertEqual(json_dict, {})
        self.assertEqual(json_dict._obj, {})

    def test_dynamic_container(self):
        class Foo(JsonObject):
            pass
        foo = Foo(my_list=[])
        self.assertIs(foo.my_list._obj, foo._obj['my_list'])
        foo = Foo(my_dict={})
        self.assertIs(foo.my_dict._obj, foo._obj['my_dict'])


class PropertyTestCase(unittest2.TestCase):
    def test_date(self):
        import datetime
        p = DateProperty()
        for string, date in [('1988-07-07', datetime.date(1988, 7, 7))]:
            self.assertEqual(p.wrap(string), date)
            self.assertEqual(p.unwrap(date), (date, string))
        with self.assertRaises(BadValueError):
            p.wrap('1234-05-90')
        with self.assertRaises(BadValueError):
            p.wrap('2000-01-01T00:00:00Z')

    def test_datetime(self):
        import datetime
        p = DateTimeProperty()
        for string, dt in [('2011-01-18T12:38:09Z', datetime.datetime(2011, 1, 18, 12, 38, 9))]:
            self.assertEqual(p.wrap(string), dt)
            self.assertEqual(p.unwrap(dt), (dt, string))
        with self.assertRaises(BadValueError):
            p.wrap('1234-05-90T00:00:00Z')
        with self.assertRaises(BadValueError):
            p.wrap('1988-07-07')

    def test_time(self):
        import datetime
        p = TimeProperty()
        for string, time in [('12:38:09', datetime.time(12, 38, 9))]:
            self.assertEqual(p.wrap(string), time)
            self.assertEqual(p.unwrap(time), (time, string))
        with self.assertRaises(BadValueError):
            p.wrap('25:00:00')
        with self.assertRaises(BadValueError):
            p.wrap('2011-01-18T12:38:09Z')
        with self.assertRaises(BadValueError):
            p.wrap('1988-07-07')

    def test_decimal(self):
        import decimal

        class Foo(JsonObject):
            decimal = DecimalProperty()

        foo = Foo(decimal=decimal.Decimal('2.0'))
        self.assertEqual(foo.decimal, decimal.Decimal('2.0'))
        self.assertEqual(foo.to_json()['decimal'], '2.0')

    def test_dict(self):
        mapping = {'one': 1, 'two': 2}
        o = ObjectWithDictProperty(mapping=mapping)
        self.assertEqual(o.mapping, mapping)
        o.mapping.update({'three': 3}, four=4)
        self.assertEqual(o.mapping, {'one': 1, 'two': 2, 'three': 3, 'four': 4})

    def test_typed_dict(self):
        features = FeatureMap({'feature_map': {'lala': {}, 'foo': None}})
        self.assertEqual(features.to_json(), {
            'feature_map': {
                'lala': {'hair': None, 'eyes': None},
                'foo': {'hair': None, 'eyes': None},
            },
        })
        with self.assertRaises(BadValueError):
            FeatureMap({'feature_map': {'lala': 10}})

        features.feature_map.update({'hoho': Features(eyes='brown')})
        self.assertEqual(features.to_json(), {
            'feature_map': {
                'lala': {'hair': None, 'eyes': None},
                'foo': {'hair': None, 'eyes': None},
                'hoho': {'hair': None, 'eyes': 'brown'},
            },
        })

    def test_allow_dynamic(self):
        class Foo(JsonObject):
            _allow_dynamic_properties = False

        foo = Foo()
        with self.assertRaises(AttributeError):
            foo.blah = 3
        foo._blah = 5
        self.assertEqual(foo, {})
        self.assertEqual(foo.to_json(), {})
        self.assertEqual(foo._blah, 5)

    def test_exclude_if_none(self):
        class Foo(JsonObject):
            _id = StringProperty(exclude_if_none=True)
            name = StringProperty()

        foo = Foo()
        self.assertEqual(foo.to_json(), {'name': None})
        self.assertEqual(foo._id, None)
        foo = Foo(_id='xxx')
        self.assertEqual(foo, {'name': None, '_id': 'xxx'})
        foo._id = None
        self.assertEqual(foo.to_json(), {'name': None})
        self.assertEqual(foo._id, None)


class DynamicConversionTestCase(unittest2.TestCase):
    import datetime

    class Foo(JsonObject):
        pass
    string_date = '2012-01-01'
    date_date = datetime.date(2012, 01, 01)

    def _test_dynamic_conversion(self, foo):
        string_date = self.string_date
        date_date = self.date_date

        self.assertEqual(foo.to_json()['my_date'], string_date)
        self.assertEqual(foo.my_date, date_date)

        self.assertEqual(foo.to_json()['my_list'], [1, 2, [string_date]])
        self.assertEqual(foo.my_list, [1, 2, [date_date]])

        self.assertEqual(foo.to_json()['my_dict'], {'a': {'b': string_date}})
        self.assertEqual(foo.my_dict, {'a': {'b': date_date}})

    def test_wrapping(self):
        foo = self.Foo({
            'my_date': self.string_date,
            'my_list': [1, 2, [self.string_date]],
            'my_dict': {'a': {'b': self.string_date}},
        })
        self._test_dynamic_conversion(foo)

    def test_kwargs(self):

        foo = self.Foo(
            my_date=self.date_date,
            my_list=[1, 2, [self.date_date]],
            my_dict={'a': {'b': self.date_date}},
        )
        self._test_dynamic_conversion(foo)

    def test_assignment(self):
        foo = self.Foo()
        foo.my_date = self.date_date
        foo.my_list = [1, 2, [self.date_date]]
        foo.my_dict = {'a': {'b': self.date_date}}
        self._test_dynamic_conversion(foo)

    def test_manipulation(self):
        foo = self.Foo()
        foo.my_date = self.date_date
        foo.my_list = [1, 2, []]
        foo.my_list[2].append(self.date_date)
        foo.my_dict = {'a': {}}
        foo.my_dict['a']['b'] = self.date_date
        self._test_dynamic_conversion(foo)


class User(JsonObject):
    username = StringProperty()
    name = StringProperty()
    active = BooleanProperty(default=False, required=True)
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
