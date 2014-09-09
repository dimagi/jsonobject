from __future__ import absolute_import
from collections import namedtuple, OrderedDict
import copy
import inspect
from .exceptions import (
    BadValueError,
    DeleteNotAllowed,
    WrappingAttributeError,
)


class JsonProperty(object):

    default = None
    type_config = None

    def __init__(self, default=Ellipsis, name=None, choices=None,
                 required=False, exclude_if_none=False, validators=None,
                 verbose_name=None, type_config=None):
        validators = validators or ()
        self.name = name
        if default is Ellipsis:
            default = self.default
        if callable(default):
            self.default = default
        else:
            self.default = lambda: default
        self.choices = choices
        self.choice_keys = []
        if choices:
            for choice in choices:
                if isinstance(choice, tuple):
                    choice, _ = choice
                self.choice_keys.append(choice)
        self.required = required
        self.exclude_if_none = exclude_if_none
        if hasattr(validators, '__iter__'):
            def _validator(value):
                for validator in validators:
                    validator(value)
            self.custom_validator = _validator
        else:
            self.custom_validator = validators
        self.verbose_name = verbose_name
        if type_config:
            self.type_config = type_config

    def init_property(self, default_name, type_config):
        self.name = self.name or default_name
        self.type_config = self.type_config or type_config

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
        if instance:
            assert self.name in instance
            return instance[self.name]
        else:
            return self

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

    def validate(self, value, required=True, recursive=True):
        if (self.choice_keys and value not in self.choice_keys
                and value is not None):
            raise BadValueError(
                '{0!r} not in choices: {1!r}'.format(value, self.choice_keys)
            )

        if not self.empty(value):
            self.custom_validator(value)
        elif required and self.required:
            raise BadValueError(
                'Property {0} is required.'.format(self.name)
            )
        if recursive and hasattr(value, 'validate'):
            value.validate(required=required)


