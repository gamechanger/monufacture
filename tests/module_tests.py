from unittest import TestCase
from monufacture import factory, default, document, build, create, build_list, create_list, cleanup, reset, FactoryContextException
from monufacture.helpers import dependent, sequence, id_of
from mock import Mock
from bson.objectid import ObjectId
from copy import copy


class TestDeclaration(TestCase):
    """Tests for "declaration"-type methods which allow factories to
    be declared/registered for use later."""

    def tearDown(self):
        reset()

    def test_default_not_callable_outside_factory_context(self):
        with self.assertRaises(FactoryContextException):
            default({"a": "b"})

    def test_document_not_callable_outside_factory_context(self):
        with self.assertRaises(FactoryContextException):
            document("test", {"a": "b"})

class TestGeneration(TestCase):
    """Tests for "generation"-type methods - those which create new 
    document instances using registered factories."""
    def setUp(self):
        self.company_id = ObjectId()
        self.user_collection = Mock()
        self.company_collection = Mock()
        self.company_collection.insert = Mock(return_value=self.company_id)
        self.company_collection.find_one = Mock(return_value={'_id': self.company_id})

        with factory("user", self.user_collection):
            default({
                "first": "John",
                "last": "Smith",
                "prefs": {
                    "receives_sms": True,
                    "receives_email": False
                },
                "company_id": id_of("company"),
                "email": dependent(lambda doc: "%s.%s@test.com" % (doc['first'], doc['last'])),
                "age": sequence(lambda n: n + 20)
            })

            document("admin", {
                "first": "Bill",
                "last": "Jones",
                "prefs": {
                    "receives_sms": False,
                    "receives_email": True
                },
                "company_id": id_of("company"),
                "email": dependent(lambda doc: "%s.%s@test.com" % (doc['first'], doc['last'])),
                "age": sequence(lambda n: n + 20)
            })
        
        with factory("company", self.company_collection):
            default({
                "name": "GloboCorp"
            })


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

    def test_build_named_document(self):
        expected1 = {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21
        }

        expected2 = {
            "first": "Mike",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Mike.Jones@test.com",
            "age": 22
        }

        doc1 = build("user", "admin")
        doc2 = build("user", "admin", first="Mike")
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

    def test_create_named_document(self):
        to_return = {
            "_id": ObjectId,
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21
        }

        self.user_collection.insert = Mock(return_value=to_return["_id"])
        self.user_collection.find_one = Mock(return_value=to_return)

        created = create("user", "admin", first='Mike')

        self.user_collection.insert.assert_called_with({
            "first": "Mike",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Mike.Jones@test.com",
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

        docs = build_list(3, "user")

        self.assertEquals(expected_list, docs)

    def test_build_list_of_named_documents(self):
        expected_list = [{
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 22
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 23
        }]

        docs = build_list(3, "user", "admin")

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

        created_list = create_list(3, "user")

        self.assertEqual(created_list, docs)

    def test_create_list_of_named_documents(self):
        object_ids = [ObjectId() for x in range(3)]
        docs = [{
            "_id": object_ids[0],
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
        },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21
        }, {
            "_id": object_ids[1],
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 22
        }, {
            "_id": object_ids[2],
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 23
        }]
        return_docs = copy(docs)

        def object_id_returns(*args):
            return object_ids.pop(0)

        def doc_returns(*args):
            return return_docs.pop(0)

        self.user_collection.insert = Mock(side_effect=object_id_returns)
        self.user_collection.find_one = Mock(side_effect=doc_returns)

        created_list = create_list(3, "user", "admin")

        self.assertEqual(created_list, docs)

    def test_cleanup(self):
        object_id = ObjectId()
        self.user_collection.insert = Mock(return_value=object_id)

        create("user")
        cleanup()

        self.user_collection.remove.assert_called_with(object_id)
        self.company_collection.remove.assert_called_with(self.company_id)
