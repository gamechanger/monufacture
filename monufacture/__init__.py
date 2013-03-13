from factory import Factory
from contextlib import contextmanager
from threading import local

# Registry for all factories
factories = {}

local = local()

# Methods to setup and declare factories
@contextmanager
def factory(name, collection):
    """Declares a new named factory with the given attributes."""
    factory = Factory(collection)
    factories[name] = factory

    # Set the context for other methods
    local.working_factory = factory
    yield
    del local.working_factory


def _get_factory():
    if not hasattr(local, 'working_factory'):
        raise FactoryContextException("Method must be called inside a 'with factory()' context.")
    return local.working_factory


def default(attrs, traits=[]):
    _get_factory().default(attrs, traits)


def document(name, attrs, parent=None, traits=[]):
    _get_factory().document(name, attrs, parent, traits)


def trait(name, attrs, parent=None):
    _get_factory().trait(name, attrs, parent)


def fragment(name, attrs, parent=None, traits=[]):
    _get_factory().fragment(name, attrs, parent, traits)


def embed(name):
    return _get_factory().embed(name)


# Methods to create document instances using factories
def create(factory, document=None, **overrides):
    """Creates and returns instance of the named document using the factory
    with which it was declared, utilising any provided attribute
    overrides, storing the instance in the database."""
    return factories[factory].create(document, **overrides)


def build(factory, document=None, **overrides):
    """Builds and returns instance of the named document using the factory
    with which it was declared, utilising any provided attribute
    overrides, without storing the instance in the database."""
    return factories[factory].build(document, **overrides)


def build_list(number, factory, document=None, **overrides):
    """Builds a list of `count` instances of the named document using the 
    associated factory."""
    return [build(factory, document, **overrides) for x in range(number)]


def create_list(count, factory, document=None, **overrides):
    """Creates a list of `count` instances of the named document using the 
    associated factory."""
    return [create(factory, document, **overrides) for x in range(count)]


# Cleanup methods
def cleanup():
    """Cleans up all factory data generated since the process was started, 
    or since the last time this method was called."""
    for factory in factories.itervalues():
        factory.cleanup()

def reset():
    """Resets Monufacturer, removing all registered factories. Only really 
    here for testing purposes."""
    cleanup()
    factories.clear()


class FactoryContextException(Exception):
    pass
