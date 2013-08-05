class JsonProperty(object):

    def __init__(self, default=None, name=None):
        self.name = name
        if not callable(default):
            self.default = lambda: default
        else:
            self.default = default

    def init_property(self, default_name):
        self.name = self.name or default_name

    def wrap(self, obj):
        raise NotImplementedError()

    def unwrap(self, obj):
        raise NotImplementedError()

    def __get__(self, instance, owner):
        assert self.name in instance
        return instance[self.name]

    def __set__(self, instance, value):
        instance[self.name] = value

    def __call__(self, method):
        """
        use a property as a decorator to set its default value

        class Document(JsonObject):
            @StringProperty()
            def doc_type(self):
                return self.__class__.__name__
        """
        self.default = method
        self.name = method.func_name
        return self


class AssertTypeProperty(JsonProperty):
    _type = None

    def assert_type(self, obj):
        assert isinstance(obj, self._type), \
            '{0} not of type {1}'.format(obj, self._type)

    def wrap(self, obj):
        self.assert_type(obj)
        return obj

    def unwrap(self, obj):
        self.assert_type(obj)
        return obj, obj


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
        wrapped, unwrapped = self._wrapper.unwrap(wrapped)
        self._obj.append(unwrapped)
        super(JsonArray, self).append(wrapped)

    def extend(self, wrapped_list):
        if wrapped_list:
            wrapped_list, unwrapped_list = zip(
                *map(self._wrapper.unwrap, wrapped_list)
            )
        else:
            unwrapped_list = []
        self._obj.extend(unwrapped_list)
        super(JsonArray, self).extend(wrapped_list)


class JsonObjectMeta(type):
    def __new__(mcs, name, bases, dct):
        properties = {}
        properties_by_name = {}
        for key, value in dct.items():
            if isinstance(value, JsonProperty):
                properties[key] = value

        cls = type.__new__(mcs, name, bases, dct)

        for key, property_ in properties.items():
            property_.init_property(default_name=key)
            assert property_.name is not None, property_
            assert property_.name not in properties_by_name, \
                'You can only have one property named {0}'.format(property_.name)
            properties_by_name[property_.name] = property_

        for base in bases:
            if getattr(base, '_properties_by_attr', None):
                for key, value in base._properties_by_attr.items():
                    if key not in properties:
                        properties[key] = value
                        properties_by_name[value.name] = value

        cls._properties_by_attr = properties
        cls._properties_by_key = properties_by_name
        return cls


class JsonObject(dict):

    __metaclass__ = JsonObjectMeta

    _properties_by_attr = None
    _properties_by_key = None

    def __init__(self, _obj=None, **kwargs):
        super(JsonObject, self).__init__()

        self._obj = _obj or {}

        for key, value in self._obj.items():
            self[key] = self.__wrap(key, value)

        for attr, value in kwargs.items():
            assert attr in self._properties_by_attr
            setattr(self, attr, value)

        for key, value in self._properties_by_key.items():
            if key not in self._obj:
                try:
                    d = value.default()
                except TypeError:
                    d = value.default(self)
                self[key] = d

    @classmethod
    def wrap(cls, obj):
        self = cls(obj)
        return self

    def to_json(self):
        return self._obj

    def __wrap(self, key, value):
        if value is None:
            return None
        return self._properties_by_key[key].wrap(value)

    def __unwrap(self, key, value):
        if value is None:
            return None, None

        return self._properties_by_key[key].unwrap(value)

    def __setitem__(self, key, value):
        wrapped, unwrapped = self.__unwrap(key, value)
        super(JsonObject, self).__setitem__(key, wrapped)
        self._obj[key] = unwrapped
