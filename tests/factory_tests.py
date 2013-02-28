import unittest
from monufacture.factory import Factory
from mock import Mock, call
from bson.objectid import ObjectId
from copy import copy


class TestFactory(unittest.TestCase):

    def setUp(self):
        self.collection = Mock()

    def test_build_simple(self):
        factory = Factory(self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        self.assertDictEqual(factory.build(), {
            "first_name": "John",
            "last_name": "Smith",
            "age": 32
        })

    def test_build_with_function_attrs(self):
        def full_name(doc):
            return "%s %s" % (doc['first_name'], doc['last_name'])

        factory = Factory(self.collection,
            first_name = 'John',
            last_name = 'Smith',
            full_name = full_name,
            age = 32)

        self.assertDictEqual(factory.build(), {
            "first_name": "John",
            "last_name": "Smith",
            "full_name": "John Smith",
            "age": 32
        })

    def test_build_with_overrides(self):
        factory = Factory(self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        self.assertDictEqual(factory.build(first_name='Mike', age=45), {
            "first_name": "Mike",
            "last_name": "Smith",
            "age": 45
        })

    def test_build_with_function_and_overrides(self):
        def full_name(doc):
            return "%s %s" % (doc['first_name'], doc['last_name'])

        factory = Factory(self.collection,
            first_name = 'John',
            last_name = 'Smith',
            full_name = full_name,
            age = 32)

        self.assertDictEqual(factory.build(first_name='Mike', age=45), {
            "first_name": "Mike",
            "last_name": "Smith",
            "full_name": "Mike Smith",
            "age": 45
        })

    def test_create_simple(self):
        to_return = {
            "_id": ObjectId(),
            "first_name": "John",
            "last_name": "Smith",
            "age": 32
        }

        self.collection.insert = Mock(return_value=to_return["_id"])
        self.collection.find_one = Mock(return_value=to_return)

        factory = Factory(self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        created = factory.create()

        self.collection.insert.assert_called_with({
            "first_name": "John",
            "last_name": "Smith",
            "age": 32
        })
        self.collection.find_one.assert_called_with(to_return["_id"])
        self.assertDictEqual(created, to_return)

    def test_create_with_overrides(self):
        to_return = {
            "_id": ObjectId(),
            "first_name": "Mike",
            "last_name": "Smith",
            "age": 32
        }

        self.collection.insert = Mock(return_value=to_return["_id"])
        self.collection.find_one = Mock(return_value=to_return)

        factory = Factory(self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        created = factory.create(first_name='Mike')

        self.collection.insert.assert_called_with({
            "first_name": "Mike",
            "last_name": "Smith",
            "age": 32
        })
        self.collection.find_one.assert_called_with(to_return["_id"])
        self.assertDictEqual(created, to_return)

    def test_create_with_additional_fields(self):
        to_return = {
            "_id": ObjectId(),
            "first_name": "John",
            "last_name": "Smith",
            "age": 32,
            "gender": "male"
        }

        self.collection.insert = Mock(return_value=to_return["_id"])
        self.collection.find_one = Mock(return_value=to_return)

        factory = Factory(self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        created = factory.create(gender='male')

        self.collection.insert.assert_called_with({
            "first_name": "John",
            "last_name": "Smith",
            "age": 32,
            "gender": "male"
        })
        self.collection.find_one.assert_called_with(to_return["_id"])
        self.assertDictEqual(created, to_return)

    def test_create_disabled_when_no_collection_provided(self):
        factory = Factory(
            first_name='John',
            last_name='Smith',
            age=32)

        with self.assertRaises(IOError):
            factory.create()

    def test_cleanup_nothing_to_do(self):
        factory = Factory(self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        factory.cleanup()

        expected_calls = []
        self.assertEqual(self.collection.remove.mock_calls, expected_calls)

    def test_cleanup(self):
        ids = [ObjectId() for x in range(3)]
        cleanup_ids = copy(ids)
        cleanup_ids.reverse()

        def insert_results(*args):
            return ids.pop(0)

        self.collection.insert = Mock(side_effect=insert_results)

        factory = Factory(self.collection,
            first_name='John',
            last_name='Smith',
            age=32)

        for x in range(3):
            factory.create()

        factory.cleanup()

        expected_calls = [call(oid) for oid in cleanup_ids]
        self.assertEqual(self.collection.remove.mock_calls, expected_calls)

        self.collection.reset_mock()

        factory.cleanup()

        self.assertFalse(self.collection.remove.called)
