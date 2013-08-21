# DateTimeProperty, DateProperty, and TimeProperty
# include code copied from couchdbkit
import datetime
import time
import decimal
from jsonobject.base import AssertTypeProperty, JsonProperty, JsonArray, JsonObject, JsonContainerProperty, JsonDict


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


class DateProperty(JsonProperty):

    FORMAT = '%Y-%m-%d'

    def wrap(self, date_string):
        return datetime.datetime.strptime(date_string, self.FORMAT).date()

    def unwrap(self, date):
        return date, date.strftime(self.FORMAT)


class DateTimeProperty(JsonProperty):
    FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def wrap(self, datetime_string):
        return datetime.datetime.strptime(datetime_string, self.FORMAT)

    def unwrap(self, datetime):
        return datetime, datetime.strftime(self.FORMAT)


class TimeProperty(JsonProperty):
    FORMAT = '%H:%M:%S'

    def wrap(self, time_string):
        return datetime.datetime.strptime(time_string, self.FORMAT).time()

    def unwrap(self, time):
        return time, time.strftime(self.FORMAT)


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
