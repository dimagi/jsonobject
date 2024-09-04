from __future__ import absolute_import
from __future__ import unicode_literals
import random
import six
from six.moves import range

from . import jsonobject as jo


def generate_object_type():
    WORDS = 'dog cat elephant river candle stripe pin plum'.split()
    leaf_types = {
        jo.StringProperty: six.text_type,
        jo.IntegerProperty: int,
    }
    used_phrases = set()

    def get_phrase(n=2):
        phrase = tuple(random.sample(WORDS, n))
        if phrase in used_phrases or len(set(phrase)) < n:
            phrase = get_phrase()
        else:
            used_phrases.add(phrase)
        return phrase

    def generate_class_name(words=None):
        words = words or get_phrase()
        return ''.join([s.title() for s in words])

    def generate_property_name(words=None):
        words = words or get_phrase()
        return '_'.join(words)

    def generate_list_name(words=None):
        words = words or get_phrase()
        return generate_property_name(words) + 's'

    object_types = []

    def generate_object_type(words=None):
        class_name = generate_class_name(words)
        n_properties = random.choice(list(range(5)))
        dct = {}
        for _ in range(n_properties):
            words = get_phrase()

            property_type = random.choice([
                jo.ObjectProperty,
                jo.ListProperty,
                Ellipsis
            ])
            if property_type is jo.ObjectProperty:
                property_name = generate_property_name(words)
                dct[property_name] = jo.ObjectProperty(generate_object_type(words))
            elif property_type is jo.ListProperty:
                property_name = generate_list_name(words)
                dct[property_name] = jo.ListProperty(generate_list_type(words))

        object_type = type(jo.JsonObject)(class_name, (jo.JsonObject,), dct)
        object_types.append(object_type)
        return object_type

    def generate_list_type(words=None):
        property_type = random.choice([jo.ObjectProperty, Ellipsis])
        if property_type is jo.ObjectProperty:
            return generate_object_type(words)
        else:
            return random.choice(list(leaf_types.values()))

    return generate_object_type(), object_types
