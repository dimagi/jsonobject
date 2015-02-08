from jsonobject.properties import StringProperty


class TypeProperty(StringProperty):
    """
    A property that is always required and can only ever have a single value.
    """
    def __init__(self, type_name, name=None, validators=None,
                 verbose_name=None, type_config=None):
        super(TypeProperty, self).__init__(
            default=type_name, name=name, required=True,
            choices=[type_name], validators=validators,
            verbose_name=verbose_name, type_config=type_config)


class TypeFactory(object):
    """
    Use a TypeFactory instance to dynamically determine the type of
    an ObjectProperty during wrapping.
    """
    def __init__(self, identifier_field):
        self.identifier_field = identifier_field
        self.registered_types = {}
        self.default_type = None

    def register_type(self, is_default=False):
        def register_type_decorator(type_cls):
            try:
                id_field = getattr(type_cls, self.identifier_field)
            except AttributeError:
                raise TypeError("Missing identifier field '{}' for type '{}'".format(self.identifier_field, type_cls))

            type_id = id_field.default()
            if not type_id:
                raise TypeError("Identifier field for class '{}' must have a "
                                "default value: {}".format(type_cls, self.identifier_field))

            if type_id in self.registered_types:
                raise TypeError("Type '{}' already registered by '{}'".format(type_id, self.registered_types[type_id]))

            self.registered_types[type_id] = type_cls

            if is_default:
                if self.default_type:
                    raise TypeError(("Attempt to register multiple default types: "
                                     "{}, {}").format(self.default_type, type_cls))
                self.default_type = type_cls

            return type_cls

        return register_type_decorator

    def get_type_for_object(self, obj):
        if obj is None:
            return self.default_type
        if self.identifier_field not in obj:
            raise TypeError("Missing identifier field '{}' in object source: {}".format(self.identifier_field, obj))
        else:
            type_ = self.registered_types.get(obj[self.identifier_field])
            if not type_:
                raise TypeError("Unknown object type '{}': {}".format(obj[self.identifier_field], obj))
            return type_