class JsonContainerProperty(JsonProperty):

    _type = default = None
    container_class = None

    def __init__(self, item_type=None, **kwargs):
        self._item_type_deferred = item_type
        super(JsonContainerProperty, self).__init__(**kwargs)

    def init_property(self, **kwargs):
        super(JsonContainerProperty, self).init_property(**kwargs)
        if not inspect.isfunction(self._item_type_deferred):
            # trigger validation
            self.item_type

    def set_item_type(self, item_type):
        if hasattr(item_type, '_type'):
            item_type = item_type._type
        if isinstance(item_type, tuple):
            # this is for the case where item_type = (int, long)
            item_type = item_type[0]
        allowed_types = set(self.type_config.properties.keys())
        if isinstance(item_type, JsonObjectMeta) \
                or not item_type or item_type in allowed_types:
            self._item_type = item_type
        else:
            raise ValueError("item_type {0!r} not in {1!r}".format(
                item_type,
                allowed_types,
            ))

    @property
    def item_type(self):
        if hasattr(self, '_item_type_deferred'):
            if inspect.isfunction(self._item_type_deferred):
                self.set_item_type(self._item_type_deferred())
            else:
                self.set_item_type(self._item_type_deferred)
            del self._item_type_deferred
        return self._item_type

    def empty(self, value):
        return not value

    def wrap(self, obj):
        wrapper = self.type_to_property(self.item_type) if self.item_type else None
        return self.container_class(obj, wrapper=wrapper,
                                    type_config=self.type_config)

    def type_to_property(self, item_type):
        map_types_properties = self.type_config.properties
        from .properties import ObjectProperty
        if issubclass(item_type, JsonObjectBase):
            return ObjectProperty(item_type, type_config=self.type_config)
        elif item_type in map_types_properties:
            return map_types_properties[item_type](type_config=self.type_config)
        else:
            for key, value in map_types_properties.items():
                if issubclass(item_type, key):
                    return value(type_config=self.type_config)
            raise TypeError('Type {0} not recognized'.format(item_type))

    def unwrap(self, obj):
        if not isinstance(obj, self._type):
            raise BadValueError(
                '{0!r} is not an instance of {1!r}'.format(
                    obj, self._type.__name__)
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
        assert self.type_config.string_conversions is not None
        value = self.value_to_python(obj)
        property_ = self.value_to_property(value)

        if property_:
            return property_.wrap(obj)

    def unwrap(self, obj):
        property_ = self.value_to_property(obj)
        if property_:
            return property_.unwrap(obj)
        else:
            return obj, None

    def value_to_property(self, value):
        map_types_properties = self.type_config.properties
        if value is None:
            return None
        elif type(value) in map_types_properties:
            return map_types_properties[type(value)](
                type_config=self.type_config)
        else:
            for value_type, prop_class in map_types_properties.items():
                if isinstance(value, value_type):
                    return prop_class(type_config=self.type_config)
            else:
                raise BadValueError(
                    'value {0!r} not in allowed types: {1!r}'.format(
                        value, map_types_properties.keys())
                )

    def value_to_python(self, value):
        """
        convert encoded string values to the proper python type

        ex:
        >>> DefaultProperty().value_to_python('2013-10-09T10:05:51Z')
        datetime.datetime(2013, 10, 9, 10, 5, 51)

        other values will be passed through unmodified
        Note: containers' items are NOT recursively converted

        """
        if isinstance(value, basestring):
            convert = None
            for pattern, _convert in self.type_config.string_conversions:
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


class AssertTypeProperty(JsonProperty):
    _type = None

    def assert_type(self, obj):
        if not isinstance(obj, self._type):
            raise BadValueError(
                '{0!r} not of type {1!r}'.format(obj, self._type)
            )

    def selective_coerce(self, obj):
        return obj

    def wrap(self, obj):
        obj = self.selective_coerce(obj)
        self.assert_type(obj)
        return obj

    def unwrap(self, obj):
        obj = self.selective_coerce(obj)
        self.assert_type(obj)
        return obj, obj


class AbstractDateProperty(JsonProperty):

    _type = None

    def __init__(self, exact=False, *args, **kwargs):
        super(AbstractDateProperty, self).__init__(*args, **kwargs)
        self.exact = exact

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
    def __init__(self, _obj=None, wrapper=None, type_config=None):
        super(JsonArray, self).__init__()
        self._obj = check_type(_obj, list,
                               'JsonArray must wrap a list or None')

        assert type_config is not None
        self._type_config = type_config
        self._wrapper = (
            wrapper or
            DefaultProperty(type_config=self._type_config)
        )
        for item in self._obj:
            super(JsonArray, self).append(self._wrapper.wrap(item))

    def validate(self, required=True):
        for obj in self:
            self._wrapper.validate(obj, required=required)

    def append(self, wrapped):
        wrapped, unwrapped = self._wrapper.unwrap(wrapped)
        self._obj.append(unwrapped)
        super(JsonArray, self).append(wrapped)

    def __delitem__(self, i):
        super(JsonArray, self).__delitem__(i)
        del self._obj[i]

    def extend(self, wrapped_list):
        if wrapped_list:
            wrapped_list, unwrapped_list = zip(
                *map(self._wrapper.unwrap, wrapped_list)
            )
        else:
            unwrapped_list = []
        self._obj.extend(unwrapped_list)
        super(JsonArray, self).extend(wrapped_list)

    def insert(self, index, wrapped):
        wrapped, unwrapped = self._wrapper.unwrap(wrapped)
        self._obj.insert(index, unwrapped)
        super(JsonArray, self).insert(index, wrapped)

    def remove(self, value):
        i = self.index(value)
        super(JsonArray, self).remove(value)
        self._obj.pop(i)

    def pop(self, index=-1):
        self._obj.pop(index)
        return super(JsonArray, self).pop(index)

    def sort(self, cmp=None, key=None, reverse=False):
        zipped = zip(self, self._obj)
        if key:
            new_key = lambda pair: key(pair[0])
            zipped.sort(key=new_key, reverse=reverse)
        elif cmp:
            new_cmp = lambda pair1, pair2: cmp(pair1[0], pair2[0])
            zipped.sort(cmp=new_cmp, reverse=reverse)
        else:
            zipped.sort(reverse=reverse)

        wrapped_list, unwrapped_list = zip(*zipped)
        while self:
            self.pop()
        super(JsonArray, self).extend(wrapped_list)
        self._obj.extend(unwrapped_list)

    def reverse(self):
        self._obj.reverse()
        super(JsonArray, self).reverse()

    def __fix_slice(self, i, j):
        length = len(self)
        if j < 0:
            j += length
        if i < 0:
            i += length
        if i > length:
            i = length
        if j > length:
            j = length
        return i, j

    def __setslice__(self, i, j, sequence):
        i, j = self.__fix_slice(i, j)
        for _ in range(j - i):
            self.pop(i)
        for k, wrapped in enumerate(sequence):
            self.insert(i + k, wrapped)

    def __delslice__(self, i, j):
        i, j = self.__fix_slice(i, j)
        for _ in range(j - i):
            self.pop(i)


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

    def __init__(self, _obj=None, wrapper=None, type_config=None):
        super(JsonDict, self).__init__()
        self._obj = check_type(_obj, dict, 'JsonDict must wrap a dict or None')
        assert type_config is not None
        self._type_config = type_config
        self._wrapper = (
            wrapper or
            DefaultProperty(type_config=self._type_config)
        )
        for key, value in self._obj.items():
            self[key] = self.__wrap(key, value)

    def validate(self, required=True):
        for obj in self.values():
            self._wrapper.validate(obj, required=required)

    def __wrap(self, key, unwrapped):
        return self._wrapper.wrap(unwrapped)

    def __unwrap(self, key, wrapped):
        return self._wrapper.unwrap(wrapped)

    def __setitem__(self, key, value):
        if isinstance(key, int):
            key = unicode(key)

        wrapped, unwrapped = self.__unwrap(key, value)
        self._obj[key] = unwrapped
        super(JsonDict, self).__setitem__(key, wrapped)

    def __delitem__(self, key):
        del self._obj[key]
        super(JsonDict, self).__delitem__(key)

    def __getitem__(self, key):
        if isinstance(key, int):
            key = unicode(key)
        return super(JsonDict, self).__getitem__(key)


class JsonSet(set):
    def __init__(self, _obj=None, wrapper=None, type_config=None):
        super(JsonSet, self).__init__()
        if isinstance(_obj, set):
            _obj = list(_obj)
        self._obj = check_type(_obj, list, 'JsonSet must wrap a list or None')
        assert type_config is not None
        self._type_config = type_config
        self._wrapper = (
            wrapper or
            DefaultProperty(type_config=self._type_config)
        )
        for item in self._obj:
            super(JsonSet, self).add(self._wrapper.wrap(item))

    def validate(self, required=True):
        for obj in self:
            self._wrapper.validate(obj, required=required)

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


JsonObjectClassSettings = namedtuple('JsonObjectClassSettings', ['type_config'])

CLASS_SETTINGS_ATTR = '_$_class_settings'


def get_settings(cls):
    return getattr(cls, CLASS_SETTINGS_ATTR,
                   JsonObjectClassSettings(type_config=TypeConfig()))


def set_settings(cls, settings):
    setattr(cls, CLASS_SETTINGS_ATTR, settings)


class TypeConfig(object):
    """
    This class allows the user to configure dynamic
    type handlers and string conversions for their JsonObject.

    properties is a map from python types to JsonProperty subclasses
    string_conversions is a list or tuple of (regex, python type)-tuples

    This class is used to store the configuration but is not part of the API.
    To configure:

        class Foo(JsonObject):
            # property definitions go here
            # ...

            class Meta(object):
                update_properties = {
                    datetime.datetime: MySpecialDateTimeProperty
                }

    If you now do

        foo = Foo()
        foo.timestamp = datetime.datetime(1988, 7, 7, 11, 8, 0)

    timestamp will be governed by a MySpecialDateTimeProperty
    instead of the default.

    """
    def __init__(self, properties=None, string_conversions=None):
        self._properties = properties if properties is not None else {}

        self._string_conversions = (
            OrderedDict(string_conversions) if string_conversions is not None
            else OrderedDict()
        )
        # cache this
        self.string_conversions = self._get_string_conversions()
        self.properties = self._properties

    def replace(self, properties=None, string_conversions=None):
        return TypeConfig(
            properties=(properties if properties is not None
                        else self._properties),
            string_conversions=(string_conversions if string_conversions is not None
                                else self._string_conversions)
        )

    def update(self, properties=None, string_conversions=None):
        _properties = self._properties.copy()
        _string_conversions = self.string_conversions[:]
        if properties:
            _properties.update(properties)
        if string_conversions:
            _string_conversions.extend(string_conversions)
        return TypeConfig(
            properties=_properties,
            string_conversions=_string_conversions,
        )

    def _get_string_conversions(self):
        result = []
        for pattern, conversion in self._string_conversions.items():
            conversion = (
                conversion if conversion not in self._properties
                else self._properties[conversion](type_config=self).to_python
            )
            result.append((pattern, conversion))
        return result

META_ATTRS = ('properties', 'string_conversions', 'update_properties')


class JsonObjectMeta(type):

    class Meta(object):
        pass

    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)

        cls.__configure(**{key: value
                           for key, value in cls.Meta.__dict__.items()
                           if key in META_ATTRS})
        cls_settings = get_settings(cls)

        properties = {}
        properties_by_name = {}
        for key, value in dct.items():
            if isinstance(value, JsonProperty):
                properties[key] = value
            elif key.startswith('_'):
                continue
            elif type(value) in cls_settings.type_config.properties:
                property_ = cls_settings.type_config.properties[type(value)](default=value)
                properties[key] = dct[key] = property_
                setattr(cls, key, property_)

        for key, property_ in properties.items():
            property_.init_property(default_name=key,
                                    type_config=cls_settings.type_config)
            assert property_.name is not None, property_
            assert property_.name not in properties_by_name, \
                'You can only have one property named {0}'.format(
                    property_.name)
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

    def __configure(cls, properties=None, string_conversions=None,
                    update_properties=None):
        super_settings = get_settings(super(cls, cls))
        assert len(filter(None, (properties, update_properties))) <= 1
        type_config = super_settings.type_config
        if update_properties is not None:
            type_config = type_config.update(properties=update_properties)
        elif properties is not None:
            type_config = type_config.replace(properties=properties)
        if string_conversions is not None:
            type_config = type_config.replace(
                string_conversions=string_conversions)
        set_settings(cls, super_settings._replace(type_config=type_config))
        return cls


