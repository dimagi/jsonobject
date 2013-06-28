import inspect


class JsonProperty(object):

    def __init__(self, default=None):
        if not callable(default):
            self.default = lambda: default
        else:
            self.default = default


class AssertTypeProperty(JsonProperty):
    _type = None

    def assert_type(self, obj):
        assert isinstance(obj, self._type), \
            '{} not of type {}'.format(obj, self._type)
        return obj

    wrap = unwrap = assert_type


class StringProperty(AssertTypeProperty):
    _type = basestring


class IntegerProperty(AssertTypeProperty):
    _type = int


class ObjectProperty(JsonProperty):
    def __init__(self, obj_type, default=Ellipsis):
        self._obj_type = obj_type
        if default is Ellipsis:
            default = self.obj_type
        super(ObjectProperty, self).__init__(default=default)


    @property
    def obj_type(self):
        if inspect.isfunction(self._obj_type):
            return self._obj_type()
        else:
            return self._obj_type

    def wrap(self, obj):
        return self.obj_type.wrap(obj)

    def unwrap(self, obj):
        assert isinstance(obj, self.obj_type), \
            '{} is not an instance of {}'.format(obj, self.obj_type)
        return obj._obj


class ListProperty(ObjectProperty):

    def __init__(self, obj_type, default=Ellipsis):
        if default is Ellipsis:
            default = list
        super(ListProperty, self).__init__(obj_type, default=default)

    def wrap(self, obj):
        return JsonArray(obj, wrapper=type_to_property(self.obj_type))

    def unwrap(self, obj):
        assert isinstance(obj, list), \
            '{} is not an instance of list'.format(obj)

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
        for key, value in self._obj.items():
            self[key] = self.__wrap(key, value)
        for key, value in self._wrappers.items():
            if key not in self._obj:
                d = value.default()
                self[key] = d

    @classmethod
    def wrap(cls, obj):
        return cls(**obj)

    def to_json(self):
        return self._obj

    def __get_wrapper(self, key):
        try:
            return self._wrappers[key]
        except (TypeError, KeyError):
            return None

    def __wrap(self, key, value):
        wrapper = self.__get_wrapper(key)
        if wrapper and value is not None:
            return wrapper.wrap(value)
        else:
            return value

    def __unwrap(self, key, value):
        wrapper = self.__get_wrapper(key)
        if wrapper and value is not None:
            return wrapper.unwrap(value)
        else:
            return value

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, key, value):
        if key in self._wrappers:
            self[key] = value
        else:
            super(JsonObject, self).__setattr__(key, value)

    def __setitem__(self, key, value):
        unwrapped = self.__unwrap(key, value)
        if isinstance(unwrapped, tuple):
            value, unwrapped = unwrapped
        super(JsonObject, self).__setitem__(key, value)
        self._obj[key] = unwrapped

TYPE_TO_PROPERTY = {
    int: IntegerProperty,
    basestring: StringProperty,
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