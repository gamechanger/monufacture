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

def default(attrs):
    if not hasattr(local, 'working_factory'):
        raise FactoryContextException("default() must be called inside a 'with factory()' context.")

    factory = local.working_factory
    factory.default(attrs)

def document(name, attrs):
    if not hasattr(local, 'working_factory'):
        raise FactoryContextException("default() must be called inside a 'with factory()' context.")

    factory = local.working_factory
    factory.document(name, attrs)


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


def build_list(number, factory, document=None):
    """Builds a list of `count` instances of the named document using the 
    associated factory."""
    return [build(factory, document) for x in range(number)]


def create_list(count, factory, document=None):
    """Creates a list of `count` instances of the named document using the 
    associated factory."""
    return [create(factory) for x in range(count)]


# Cleanup methods
def cleanup():
    """Cleans up all factory data generated since the process was started, 
    or since the last time this method was called."""
    for factory in factories.itervalues():
        factory.cleanup()

def reset():
    """Resets Monufacturer, removing all registered factories. Only really 
    here for testing purposes."""
    factories.clear()


class FactoryContextException(Exception):
    pass
