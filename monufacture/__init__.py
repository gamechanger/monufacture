from factory import Factory, Trait
from contextlib import contextmanager
from threading import local
import logging

# Registry for all factories
factories = {}
traits = {}
debug = False
local = local()

# Methods to setup and declare factories
@contextmanager
def factory(name, collection=None):
    """Declares a new named factory with the given attributes."""
    factory = Factory(collection, global_traits=traits)
    factories[name] = factory

    # Set the context for other methods
    local.working_factory = factory
    yield
    del local.working_factory


def get_factory(name):
    """Get a factory by name"""
    return factories[name]


def _get_active_factory():
    if not hasattr(local, 'working_factory'):
        raise FactoryContextException("Method must be called inside a 'with factory()' context.")
    return local.working_factory


def default(attrs, traits=[]):
    _get_active_factory().default(attrs, traits)


def document(name, attrs=None, parent=None, traits=[]):
    _get_active_factory().document(name, attrs, parent, traits)


def trait(name, attrs, parent=None):
    if hasattr(local, 'working_factory'):
        _get_active_factory().trait(name, attrs, parent)
    else:
        traits[name] = Trait(attrs, parent)


def fragment(name, attrs=None, parent=None, traits=[]):
    _get_active_factory().fragment(name, attrs, parent, traits)


def embed(name):
    return _get_active_factory().embed(name)


# Methods to create document instances using factories
def create(factory_, document_=None, **overrides):
    """Creates and returns instance of the named document using the factory
    with which it was declared, utilising any provided attribute
    overrides, storing the instance in the database."""
    doc = factories[factory_].create(document_, **overrides)
    if debug:
        logging.debug("CREATED [%s]: %s, document=%s, overrides=%s", 
                      doc['_id'], factory_, document_, overrides)
    return doc


def build(factory_, document_=None, **overrides):
    """Builds and returns instance of the named document using the factory
    with which it was declared, utilising any provided attribute
    overrides, without storing the instance in the database."""
    return factories[factory_].build(document_, **overrides)


def build_list(count_, factory_, document_=None, **overrides):
    """Builds a list of `count_` instances of the named document using the 
    associated factory."""
    return [build(factory_, document_, **overrides) for x in range(count_)]


def create_list(count_, factory_, document_=None, **overrides):
    """Creates a list of `count_` instances of the named document using the 
    associated factory."""
    return [create(factory_, document_, **overrides) for x in range(count_)]


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
    traits.clear()


class FactoryContextException(Exception):
    pass
