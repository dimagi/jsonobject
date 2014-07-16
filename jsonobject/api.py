from .base import JsonObjectBase, _LimitedDictInterfaceMixin
from .convert import STRING_CONVERSIONS


class JsonObject(JsonObjectBase, _LimitedDictInterfaceMixin):

    _string_conversions = STRING_CONVERSIONS

    def __getstate__(self):
        return self.to_json()

    def __setstate__(self, dct):
        self.__init__(dct)