class _JsonObjectPrivateInstanceVariables(object):

    def __init__(self, dynamic_properties=None):
        self.dynamic_properties = dynamic_properties or {}


class JsonObjectBase(object):

    __metaclass__ = JsonObjectMeta

    _allow_dynamic_properties = True
    _validate_required_lazily = False

    _properties_by_attr = None
    _properties_by_key = None

    _string_conversions = ()

    def __init__(self, _obj=None, **kwargs):
        setattr(self, '_$', _JsonObjectPrivateInstanceVariables())

        self._obj = check_type(_obj, dict,
                               'JsonObject must wrap a dict or None')
        self._wrapped = {}

        for key, value in self._obj.items():
            try:
                self.set_raw_value(key, value)
            except AttributeError:
                raise WrappingAttributeError(
                    "can't set attribute corresponding to {key!r} "
                    "on a {cls} while wrapping {data!r}".format(
                        cls=self.__class__,
                        key=key,
                        data=_obj,
                    )
                )

        for attr, value in kwargs.items():
            try:
                setattr(self, attr, value)
            except AttributeError:
                raise WrappingAttributeError(
                    "can't set attribute {attr!r} "
                    "on a {cls} while wrapping {data!r}".format(
                        cls=self.__class__,
                        key=attr,
                        data=_obj,
                    )
                )

        for key, value in self._properties_by_key.items():
            if key not in self._obj:
                try:
                    d = value.default()
                except TypeError:
                    d = value.default(self)
                self[key] = d

    def set_raw_value(self, key, value):
        wrapped = self.__wrap(key, value)
        if key in self._properties_by_key:
            self[key] = wrapped
        else:
            setattr(self, key, wrapped)

    @classmethod
    def properties(cls):
        return cls._properties_by_attr.copy()

    @property
    def __dynamic_properties(self):
        return getattr(self, '_$').dynamic_properties

    @classmethod
    def wrap(cls, obj):
        self = cls(obj)
        return self

    def validate(self, required=True):
        for key, value in self._wrapped.items():
            self.__get_property(key).validate(value, required=required)

    def to_json(self):
        self.validate()
        return copy.deepcopy(self._obj)

    def __get_property(self, key):
        try:
            return self._properties_by_key[key]
        except KeyError:
            return DefaultProperty(type_config=get_settings(self).type_config)

    def __wrap(self, key, value):
        property_ = self.__get_property(key)

        if value is None:
            return None

        if isinstance(property_, JsonArray):
            assert isinstance(property_, JsonContainerProperty)

        return property_.wrap(value)

    def __unwrap(self, key, value):
        property_ = self.__get_property(key)
        try:
            property_.validate(
                value,
                required=not self._validate_required_lazily,
                recursive=False,
            )
        except TypeError:
            property_.validate(
                value,
                required=not self._validate_required_lazily,
            )
        if value is None:
            return None, None

        return property_.unwrap(value)

    def __setitem__(self, key, value):
        wrapped, unwrapped = self.__unwrap(key, value)
        self._wrapped[key] = wrapped
        if self.__get_property(key).exclude(unwrapped):
            self._obj.pop(key, None)
        else:
            self._obj[key] = unwrapped
        if key not in self._properties_by_key:
            assert key not in self._properties_by_attr
            self.__dynamic_properties[key] = wrapped
            super(JsonObjectBase, self).__setattr__(key, wrapped)

    def __is_dynamic_property(self, name):
        return (
            name not in self._properties_by_attr and
            not name.startswith('_') and
            not inspect.isdatadescriptor(getattr(self.__class__, name, None))
        )

    def __setattr__(self, name, value):
        if self.__is_dynamic_property(name):
            if self._allow_dynamic_properties:
                self[name] = value
            else:
                raise AttributeError(
                    "{0!r} is not defined in schema "
                    "(not a valid property)".format(name)
                )
        else:
            super(JsonObjectBase, self).__setattr__(name, value)

    def __delitem__(self, key):
        if key in self._properties_by_key:
            raise DeleteNotAllowed(key)
        else:
            if not self.__is_dynamic_property(key):
                raise KeyError(key)
            del self._obj[key]
            del self._wrapped[key]
            del self.__dynamic_properties[key]
            super(JsonObjectBase, self).__delattr__(key)

    def __delattr__(self, name):
        if name in self._properties_by_attr:
            raise DeleteNotAllowed(name)
        elif self.__is_dynamic_property(name):
            del self[name]
        else:
            super(JsonObjectBase, self).__delattr__(name)

    def __repr__(self):
        name = self.__class__.__name__
        predefined_properties = self._properties_by_attr.keys()
        predefined_property_keys = set(self._properties_by_attr[p].name
                                       for p in predefined_properties)
        dynamic_properties = (set(self._wrapped.keys())
                              - predefined_property_keys)
        properties = sorted(predefined_properties) + sorted(dynamic_properties)
        return u'{name}({keyword_args})'.format(
            name=name,
            keyword_args=', '.join('{key}={value!r}'.format(
                key=key,
                value=getattr(self, key)
            ) for key in properties),
        )


class _LimitedDictInterfaceMixin(object):
    """
    mindlessly farms selected dict methods out to an internal dict

    really only a separate class from JsonObject
    to keep this mindlessness separate from the methods
    that need to be more carefully understood

    """
    _wrapped = None

    def keys(self):
        return self._wrapped.keys()

    def items(self):
        return self._wrapped.items()

    def iteritems(self):
        return self._wrapped.iteritems()

    def __contains__(self, item):
        return item in self._wrapped

    def __getitem__(self, item):
        return self._wrapped[item]

    def __iter__(self):
        return iter(self._wrapped)

    def __len__(self):
        return len(self._wrapped)


def get_dynamic_properties(obj):
    return getattr(obj, '_$').dynamic_properties.copy()
