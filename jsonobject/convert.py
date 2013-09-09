"""
This file was excerpted directly from couchdbkit.schema.properties
and edited to fit the needs of jsonobject

"""
from collections import MutableSet
import decimal
import datetime

from . import properties
from jsonobject.exceptions import BadValueError
import re


re_date = re.compile('^(\d{4})\D?(0[1-9]|1[0-2])\D?([12]\d|0[1-9]|3[01])$')
re_time = re.compile('^([01]\d|2[0-3])\D?([0-5]\d)\D?([0-5]\d)?\D?(\d{3})?$')
re_datetime = re.compile(r'^(\d{4})\D?(0[1-9]|1[0-2])\D?([12]\d|0[1-9]|3[01])('
                         '\D?([01]\d|2[0-3])\D?([0-5]\d)\D?([0-5]\d)?\D?(\d{3})?'
                         '([zZ]|([\+-])([01]\d|2[0-3])\D?([0-5]\d)?)?)?$')
re_decimal = re.compile('^(\d+)\.(\d+)$')


ALLOWED_PROPERTY_TYPES = set([
    basestring,
    str,
    unicode,
    bool,
    int,
    long,
    float,
    datetime.datetime,
    datetime.date,
    datetime.time,
    decimal.Decimal,
    dict,
    list,
    set,
    type(None)
])

MAP_TYPES_PROPERTIES = {
    decimal.Decimal: properties.DecimalProperty,
    datetime.datetime: properties.DateTimeProperty,
    datetime.date: properties.DateProperty,
    datetime.time: properties.TimeProperty,
    str: properties.StringProperty,
    unicode: properties.StringProperty,
    basestring: properties.StringProperty,
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
            raise BadValueError('value {0!r} not in allowed types: {1!r}'.format(
                value,
                MAP_TYPES_PROPERTIES.keys(),
            ))


def is_type_ok(item_type, value_type):
    return item_type is None or item_type == value_type


def value_to_python(value, item_type=None):
    """convert a json value to python type using regexp. values converted
    have been put in json via `value_to_json` .
    """
    data_type = None
    if isinstance(value, basestring):
        if re_date.match(value) and is_type_ok(item_type, datetime.date):
            data_type = datetime.date
        elif re_time.match(value) and is_type_ok(item_type, datetime.time):
            data_type = datetime.time
        elif re_datetime.match(value) and is_type_ok(item_type, datetime.datetime):
            data_type = datetime.datetime
        elif re_decimal.match(value) and is_type_ok(item_type, decimal.Decimal):
            data_type = decimal.Decimal
        if data_type is not None:
            prop = MAP_TYPES_PROPERTIES[data_type]()
            try:
                #sometimes regex fail so return value
                value = prop.to_python(value)
            except:
                pass
    elif isinstance(value, (list, dict, MutableSet)):
        raise NotImplementedError()
    return value
