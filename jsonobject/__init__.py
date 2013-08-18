from base import JsonObject, JsonArray
from .properties import *
import convert

__all__ = [
    'IntegerProperty', 'FloatProperty', 'DecimalProperty',
    'StringProperty', 'BooleanProperty',
    'DateProperty', 'DateTimeProperty', 'TimeProperty',
    'ObjectProperty', 'ListProperty', 'DictProperty',
    'JsonObject', 'JsonArray',
]

JsonObjectMeta._convert = convert
