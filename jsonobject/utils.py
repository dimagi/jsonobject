from __future__ import absolute_import
from .exceptions import BadValueError



def check_type(obj, item_type, message):
    if obj is None:
        return item_type()
    elif not isinstance(obj, item_type):
        raise BadValueError(message)
    else:
        return obj


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
        for key in list(self.keys()):
            del self[key]
