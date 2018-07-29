from __future__ import absolute_import
from __future__ import unicode_literals
import six
__all__ = ['StringProperty', 'IntegerProperty', 'ObjectProperty', 'JsonObject', 'ListProperty']

from couchdbkit import (
    StringProperty,
    IntegerProperty,
    SchemaProperty as ObjectProperty,
    DocumentSchema as JsonObject,
)


def ListProperty(obj_type):
    if issubclass(obj_type, JsonObject):
        from couchdbkit import SchemaListProperty
        return SchemaListProperty
    elif obj_type is int:
        from couchdbkit import ListProperty
        return ListProperty
    elif issubclass(obj_type, six.string_types):
        from couchdbkit import StringListProperty
        return StringListProperty
    else:
        raise TypeError(obj_type)
