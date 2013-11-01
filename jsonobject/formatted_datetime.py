import datetime


class FormattedDateTime(datetime.datetime):
    def __new__(cls, *args, **kwargs):
        string_repr = kwargs.pop('string_repr')
        self = super(FormattedDateTime, cls).__new__(cls, *args, **kwargs)
        self.string_repr = string_repr
        return self


class FormattedTime(datetime.time):
    def __new__(cls, *args, **kwargs):
        string_repr = kwargs.pop('string_repr')
        self = super(FormattedTime, cls).__new__(cls, *args, **kwargs)
        self.string_repr = string_repr
        return self
