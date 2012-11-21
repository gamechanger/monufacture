import unittest
from monufacture.factory import Factory
from mock import Mock


class TestFactory(unittest.TestCase):

    def setUp(self):
        self.database = Mock()
        self.collection = Mock()

    def test_build_simple_factory(self):
        factory = Factory(self.database, self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        self.assertDictEqual(factory.build(), {
            "first_name": "John",
            "last_name": "Smith",
            "age": 32
        })

    def test_build_factory_with_function_attrs(self):
        def age_function():
            return 32

        factory = Factory(self.database, self.collection,
            first_name='John',
            last_name='Smith',
            age=age_function)

        self.assertDictEqual(factory.build(), {
            "first_name": "John",
            "last_name": "Smith",
            "age": 32
        })
