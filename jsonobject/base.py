import copy
import inspect
from jsonobject.exceptions import DeleteNotAllowed, BadValueError


class JsonProperty(object):

    default = None

    def __init__(self, default=Ellipsis, name=None, choices=None, required=False,
                 exclude_if_none=False):
        self.name = name
        if default is Ellipsis:
            default = self.default
        if callable(default):
            self.default = default
        else:
            self.default = lambda: default
        self.choices = choices
        self.required = required
        self.exclude_if_none = exclude_if_none

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

    def exclude(self, value):
        return self.exclude_if_none and not value

    def empty(self, value):
        return value is None

    def validate(self, value):
        if self.choices and value not in self.choices and value is not None:
            raise BadValueError(
                '{0!r} not in choices: {1!r}'.format(value, self.choices)
            )
        if self.empty(value) and self.required:
            raise BadValueError(
                'Property {0} is required.'.format(self.name)
            )
        if hasattr(value, 'validate'):
            value.validate()


class JsonContainerProperty(JsonProperty):

    _type = default = None
    container_class = None

    def __init__(self, item_type=None, **kwargs):
        from convert import ALLOWED_PROPERTY_TYPES
        if inspect.isfunction(item_type):
            item_type = item_type()
        else:
            item_type = item_type
        self.item_type = item_type
        if item_type and item_type not in tuple(ALLOWED_PROPERTY_TYPES) \
                and not issubclass(item_type, JsonObject):
            raise ValueError("item_type {0!r} not in {1!r}".format(
                item_type,
                ALLOWED_PROPERTY_TYPES,
            ))
        super(JsonContainerProperty, self).__init__(**kwargs)

    def empty(self, value):
        return not value

    def wrap(self, obj):
        from properties import type_to_property
        wrapper = type_to_property(self.item_type) if self.item_type else None
        return self.container_class(obj, wrapper=wrapper)

    def unwrap(self, obj):
        if not isinstance(obj, self._type):
            raise BadValueError(
                '{0} is not an instance of {1}'.format(obj, self._type.__name__)
            )
        if isinstance(obj, self.container_class):
            return obj, obj._obj
        else:
            wrapped = self.wrap(self._type())
            self._update(wrapped, obj)
            return self.unwrap(wrapped)

    def _update(self, container, extension):
        raise NotImplementedError()

class DefaultProperty(JsonProperty):
    def wrap(self, obj):
        from . import convert
        from properties import DictProperty
        from properties import ListProperty
        if isinstance(obj, dict):
            property_ = DictProperty()
        elif isinstance(obj, list):
            property_ = ListProperty()
        else:
            value = convert.value_to_python(obj)
            property_ = convert.value_to_property(value)

        if property_:
            return property_.wrap(obj)

    def unwrap(self, obj):
        from . import convert
        from properties import DictProperty
        from properties import ListProperty
        if isinstance(obj, dict):
            property_ = DictProperty()
        elif isinstance(obj, list):
            property_ = ListProperty()
        else:
            property_ = convert.value_to_property(obj)

        if property_:
            return property_.unwrap(obj)
        else:
            return obj, None


class AssertTypeProperty(JsonProperty):
    _type = None

    def assert_type(self, obj):
        if not isinstance(obj, self._type):
            raise BadValueError('{0} not of type {1}'.format(obj, self._type))

    def wrap(self, obj):
        self.assert_type(obj)
        return obj

    def unwrap(self, obj):
        self.assert_type(obj)
        return obj, obj


class AbstractDateProperty(JsonProperty):

    _type = None

    def wrap(self, obj):
        try:
            if not isinstance(obj, basestring):
                raise ValueError()
            return self._wrap(obj)
        except ValueError:
            raise BadValueError('{0!r} is not a {1}-formatted string'.format(
                obj,
                self._type.__name__,
            ))

    def unwrap(self, obj):
        if not isinstance(obj, self._type):
            raise BadValueError('{0!r} is not a {1} object'.format(
                obj,
                self._type.__name__,
            ))
        return self._unwrap(obj)

    def _wrap(self, obj):
        raise NotImplementedError()

    def _unwrap(self, obj):
        raise NotImplementedError()


