import monufacture
import string
import random
from pytz import timezone
from datetime import datetime, timedelta
from bson.objectid import ObjectId

"""Contains setter functions designed to be used inline with
factory definitions to inject dynamic values into models as
and when they are built."""


class Sequence(object):
    def __init__(self):
        self.seq_num = 0

    def next(self):
        self.seq_num = self.seq_num + 1
        return self.seq_num


def sequence(fn=None):
    """Defines a sequential value for a factory attribute. On each successive
    invocation of this helper (i.e. when a new instance of a document is
    created by the enclosing factory) the given function is passed a
    sequentially incrementing number which should be used to return a dynamic
    value to be used on the model instance."""
    sequence = Sequence()

    if not fn:
        fn = lambda n: n

    def build(*args):
        return fn(sequence.next())
    return build


def dependent(fn):
    """Declares a value for a factory attribute which depends on other values
    in the document in order to be set. The given function or lambda is
    passed the document and should return the value to set."""
    def build(obj):
        return fn(obj)

    return build


def id_of(factory_, document_=None, **overrides):
    """Creates an instance using the given named factory and returns the
    ID of the persisted record. """
    def build(*args):
        # Flatten an function overrides
        instance_overrides = {}
        for key, value in overrides.iteritems():
            if callable(value):
                instance_overrides[key] = value(*args)
            else:
                instance_overrides[key] = value

        return monufacture.create(factory_, document_, **instance_overrides)["_id"]
    return build


def text(*args, **kwargs):
    """Aliases to random_text."""
    return random_text(*args, **kwargs)


def random_text(length=10, spaces=False, digits=False, upper=True,
                lower=True, other_chars=[]):
    """Inserts some random text of the given length into the document."""

    # Build the char set we'll use
    char_set = []
    if upper:
        char_set += list(string.uppercase)
    if lower:
        char_set += list(string.lowercase)
    if spaces:
        char_set.append(" ")
    if digits:
        char_set += list(string.digits)
    char_set += other_chars

    def build(*args):
        return "".join([random.choice(char_set) for i in xrange(length)])
    return build


def dbref_to(factory, document=None, **overrides):
    """Create a DBRef-type subdoc structure linking to a new instance of the
    given named factory type."""

    def build(*args):
        return {
            "$id": monufacture.create(factory, document, **overrides)["_id"],
            "$ref": monufacture.get_factory(factory).collection.name
        }
    return build


def date(year=None, month=None, day=None, hour=None, minute=None, second=None, microsecond=None, tz=None):
    """Returns a function to generate the current datetime for insertion into a document.
    Components of the date/time can be provided as overrides."""

    if year or month or day or hour or minute or second or microsecond:
        if not (year and month and day):
            raise ValueError("Either all components of a date must be provided or none of them.")

        def compact_args(**kwargs):
            out = {}
            out.update((k, v) for k, v in kwargs.iteritems() if v is not None)
            return out

        dt_args = compact_args(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond)

        def build_specific(*args):
            dt = datetime(**dt_args)
            if tz:
                dt = timezone(tz).localize(dt)
            return dt

        return build_specific

    def build_now(*args):
        return datetime.utcnow()
    return build_now


def now():
    """Forwards to date(), allowing the current datetime to be inserted."""
    return date()

def _convert_years_months_to_days(timedeltas):
    """Converts any 'years' or 'months' values in a given timedeltas dict
    to equivalent values of days and adds them to the 'days' value.
    This is to work around a lack of support for months and years in
    Python's timedelta library.
    Assumes 30 days per month, 365 days per year.
    """
    if 'months' in timedeltas:
        timedeltas['days'] = timedeltas.setdefault('days', 0) + 30 * timedeltas['months']
        del timedeltas['months']
    if 'years' in timedeltas:
        timedeltas['days'] = timedeltas.setdefault('days', 0) + 365 * timedeltas['years']
        del timedeltas['years']

def ago(**kwargs):
    """Returns a function to generate a datetime a time delta in the past from the
    time at which it is run."""
    def build(*args):
        _convert_years_months_to_days(kwargs)
        return datetime.utcnow() - timedelta(**kwargs)

    return build


def from_now(**kwargs):
    """Returns a function to generate a datetime a time delta in the future from the
    time at which it is run."""
    def build(*args):
        _convert_years_months_to_days(kwargs)
        return datetime.utcnow() + timedelta(**kwargs)

    return build


def list_of(fn, length):
    """Returns a function to generate a list of the given length,
    consisting of results of the given function"""
    def build(*args):
        return [fn(*args) for i in range(length)]
    return build


def object_id():
    """Returns a builder function which will insert a new ObjectId
    when the object is built."""
    def build(*args):
        return ObjectId()
    return build


def union(*fns):
    """Allows the list output of other helper functions to be unioned
    together in order to be set as a single attribute value. E.g.
    Unioning the output of n list_of helper calls."""
    def build(*args):
        out = []
        for fn in fns:
            out += fn(*args)
        return out
    return build


def one_of(*values):
    """Provides a function which returns one of the given values at
    random. Useful for getting a range of different but valid
    field values on a list of document instances."""
    def build(*args):
        return random.choice(values)
    return build


def random_number(a, b=None):
    """Inserts a random number in the given range into the document."""
    def build(*args):
        return random.randrange(a, b)
    return build


def number(*args, **kwargs):
    """Alias to random_number."""
    return random_number(*args, **kwargs)
