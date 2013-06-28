import unittest
from jsonobject import JsonObject, StringProperty, ListProperty, JsonArray, ObjectProperty


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


if __name__ == '__main__':
    unittest.main()
