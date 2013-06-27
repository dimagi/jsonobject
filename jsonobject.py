import inspect


class JsonProperty(object):
    def __init__(self, default=None):
        self.default = default


class AssertTypeProperty(JsonProperty):
    _type = None

    def assert_type(self, obj):
        assert isinstance(obj, self._type)
        return obj

    wrap = unwrap = assert_type


class StringProperty(AssertTypeProperty):
    _type = basestring


class IntegerProperty(AssertTypeProperty):
    _type = int


class ObjectProperty(JsonProperty):
    def __init__(self, obj_type, **kwargs):
        super(ObjectProperty, self).__init__(**kwargs)
        self._obj_type = obj_type

    @property
    def obj_type(self):
        if inspect.isfunction(self._obj_type):
            return self._obj_type()
        else:
            return self._obj_type

    def wrap(self, obj):
        return self.obj_type.wrap(obj)

    def unwrap(self, obj):
        assert isinstance(obj, self.obj_type),\
            '{} is not an instance of {}'.format(obj, self.obj_type)
        return obj._obj


class ListProperty(ObjectProperty):

    def wrap(self, obj):
        return JsonArray(obj, wrapper=type_to_property(self.obj_type))

    def unwrap(self, obj):
        assert isinstance(obj, (JsonArray, list))

        if isinstance(obj, JsonArray):
            return obj._obj
        else:
            wrapped = self.wrap([])
            wrapped.extend(obj)
            return wrapped, self.unwrap(wrapped)


class JsonArray(list):
    def __init__(self, obj, wrapper=None):
        super(JsonArray, self).__init__()
        self._obj = obj
        self._wrapper = wrapper
        for item in self._obj:
            super(JsonArray, self).append(self._wrapper.wrap(item))

    def to_json(self):
        return self._obj

    def append(self, wrapped):
        self._obj.append(self._wrapper.unwrap(wrapped))
        super(JsonArray, self).append(wrapped)

    def extend(self, wrapped_list):
        self._obj.extend(map(self._wrapper.unwrap, wrapped_list))
        super(JsonArray, self).extend(wrapped_list)


class JsonObjectMeta(type):
    def __new__(mcs, name, bases, dct):
        wrappers = {}
        for key, value in dct.items():
            if isinstance(value, JsonProperty):
                wrappers[key] = value
                del dct[key]
        for base in bases:
            if getattr(base, '_wrappers', None):
                for key, value in base._wrappers.items():
                    if key not in wrappers:
                        wrappers[key] = value
        cls = type.__new__(mcs, name, bases, dct)
        cls._wrappers = wrappers
        return cls


class JsonObject(dict):

    __metaclass__ = JsonObjectMeta

    _wrappers = None

    def __init__(self, **kwargs):
        super(JsonObject, self).__init__()
        self._obj = kwargs
        for key, value in self._wrappers.items():
            if value.default and 'key' not in self._obj:
                self[key] = value.default
        for key, value in self._obj.items():
            self[key] = self.__wrap(key, value)

    @classmethod
    def wrap(cls, obj):
        return cls(**obj)

    def to_json(self):
        return self._obj

    def __wrap(self, key, value):
        try:
            wrapper = self._wrappers[key]
        except (TypeError, KeyError):
            if isinstance(value, JsonProperty):
                # this shouldn't happen
                raise
            return value
        else:
            return wrapper.wrap(value)

    def __unwrap(self, key, value):
        try:
            wrapper = self._wrappers[key]
        except (TypeError, KeyError):
            return value
        else:
            return wrapper.unwrap(value)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, key, value):
        if key in self._wrappers:
            unwrapped = self.__unwrap(key, value)
            if isinstance(unwrapped, tuple):
                value, unwrapped = unwrapped
            self[key] = value
            self._obj[key] = unwrapped
        else:
            super(JsonObject, self).__setattr__(key, value)

TYPE_TO_PROPERTY = {
    int: IntegerProperty,
    basestring: StringProperty
}


def type_to_property(obj_type):
    if issubclass(obj_type, JsonObject):
        return ObjectProperty(obj_type)
    elif obj_type in TYPE_TO_PROPERTY:
        return TYPE_TO_PROPERTY[obj_type]()
    else:
        for key, value in TYPE_TO_PROPERTY.items():
            if issubclass(obj_type, key):
                return value()
        raise TypeError('Type {} not recognized'.format(obj_type))