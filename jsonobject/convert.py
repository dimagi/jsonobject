"""
This file was excerpted directly from couchdbkit.schema.properties
and edited to fit the needs of jsonobject

"""
ALLOWED_PROPERTY_TYPES = set([
    basestring,
    str,
    unicode,
    bool,
    int,
    long,
    float,
    datetime.datetime,
    datetime.date,
    datetime.time,
    decimal.Decimal,
    dict,
    list,
    set,
    type(None)
])

MAP_TYPES_PROPERTIES = {
        decimal.Decimal: DecimalProperty,
        datetime.datetime: DateTimeProperty,
        datetime.date: DateProperty,
        datetime.time: TimeProperty,
        str: StringProperty,
        unicode: StringProperty,
        bool: BooleanProperty,
        int: IntegerProperty,
        long: LongProperty,
        float: FloatProperty,
        list: ListProperty,
        dict: DictProperty,
        set: SetProperty,
}

def convert_property(value):
    """ convert a value to json from Property._to_json """
    if type(value) in MAP_TYPES_PROPERTIES:
        prop = MAP_TYPES_PROPERTIES[type(value)]()
        value = prop.to_json(value)
    return value


def value_to_property(value):
    """ Convert value in a Property object """
    if type(value) in MAP_TYPES_PROPERTIES:
        prop = MAP_TYPES_PROPERTIES[type(value)]()
        return prop
    else:
        return value

# utilities functions

def validate_list_content(value, item_type=None):
    """ validate type of values in a list """
    return [validate_content(item, item_type=item_type) for item in value]

def validate_dict_content(value, item_type=None):
    """ validate type of values in a dict """
    return dict([(k, validate_content(v,
                item_type=item_type)) for k, v in value.iteritems()])

def validate_set_content(value, item_type=None):
    """ validate type of values in a set """
    return set(validate_content(item, item_type=item_type) for item in value)

def validate_content(value, item_type=None):
    """ validate a value. test if value is in supported types """
    if isinstance(value, list):
        value = validate_list_content(value, item_type=item_type)
    elif isinstance(value, dict):
        value = validate_dict_content(value, item_type=item_type)
    elif item_type is not None and not isinstance(value, item_type):
        raise BadValueError(
            'Items  must all be in %s' % item_type)
    elif type(value) not in ALLOWED_PROPERTY_TYPES:
            raise BadValueError(
                'Items  must all be in %s' %
                    (ALLOWED_PROPERTY_TYPES))
    return value

def dict_to_json(value, item_type=None):
    """ convert a dict to json """
    return dict([(k, value_to_json(v, item_type=item_type)) for k, v in value.iteritems()])

def list_to_json(value, item_type=None):
    """ convert a list to json """
    return [value_to_json(item, item_type=item_type) for item in value]

def value_to_json(value, item_type=None):
    """ convert a value to json using appropriate regexp.
    For Dates we use ISO 8601. Decimal are converted to string.

    """
    if isinstance(value, datetime.datetime) and is_type_ok(item_type, datetime.datetime):
        value = value.replace(microsecond=0).isoformat() + 'Z'
    elif isinstance(value, datetime.date) and is_type_ok(item_type, datetime.date):
        value = value.isoformat()
    elif isinstance(value, datetime.time) and is_type_ok(item_type, datetime.time):
        value = value.replace(microsecond=0).isoformat()
    elif isinstance(value, decimal.Decimal) and is_type_ok(item_type, decimal.Decimal):
        value = unicode(value)
    elif isinstance(value, (list, MutableSet)):
        value = list_to_json(value, item_type)
    elif isinstance(value, dict):
        value = dict_to_json(value, item_type)
    return value

def is_type_ok(item_type, value_type):
    return item_type is None or item_type == value_type


def value_to_python(value, item_type=None):
    """ convert a json value to python type using regexp. values converted
    have been put in json via `value_to_json` .
    """
    data_type = None
    if isinstance(value, basestring):
        if re_date.match(value) and is_type_ok(item_type, datetime.date):
            data_type = datetime.date
        elif re_time.match(value) and is_type_ok(item_type, datetime.time):
            data_type = datetime.time
        elif re_datetime.match(value) and is_type_ok(item_type, datetime.datetime):
            data_type = datetime.datetime
        elif re_decimal.match(value) and is_type_ok(item_type, decimal.Decimal):
            data_type = decimal.Decimal
        if data_type is not None:
            prop = MAP_TYPES_PROPERTIES[data_type]()
            try:
                #sometimes regex fail so return value
                value = prop.to_python(value)
            except:
                pass
    elif isinstance(value, (list, MutableSet)):
        value = list_to_python(value, item_type=item_type)
    elif isinstance(value, dict):
        value = dict_to_python(value, item_type=item_type)
    return value

def list_to_python(value, item_type=None):
    """ convert a list of json values to python list """
    return [value_to_python(item, item_type=item_type) for item in value]

def dict_to_python(value, item_type=None):
    """ convert a json object values to python dict """
    return dict([(k, value_to_python(v, item_type=item_type)) for k, v in value.iteritems()])
