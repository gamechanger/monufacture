import monufacture
import string
import random
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


def sequence(fn):
    """Defines a sequential value for a factory attribute. On each successive
    invocation of this helper (i.e. when a new instance of a document is
    created by the enclosing factory) the given function is passed a
    sequentially incrementing number which should be used to return a dynamic
    value to be used on the model instance."""
    sequence = Sequence()

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


def subdoc(name):
    """Inserts the document fragment built by the given named factory at a
    given container attribute."""
    def build(*args):
        return monufacture.build(name)
    return build


def id_of(name):
    """Creates an instance using the given named factory and returns the
    ID of the persisted record."""
    def build(*args):
        return monufacture.create(name)["_id"]
    return build


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


def dbref_to(name, type=None):
    """Create a DBRef-type subdoc structure linking to a new instance of the
    given named factory type."""
    if not type:
        type = name

    def build(*args):
        return {
            "$id": monufacture.create(name)["_id"],
            "$ref": type
        }
    return build


def date(year=None, month=None, day=None, hour=None, minute=None, second=None, microsecond=None):
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
            return datetime(**dt_args)

        return build_specific

    def build_now(*args):
        return datetime.now()
    return build_now


def ago(**kwargs):
    """Returns a function to generate a datetime a time delta in the past from the 
    time at which it is run."""
    def build(*args):
        return datetime.now() - timedelta(**kwargs)

    return build


def from_now(**kwargs):
    """Returns a function to generate a datetime a time delta in the future from the
    time at which it is run."""
    def build(*args):
        return datetime.now() + timedelta(**kwargs)

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
