from unittest import TestCase
from monufacture import factory, build, create, build_list, create_list, cleanup, reset
from monufacture.helpers import dependent, sequence, subdoc, id_of
from mock import Mock
from bson.objectid import ObjectId
from copy import copy

class TestModule(TestCase):

    def setUp(self):
        self.company_id = ObjectId()
        self.user_collection = Mock()
        self.company_collection = Mock()
        self.company_collection.insert = Mock(return_value=self.company_id)
        self.company_collection.find_one = Mock(return_value={'_id': self.company_id})

        factory("prefs", {
            "receives_sms": True,
            "receives_email": False
        })

        factory("company", {
            "name": "GloboCorp"
        }, self.company_collection)

        factory("user", {
            "first": "John",
            "last": "Smith",
            "prefs": subdoc("prefs"),
            "company_id": id_of("company"),
            "email": dependent(lambda doc: "%s.%s@test.com" % (doc['first'], doc['last'])),
            "age": sequence(lambda n: n + 20)
        }, self.user_collection)

    def tearDown(self):
        reset()

    def test_build(self):
        expected1 = {
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 21
        }

        expected2 = {
            "first": "Mike",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
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
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "Mike.Smith@test.com",
            "age": 21
        }

        self.user_collection.insert = Mock(return_value=to_return["_id"])
        self.user_collection.find_one = Mock(return_value=to_return)

        created = create("user", first='Mike')

        self.user_collection.insert.assert_called_with({
            "first": "Mike",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "Mike.Smith@test.com",
            "age": 21
        })
        self.user_collection.find_one.assert_called_with(to_return["_id"])
        self.assertDictEqual(created, to_return)        

    def test_build_list(self):
        expected_list = [{
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 21
        }, {
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 22
        }, {
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 23
        }]

        docs = build_list("user", 3)

        self.assertEquals(expected_list, docs)

    def test_create_list(self):
        object_ids = [ObjectId() for x in range(3)]
        docs = [{
            "_id": object_ids[0],
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
        },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 21
        }, {
            "_id": object_ids[1],
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 22
        }, {
            "_id": object_ids[2],
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 23
        }]
        return_docs = copy(docs)

        def object_id_returns(*args):
            return object_ids.pop(0)

        def doc_returns(*args):
            return return_docs.pop(0)

        self.user_collection.insert = Mock(side_effect=object_id_returns)
        self.user_collection.find_one = Mock(side_effect=doc_returns)

        created_list = create_list("user", 3)

        self.assertEqual(created_list, docs)

    def test_cleanup(self):
        object_id = ObjectId()
        self.user_collection.insert = Mock(return_value=object_id)

        create("user")
        cleanup()

        self.user_collection.remove.assert_called_with(object_id)
        self.company_collection.remove.assert_called_with(self.company_id)
