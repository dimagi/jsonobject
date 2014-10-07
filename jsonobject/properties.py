# DateTimeProperty, DateProperty, and TimeProperty
# include code copied from couchdbkit
from __future__ import absolute_import
import datetime
import time
import decimal
from .base_properties import (
    AbstractDateProperty,
    AssertTypeProperty,
    JsonContainerProperty,
    JsonProperty,
)
from .containers import JsonArray, JsonDict, JsonSet
from six import integer_types
import types
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring

class StringProperty(AssertTypeProperty):

    _type = (unicode, str)

    def selective_coerce(self, obj):
        if isinstance(obj, str):
            obj = unicode(obj)
        return obj


class BooleanProperty(AssertTypeProperty):
    _type = bool


class IntegerProperty(AssertTypeProperty):
    _type = integer_types


class FloatProperty(AssertTypeProperty):
    _type = float

    def selective_coerce(self, obj):
        if isinstance(obj, integer_types):
            obj = float(obj)
        return obj


class DecimalProperty(JsonProperty):

    def wrap(self, obj):
        return decimal.Decimal(obj)

    def unwrap(self, obj):
        if isinstance(obj, integer_types):
            obj = decimal.Decimal(obj)
        elif isinstance(obj, float):
            # python 2.6 doesn't allow a float to Decimal
            obj = decimal.Decimal(unicode(obj))
        assert isinstance(obj, decimal.Decimal)
        return obj, unicode(obj)


class DateProperty(AbstractDateProperty):

    _type = datetime.date

    def _wrap(self, value):
        fmt = '%Y-%m-%d'
        try:
            return datetime.date(*time.strptime(value, fmt)[:3])
        except ValueError as e:
            raise ValueError('Invalid ISO date {0!r} [{1}]'.format(value, e))

    def _unwrap(self, value):
        return value, value.isoformat()


class DateTimeProperty(AbstractDateProperty):

    _type = datetime.datetime

    def _wrap(self, value):
        if not self.exact:
            value = value.split('.', 1)[0]  # strip out microseconds
            value = value[0:19]  # remove timezone
            fmt = '%Y-%m-%dT%H:%M:%S'
        else:
            fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError as e:
            raise ValueError(
                'Invalid ISO date/time {0!r} [{1}]'.format(value, e))

    def _unwrap(self, value):
        if not self.exact:
            value = value.replace(microsecond=0)
            padding = ''
        else:
            padding = '' if value.microsecond else '.000000'
        return value, value.isoformat() + padding + 'Z'


class TimeProperty(AbstractDateProperty):

    _type = datetime.time

    def _wrap(self, value):
        if not self.exact:
            value = value.split('.', 1)[0]  # strip out microseconds
            fmt = '%H:%M:%S'
        else:
            fmt = '%H:%M:%S.%f'
        try:
            return datetime.time(*time.strptime(value, fmt)[3:6])
        except ValueError as e:
            raise ValueError('Invalid ISO time {0!r} [{1}]'.format(value, e))

    def _unwrap(self, value):
        if not self.exact:
            value = value.replace(microsecond=0)
        return value, value.isoformat()


class ObjectProperty(JsonContainerProperty):

    default = lambda self: self.item_type()

    def wrap(self, obj, string_conversions=None):
        return self.item_type.wrap(obj)

    def unwrap(self, obj):
        assert isinstance(obj, self.item_type), \
            '{0} is not an instance of {1}'.format(obj, self.item_type)
        return obj, obj._obj


class ListProperty(JsonContainerProperty):

    _type = default = list
    container_class = JsonArray

    def _update(self, container, extension):
        container.extend(extension)


class DictProperty(JsonContainerProperty):

    _type = default = dict
    container_class = JsonDict

    def _update(self, container, extension):
        container.update(extension)


class SetProperty(JsonContainerProperty):

    _type = default = set
    container_class = JsonSet

    def _update(self, container, extension):
        container.update(extension)
