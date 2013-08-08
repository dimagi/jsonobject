from base import JsonObject, JsonArray
from .properties import *
import properties
__all__ = [
    'IntegerProperty', 'FloatProperty', 'StringProperty', 'BooleanProperty',
    'DateProperty', 'DateTimeProperty',
    'ObjectProperty', 'ListProperty', 'DictProperty',
    'JsonObject', 'JsonArray',
]

JsonObjectMeta.properties_module = properties
