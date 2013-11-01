"""
This file was excerpted directly from couchdbkit.schema.properties
and edited to fit the needs of jsonobject

"""
import decimal
import datetime
import time

from . import properties, FormattedDateTime
from jsonobject.exceptions import BadValueError
import re
from jsonobject.formatted_datetime import FormattedTime


re_date = re.compile(r'^(\d{4})-(0[1-9]|1[0-2])-([12]\d|0[1-9]|3[01])$')
re_time = re.compile(
    r'^([01]\d|2[0-3]):([0-5]\d):(([0-5]\d)(\.(?P<microsecond>\d{1,6}))?)?$'
)
re_datetime = re.compile(
    r'^(\d{4})-(0[1-9]|1[0-2])-([12]\d|0[1-9]|3[01])T'
    r'([01]\d|2[0-3]):([0-5]\d):(([0-5]\d)(\.(?P<microsecond>\d{1,6}))?)?'
    r'(Z|([\+-])([01]\d|2[0-3])(:([0-5]\d))?)?$'
)
re_decimal = re.compile(r'^(\d+)\.(\d+)$')


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
    FormattedDateTime: properties.DateTimeProperty,
    datetime.date: properties.DateProperty,
    datetime.time: properties.TimeProperty,
    FormattedTime: properties.TimeProperty,
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


def _get_microsecond(string, pattern):
    match = pattern.match(string)
    if match:
        microsecond = match.group('microsecond')
    else:
        microsecond = ''

    if microsecond:
        precision = len(microsecond)
        assert 1 <= precision <= 6
        microsecond += '0' * (6 - precision)
        microsecond = int(microsecond)
    else:
        microsecond = 0

    return microsecond


def convert_string_to_datetime(string):
    value = string.split('.', 1)[0]  # strip out microseconds
    value = value[0:19]  # remove timezone
    try:
        value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
    except ValueError, e:
        raise ValueError('Invalid ISO date/time %r [%s]' % (string, str(e)))

    microsecond = _get_microsecond(string, re_datetime)

    return value.replace(microsecond=microsecond)


def convert_string_to_time(string):
    value = string.split('.', 1)[0]  # strip out microseconds
    try:
        value = datetime.time(*time.strptime(value, '%H:%M:%S')[3:6])
    except ValueError, e:
        raise ValueError('Invalid ISO time %r [%s]' % (value, str(e)))

    microsecond = _get_microsecond(string, re_time)

    return value.replace(microsecond=microsecond)


def convert_string_to_date(string):
    try:
        value = datetime.date(*time.strptime(string, '%Y-%m-%d')[:3])
    except ValueError, e:
        raise ValueError('Invalid ISO date %r [%s]' % (string, str(e)))
    return value