def check_type(obj, item_type, message):
    if obj is None:
        return item_type()
    elif not isinstance(obj, item_type):
        raise BadValueError(message)
    else:
        return obj


class JsonArray(list):
    def __init__(self, _obj=None, wrapper=None):
        super(JsonArray, self).__init__()

        self._obj = check_type(_obj, list, 'JsonArray must wrap a list or None')
        self._wrapper = wrapper or DefaultProperty()
        for item in self._obj:
            super(JsonArray, self).append(self._wrapper.wrap(item))

    def to_json(self):
        return copy.deepcopy(self._obj)

    def validate(self):
        for obj in self:
            self._wrapper.validate(obj)

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

    def validate(self):
        for obj in self.values():
            self._wrapper.validate(obj)

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


class JsonSet(set):
    def __init__(self, _obj=None, wrapper=None):
        super(JsonSet, self).__init__()
        if isinstance(_obj, set):
            _obj = list(_obj)
        self._obj = check_type(_obj, list, 'JsonSet must wrap a list or None')
        self._wrapper = wrapper or DefaultProperty()

        for item in self._obj:
            super(JsonSet, self).add(self._wrapper.wrap(item))

    def validate(self):
        for obj in self:
            self._wrapper.validate(obj)

    def add(self, wrapped):
        wrapped, unwrapped = self._wrapper.unwrap(wrapped)
        if wrapped not in self:
            self._obj.append(unwrapped)
            super(JsonSet, self).add(wrapped)

    def remove(self, wrapped):
        wrapped, unwrapped = self._wrapper.unwrap(wrapped)
        if wrapped in self:
            self._obj.remove(unwrapped)
            super(JsonSet, self).remove(wrapped)
        else:
            raise KeyError(wrapped)

    def discard(self, wrapped):
        try:
            self.remove(wrapped)
        except KeyError:
            pass

    def pop(self):
        # get first item
        for wrapped in self:
            break
        else:
            raise KeyError()
        wrapped_, unwrapped = self._wrapper.unwrap(wrapped)
        assert wrapped is wrapped_
        self.remove(unwrapped)
        return wrapped

    def clear(self):
        while self:
            self.pop()

    def __ior__(self, other):
        for wrapped in other:
            self.add(wrapped)
        return self

    def update(self, *args):
        for wrapped_list in args:
            self |= set(wrapped_list)

    union_update = update

    def __iand__(self, other):
        for wrapped in list(self):
            if wrapped not in other:
                self.remove(wrapped)
        return self

    def intersection_update(self, *args):
        for wrapped_list in args:
            self &= set(wrapped_list)

    def __isub__(self, other):
        for wrapped in list(self):
            if wrapped in other:
                self.remove(wrapped)
        return self

    def difference_update(self, *args):
        for wrapped_list in args:
            self -= set(wrapped_list)

    def __ixor__(self, other):
        removed = set()
        for wrapped in list(self):
            if wrapped in other:
                self.remove(wrapped)
                removed.add(wrapped)
        self.update(other - removed)
        return self

    def symmetric_difference_update(self, *args):
        for wrapped_list in args:
            self ^= set(wrapped_list)


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
    _validate_lazily = False

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
                setattr(self, key, wrapped)

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

    def validate(self):
        for key, value in self.items():
            self.__get_property(key).validate(value)

    def to_json(self):
        self.validate()
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
        if not self._validate_lazily:
            property_.validate(value)

        if value is None:
            return None, None

        return property_.unwrap(value)

    def __setitem__(self, key, value):
        wrapped, unwrapped = self.__unwrap(key, value)
        super(JsonObject, self).__setitem__(key, wrapped)
        if self.__get_property(key).exclude(unwrapped):
            self._obj.pop(key, None)
        else:
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
