from factory import Factory
from dynamic import dependent, sequence

# Registry for all factories
factories = {}


def factory(name, collection=None, **attrs):
    """Declares a new named factory with the given attributes."""
    factory = Factory(collection, **attrs)
    factories[name] = factory


def create(name, **overrides):
    """Creates and returns instance of the named document using the factory
    with which it was declared, utilising any provided attribute
    overrides, storing the instance in the database."""
    return factories[name].create(**overrides)


def build(name, **overrides):
    """Builds and returns instance of the named document using the factory
    with which it was declared, utilising any provided attribute
    overrides, without storing the instance in the database."""
    return factories[name].build(**overrides)


def build_list(name, count):
    """Builds a list of `count` instances of the named document using the 
    associated factory."""
    return [build(name) for x in range(count)]


def create_list(name, count):
    """Creates a list of `count` instances of the named document using the 
    associated factory."""
    return [create(name) for x in range(count)]
