import functools
from jsonobject import *
from six import text_type
SchemaProperty = ObjectProperty
SchemaListProperty = ListProperty
StringListProperty = functools.partial(ListProperty, text_type)
SchemaDictProperty = DictProperty


class DocumentSchema(JsonObject):

    @StringProperty
    def doc_type(self):
        return self.__class__.__name__


class Document(DocumentSchema):

    _id = StringProperty()
    _rev = StringProperty()
    _attachments = DictProperty()
