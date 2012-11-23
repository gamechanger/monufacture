from unittest import TestCase
from monufacture import factory, dependent, sequence, build, create
from mock import Mock
from bson.objectid import ObjectId

class TestModule(TestCase):

    def setUp(self):
        self.collection = Mock()
        factory("user", self.collection,
            first = "John",
            last = "Smith",
            email = dependent(lambda doc: "%s.%s@test.com" % (doc['first'], doc['last'])),
            age = sequence(lambda n: n + 20))

    def test_build(self):
        expected1 = {
            "first": "John",
            "last": "Smith",
            "email": "John.Smith@test.com",
            "age": 21
        }

        expected2 = {
            "first": "Mike",
            "last": "Smith",
            "email": "Mike.Smith@test.com",
            "age": 22
        }

        doc1 = build("user")
        doc2 = build("user", first="Mike")
        self.assertEquals(doc1, expected1)
        self.assertEquals(doc2, expected2)

    def test_create(self):
        to_return = {
            "_id": ObjectId,
            "first": "Mike",
            "last": "Smith",
            "email": "Mike.Smith@test.com",
            "age": 21
        }

        self.collection.insert = Mock(return_value=to_return["_id"])
        self.collection.find_one = Mock(return_value=to_return)

        created = create("user", first='Mike')

        self.collection.insert.assert_called_with({
            "first": "Mike",
            "last": "Smith",
            "email": "Mike.Smith@test.com",
            "age": 21
        })
        self.collection.find_one.assert_called_with(to_return["_id"])
        self.assertDictEqual(created, to_return)        
