from factory import Factory
from dynamic import dependent, sequence

# Registry for all factories
factories = {}


def factory(name, collection=None, **attrs):
    factory = Factory(collection, **attrs)
    factories[name] = factory


def create(name, **overrides):
    return factories[name].create(**overrides)


def build(name, **overrides):
    return factories[name].build(**overrides)
