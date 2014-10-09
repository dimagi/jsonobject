from __future__ import absolute_import
from .base import JsonObjectBase, _LimitedDictInterfaceMixin

import decimal
import datetime
from six import integer_types, text_type, string_types
from . import properties
import re

re_date = re.compile(r'^(\d{4})\D?(0[1-9]|1[0-2])\D?([12]\d|0[1-9]|3[01])$')
re_time = re.compile(
    r'^([01]\d|2[0-3])\D?([0-5]\d)\D?([0-5]\d)?\D?(\d{3,6})?$')
re_datetime = re.compile(
    r'^(\d{4})\D?(0[1-9]|1[0-2])\D?([12]\d|0[1-9]|3[01])'
    r'(\D?([01]\d|2[0-3])\D?([0-5]\d)\D?([0-5]\d)?\D?(\d{3,6})?'
    r'([zZ]|([\+-])([01]\d|2[0-3])\D?([0-5]\d)?)?)?$'
)
re_decimal = re.compile('^(\d+)\.(\d+)$')


class JsonObject(JsonObjectBase, _LimitedDictInterfaceMixin):
    def __getstate__(self):
        return self.to_json()

    def __setstate__(self, dct):
        self.__init__(dct)

    class Meta(object):
        properties = {
            decimal.Decimal: properties.DecimalProperty,
            datetime.datetime: properties.DateTimeProperty,
            datetime.date: properties.DateProperty,
            datetime.time: properties.TimeProperty,
            str: properties.StringProperty,
            text_type: properties.StringProperty,
            bool: properties.BooleanProperty,
            int: properties.IntegerProperty,
            integer_types: properties.IntegerProperty,
            float: properties.FloatProperty,
            list: properties.ListProperty,
            dict: properties.DictProperty,
            set: properties.SetProperty,
        }
        string_conversions = (
            (re_date, datetime.date),
            (re_time, datetime.time),
            (re_datetime, datetime.datetime),
            (re_decimal, decimal.Decimal),
        )
