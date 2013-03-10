from factory import Factory

# Registry for all factories
factories = {}


def factory(factory_document_name, attrs, collection=None):
    """Declares a new named factory with the given attributes."""
    factory = Factory(attrs, collection)
    factories[factory_document_name] = factory


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


def cleanup():
    """Cleans up all factory data generated since the process was started, 
    or since the last time this method was called."""
    for factory in factories.itervalues():
        factory.cleanup()

def reset():
    """Resets Monufacturer, removing all registered factories. Only really 
    here for testing purposes."""
    factories.clear()
