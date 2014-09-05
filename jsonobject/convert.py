"""
This file was excerpted directly from couchdbkit.schema.properties
and edited to fit the needs of jsonobject

"""
from __future__ import absolute_import
import decimal
import datetime

from . import properties
from .exceptions import BadValueError
import re


re_date = re.compile('^(\d{4})\D?(0[1-9]|1[0-2])\D?([12]\d|0[1-9]|3[01])$')
re_time = re.compile('^([01]\d|2[0-3])\D?([0-5]\d)\D?([0-5]\d)?\D?(\d{3})?$')
re_datetime = re.compile(
    r'^(\d{4})\D?(0[1-9]|1[0-2])\D?([12]\d|0[1-9]|3[01])'
    '(\D?([01]\d|2[0-3])\D?([0-5]\d)\D?([0-5]\d)?\D?(\d{3})?'
    '([zZ]|([\+-])([01]\d|2[0-3])\D?([0-5]\d)?)?)?$'
)
re_decimal = re.compile('^(\d+)\.(\d+)$')


MAP_TYPES_PROPERTIES = {
    decimal.Decimal: properties.DecimalProperty,
    datetime.datetime: properties.DateTimeProperty,
    datetime.date: properties.DateProperty,
    datetime.time: properties.TimeProperty,
    str: properties.StringProperty,
    unicode: properties.StringProperty,
    bool: properties.BooleanProperty,
    int: properties.IntegerProperty,
    long: properties.IntegerProperty,
    float: properties.FloatProperty,
    list: properties.ListProperty,
    dict: properties.DictProperty,
    set: properties.SetProperty,
}


def value_to_property(value):
    if value is None:
        return None
    elif type(value) in MAP_TYPES_PROPERTIES:
        prop = MAP_TYPES_PROPERTIES[type(value)]()
        return prop
    else:
        for value_type, prop_class in MAP_TYPES_PROPERTIES.items():
            if isinstance(value, value_type):
                return prop_class()
        else:
            raise BadValueError(
                'value {0!r} not in allowed types: {1!r}'.format(
                    value, MAP_TYPES_PROPERTIES.keys())
            )


STRING_CONVERSIONS = (
    (re_date, properties.DateProperty().to_python),
    (re_time, properties.TimeProperty().to_python),
    (re_datetime, properties.DateTimeProperty().to_python),
    (re_decimal, properties.DecimalProperty().to_python),
)


def value_to_python(value, string_conversions=STRING_CONVERSIONS):
    """
    convert encoded string values to the proper python type

    ex:
    >>> value_to_python('2013-10-09T10:05:51Z')
    datetime.datetime(2013, 10, 9, 10, 5, 51)

    other values will be passed through unmodified
    Note: containers' items are NOT recursively converted

    """
    if isinstance(value, basestring):
        convert = None
        for pattern, _convert in string_conversions:
            if pattern.match(value):
                convert = _convert
                break

        if convert is not None:
            try:
                #sometimes regex fail so return value
                value = convert(value)
            except Exception:
                pass
    return value
