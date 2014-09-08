from decimal import Decimal
import datetime
from jsonobject import JsonObject, ObjectProperty
import unittest2


class StringConversionsTest(unittest2.TestCase):

    EXAMPLES = {
        'decimal': '1.2',
        'date': '2014-02-04',
        'dict': {
            'decimal': '1.4',
        },
        'list': ['1.0', '2000-01-01'],
    }
    EXAMPLES_CONVERTED = {
        'decimal': Decimal('1.2'),
        'date': datetime.date(2014, 2, 4),
        'dict': {
            'decimal': Decimal('1.4'),
        },
        'list': [Decimal('1.0'), datetime.date(2000, 01, 01)],
    }

    def test_default_conversions(self):
        class Foo(JsonObject):
            pass
        foo = Foo.wrap(self.EXAMPLES)
        for key, value in self.EXAMPLES_CONVERTED.items():
            self.assertEqual(getattr(foo, key), value)

    def test_no_conversions(self):
        class Foo(JsonObject):
            class Meta(object):
                string_conversions = ()

        foo = Foo.wrap(self.EXAMPLES)
        for key, value in self.EXAMPLES.items():
            self.assertEqual(getattr(foo, key), value)

    def test_nested_1(self):

        class Bar(JsonObject):
            # default string conversions
            pass

        class Foo(JsonObject):
            bar = ObjectProperty(Bar)

            class Meta(object):
                string_conversions = ()

        foo = Foo.wrap({
            # don't convert
            'decimal': '1.0',
            # do convert
            'bar': {'decimal': '2.4'}
        })
        self.assertEqual(foo.decimal, '1.0')
        self.assertNotEqual(foo.decimal, Decimal('1.0'))
        self.assertEqual(foo.bar.decimal, Decimal('2.4'))

    def test_nested_2(self):
        class Bar(JsonObject):

            class Meta(object):
                string_conversions = ()

        class Foo(JsonObject):
            # default string conversions
            bar = ObjectProperty(Bar)

        foo = Foo.wrap({
            # do convert
            'decimal': '1.0',
            # don't convert
            'bar': {'decimal': '2.4'}
        })
        self.assertNotEqual(foo.decimal, '1.0')
        self.assertEqual(foo.decimal, Decimal('1.0'))
        self.assertEqual(foo.bar.decimal, '2.4')
