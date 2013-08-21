import inspect
from jsonobject.exceptions import DeleteNotAllowed


class JsonProperty(object):

    default = None

    def __init__(self, default=Ellipsis, name=None, choices=None, required=False):
        self.name = name
        if default is Ellipsis:
            default = self.default
        if callable(default):
            self.default = default
        else:
            self.default = lambda: default
        self.choices = choices
        self.required = required

    def init_property(self, default_name):
        self.name = self.name or default_name

    def wrap(self, obj):
        raise NotImplementedError()

    def unwrap(self, obj):
        """
        must return tuple of (wrapped, unwrapped)

        If obj is already a fully wrapped object,
        it must be returned as the first element.

        For an example where the first element is relevant see ListProperty

        """
        raise NotImplementedError()

    def to_json(self, value):
        _, unwrapped = self.unwrap(value)
        return unwrapped

    def to_python(self, value):
        return self.wrap(value)

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
        assert self.default() is None
        self.default = method
        self.name = self.name or method.func_name
        return self

    def empty(self, value):
        return value is None

    def validate(self, value):
        if self.choices and value not in self.choices and value is not None:
            raise ValueError(
                '{0!r} not in choices: {1!r}'.format(value, self.choices)
            )
        if self.empty(value) and self.required:
            raise ValueError(
                'Required property received value {0!r}'.format(value)
            )


class JsonContainerProperty(JsonProperty):

    def __init__(self, obj_type=None, **kwargs):
        self._obj_type = obj_type
        super(JsonContainerProperty, self).__init__(**kwargs)

    @property
    def obj_type(self):
        if inspect.isfunction(self._obj_type):
            return self._obj_type()
        else:
            return self._obj_type


class DefaultProperty(JsonProperty):
    def wrap(self, obj):
        from . import convert
        return convert.value_to_python(obj)

    def unwrap(self, obj):
        from . import convert
        return convert.value_to_python(obj), convert.value_to_json(obj)


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


def check_type(obj, obj_type, message):
    if obj is None:
        return obj_type()
    elif not isinstance(obj, obj_type):
        raise ValueError(message)
    else:
        return obj


class JsonArray(list):
    def __init__(self, _obj=None, wrapper=None):
        super(JsonArray, self).__init__()

        self._obj = check_type(_obj, list, 'JsonArray must wrap a list or None')
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


class SimpleDict(dict):
    """
    Re-implements destructive methods of dict
    to use only setitem and getitem and delitem
    """
    def update(self, E=None, **F):
        for dct in (E, F):
            if dct:
                for key, value in dct.items():
                    self[key] = value

    def clear(self):
        for key in self.keys():
            del self[key]


class JsonDict(SimpleDict):

    def __init__(self, _obj=None, wrapper=None):
        super(JsonDict, self).__init__()
        self._obj = check_type(_obj, dict, 'JsonDict must wrap a dict or None')
        self._wrapper = wrapper or DefaultProperty()

        for key, value in self._obj.items():
            self[key] = self.__wrap(key, value)

    def __wrap(self, key, unwrapped):
        return self._wrapper.wrap(unwrapped)

    def __unwrap(self, key, wrapped):
        return self._wrapper.unwrap(wrapped)

    def __setitem__(self, key, value):
        wrapped, unwrapped = self.__unwrap(key, value)
        self._obj[key] = unwrapped
        super(JsonDict, self).__setitem__(key, wrapped)

    def __delitem__(self, key):
        del self._obj[key]
        super(JsonDict, self).__delitem__(key)


class JsonObjectMeta(type):
    # There's a pretty fundamental cyclic dependency between this metaclass
    # and knowledge of all available property types (in properties module).
    # The current solution is to monkey patch this metaclass
    # with a reference to the properties module
    _convert = None

    def __new__(mcs, name, bases, dct):
        _c = mcs._convert
        properties = {}
        properties_by_name = {}
        for key, value in dct.items():
            if isinstance(value, JsonProperty):
                properties[key] = value
            elif key.startswith('_'):
                continue
            elif _c and type(value) in _c.MAP_TYPES_PROPERTIES:
                property_ = _c.MAP_TYPES_PROPERTIES[type(value)](default=value)
                properties[key] = dct[key] = property_

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


