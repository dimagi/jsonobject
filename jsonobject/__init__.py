from base import JsonObject, JsonArray
from .properties import *
import properties
__all__ = [
    'IntegerProperty', 'FloatProperty', 'StringProperty', 'BooleanProperty',
    'DateProperty', 'DateTimeProperty',
    'ObjectProperty', 'ListProperty',
    'JsonObject', 'JsonArray',
]

JsonObjectMeta.properties_module = properties
