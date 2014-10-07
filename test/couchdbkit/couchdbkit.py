import functools
from jsonobject import *
import types
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring
SchemaProperty = ObjectProperty
SchemaListProperty = ListProperty
StringListProperty = functools.partial(ListProperty, unicode)
SchemaDictProperty = DictProperty


class DocumentSchema(JsonObject):

    @StringProperty
    def doc_type(self):
        return self.__class__.__name__


class Document(DocumentSchema):

    _id = StringProperty()
    _rev = StringProperty()
    _attachments = DictProperty()
