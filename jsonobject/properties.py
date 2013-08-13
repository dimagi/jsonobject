import datetime
from jsonobject.base import AssertTypeProperty, JsonProperty, JsonArray, JsonObject, JsonObjectMeta, JsonContainerProperty, JsonDict


class StringProperty(AssertTypeProperty):
    _type = basestring


class BooleanProperty(AssertTypeProperty):
    _type = bool


class IntegerProperty(AssertTypeProperty):
    _type = int


class FloatProperty(AssertTypeProperty):
    _type = float


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


TYPE_TO_PROPERTY = {
    int: IntegerProperty,
    basestring: StringProperty,
    bool: BooleanProperty,
    float: FloatProperty,
    datetime.date: DateProperty,
    datetime.datetime: DateTimeProperty,
}


def type_to_property(obj_type, *args, **kwargs):
    if issubclass(obj_type, JsonObject):
        return ObjectProperty(obj_type, *args, **kwargs)
    elif obj_type in TYPE_TO_PROPERTY:
        return TYPE_TO_PROPERTY[obj_type](*args, **kwargs)
    else:
        for key, value in TYPE_TO_PROPERTY.items():
            if issubclass(obj_type, key):
                return value(*args, **kwargs)
        raise TypeError('Type {0} not recognized'.format(obj_type))