class _JsonObjectPrivateInstanceVariables(object):

    def __init__(self, dynamic_properties=None):
        self.dynamic_properties = dynamic_properties or {}


class JsonObject(SimpleDict):

    __metaclass__ = JsonObjectMeta

    _allow_dynamic_properties = True

    _properties_by_attr = None
    _properties_by_key = None

    def __init__(self, _obj=None, **kwargs):
        super(JsonObject, self).__init__()

        setattr(self, '_$', _JsonObjectPrivateInstanceVariables())

        self._obj = check_type(_obj, dict,
                               'JsonObject must wrap a dict or None')

        for key, value in self._obj.items():
            wrapped = self.__wrap(key, value)
            if key in self._properties_by_key:
                self[key] = wrapped
            else:
                # these should be added as attributes
                setattr(self, key, value)

        for attr, value in kwargs.items():
            setattr(self, attr, value)

        for key, value in self._properties_by_key.items():
            if key not in self._obj:
                try:
                    d = value.default()
                except TypeError:
                    d = value.default(self)
                self[key] = d

    @property
    def __dynamic_properties(self):
        return getattr(self, '_$').dynamic_properties

    @classmethod
    def wrap(cls, obj):
        self = cls(obj)
        return self

    def to_json(self):
        return self._obj

    def __get_property(self, key):
        try:
            return self._properties_by_key[key]
        except KeyError:
            return DefaultProperty()

    def __wrap(self, key, value):
        property_ = self.__get_property(key)

        if value is None:
            return None

        return property_.wrap(value)

    def __unwrap(self, key, value):
        property_ = self.__get_property(key)
        property_.validate(value)

        if value is None:
            return None, None

        return property_.unwrap(value)

    def __setitem__(self, key, value):
        wrapped, unwrapped = self.__unwrap(key, value)
        super(JsonObject, self).__setitem__(key, wrapped)
        self._obj[key] = unwrapped
        if key not in self._properties_by_key:
            assert key not in self._properties_by_attr
            self.__dynamic_properties[key] = wrapped
            super(JsonObject, self).__setattr__(key, wrapped)

    def __is_dynamic_property(self, name):
        return (
            name not in self._properties_by_attr and
            not name.startswith('_')
        )

    def __setattr__(self, name, value):
        if self.__is_dynamic_property(name):
            if self._allow_dynamic_properties:
                self[name] = value
            else:
                raise AttributeError(
                    "{0} is not defined in schema "
                    "(not a valid property)".format(name)
                )
        else:
            super(JsonObject, self).__setattr__(name, value)

    def __delitem__(self, key):
        if key in self._properties_by_key:
            raise DeleteNotAllowed(key)
        else:
            del self._obj[key]
            super(JsonObject, self).__delitem__(key)
            super(JsonObject, self).__delattr__(key)

    def __delattr__(self, name):
        if name in self._properties_by_attr:
            raise DeleteNotAllowed(name)
        else:
            del self[name]

    def __repr__(self):
        name = self.__class__.__name__
        predefined_properties = self._properties_by_attr.keys()
        predefined_property_keys = set(self._properties_by_attr[p].name for p in predefined_properties)
        dynamic_properties = set(self.keys()) - predefined_property_keys
        properties = sorted(predefined_properties) + sorted(dynamic_properties)
        return u'{name}({keyword_args})'.format(
            name=name,
            keyword_args=', '.join('{key}={value!r}'.format(
                key=key,
                value=getattr(self, key))
            for key in properties),
        )


def get_dynamic_properties(obj):
    return getattr(obj, '_$').dynamic_properties.copy()
