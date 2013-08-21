# DateTimeProperty, DateProperty, and TimeProperty
# include code copied from couchdbkit
import datetime
import time
import decimal
from jsonobject.base import AssertTypeProperty, JsonProperty, JsonArray, JsonObject, JsonContainerProperty, JsonDict, AbstractDateProperty


class StringProperty(AssertTypeProperty):
    _type = basestring


class BooleanProperty(AssertTypeProperty):
    _type = bool


class IntegerProperty(AssertTypeProperty):
    _type = int


class FloatProperty(AssertTypeProperty):
    _type = float


class DecimalProperty(JsonProperty):

    def wrap(self, obj):
        return decimal.Decimal(obj)

    def unwrap(self, obj):
        assert isinstance(obj, decimal.Decimal)
        return obj, unicode(obj)


class DateProperty(AbstractDateProperty):

    _type = datetime.date

    def _wrap(self, value):
        try:
            value = datetime.date(*time.strptime(value, '%Y-%m-%d')[:3])
        except ValueError, e:
            raise ValueError('Invalid ISO date %r [%s]' % (value, str(e)))
        return value

    def _unwrap(self, value):
        return value, value.isoformat()


class DateTimeProperty(AbstractDateProperty):

    _type = datetime.datetime

    def _wrap(self, value):
        try:
            value = value.split('.', 1)[0]  # strip out microseconds
            value = value[0:19]  # remove timezone
            value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
        except ValueError, e:
            raise ValueError('Invalid ISO date/time %r [%s]' % (value, str(e)))
        return value

    def _unwrap(self, value):
        return value, value.replace(microsecond=0).isoformat() + 'Z'


class TimeProperty(AbstractDateProperty):

    _type = datetime.time

    def _wrap(self, time_string):
        return datetime.datetime.strptime(time_string, self.FORMAT).time()

    def _unwrap(self, time):
        return time, time.strftime(self.FORMAT)

    def _wrap(self, value):
        try:
            value = value.split('.', 1)[0]  # strip out microseconds
            value = datetime.time(*time.strptime(value, '%H:%M:%S')[3:6])
        except ValueError, e:
            raise ValueError('Invalid ISO time %r [%s]' % (value, str(e)))
        return value

    def _unwrap(self, value):
        return value, value.replace(microsecond=0).isoformat()


class ObjectProperty(JsonContainerProperty):

    default = lambda self: self.obj_type()

    def wrap(self, obj):
        return self.obj_type.wrap(obj)

    def unwrap(self, obj):
        assert isinstance(obj, self.obj_type), \
            '{0} is not an instance of {1}'.format(obj, self.obj_type)
        return obj, obj._obj


class ListProperty(JsonContainerProperty):

    default = list

    def wrap(self, obj):
        return JsonArray(obj, wrapper=type_to_property(self.obj_type))

    def unwrap(self, obj):
        assert isinstance(obj, list), \
            '{0} is not an instance of list'.format(obj)

        if isinstance(obj, JsonArray):
            return obj, obj._obj
        else:
            wrapped = self.wrap([])
            wrapped.extend(obj)
            return self.unwrap(wrapped)


class DictProperty(JsonContainerProperty):

    default = dict

    def wrap(self, obj):
        wrapper = type_to_property(self.obj_type) if self.obj_type else None
        return JsonDict(obj, wrapper)

    def unwrap(self, obj):
        if isinstance(obj, JsonDict):
            return obj, obj._obj
        else:
            wrapped = self.wrap({})
            wrapped.update(obj)
            return self.unwrap(wrapped)


def type_to_property(obj_type, *args, **kwargs):
    from .convert import MAP_TYPES_PROPERTIES
    if issubclass(obj_type, JsonObject):
        return ObjectProperty(obj_type, *args, **kwargs)
    elif obj_type in MAP_TYPES_PROPERTIES:
        return MAP_TYPES_PROPERTIES[obj_type](*args, **kwargs)
    else:
        for key, value in MAP_TYPES_PROPERTIES.items():
            if issubclass(obj_type, key):
                return value(*args, **kwargs)
        raise TypeError('Type {0} not recognized'.format(obj_type))
