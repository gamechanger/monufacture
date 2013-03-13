import os
from unittest import TestCase
from monufacture import factory, trait, default, document, fragment, embed, build, create, build_list, create_list, cleanup, reset, FactoryContextException
from monufacture.helpers import dependent, sequence, id_of
from mock import Mock
from bson.objectid import ObjectId
from pymongo.connection import Connection

host = os.environ.get("DB_IP", "localhost")
port = int(os.environ.get("DB_PORT", 27017))
conn = Connection(host, port).monufacture_test

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
        self.user_collection = conn.user
        self.company_collection = Mock()
        self.company_collection.insert = Mock(return_value=self.company_id)
        self.company_collection.find_one = Mock(return_value={'_id': self.company_id})

        with factory("user", self.user_collection):
            fragment("prefs_email", {
                "receives_sms": True,
                "receives_email": False
            }, traits=['versioned'])

            fragment("prefs_sms", {
                "receives_sms": False,
                "receives_email": True                
            }, traits=['versioned'])

            default({
                "first": "John",
                "last": "Smith",
                "prefs": embed("prefs_email")
            }, traits=["common"])

            document("admin", {
                "first": "Bill",
                "last": "Jones",
                "prefs": embed("prefs_sms"),
            }, parent="default", traits=["versioned"])

            trait("timestamped", {
                "created": "now"
            })

            trait("common", {
                "company_id": id_of("company"),
                "email": dependent(lambda doc: "%s.%s@test.com" % (doc['first'], doc['last'])),
                "age": sequence(lambda n: n + 20)
            }, parent="timestamped")

            trait("versioned", {
                "v": 4
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
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 21,
            "created": "now"
        }

        expected2 = {
            "first": "Mike",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Mike.Smith@test.com",
            "age": 22,
            "created": "now"
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
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21,
            "created": "now",
            "v": 4
        }

        expected2 = {
            "first": "Mike",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Mike.Jones@test.com",
            "age": 22,
            "created": "now",
            "v": 4
        }

        doc1 = build("user", "admin")
        doc2 = build("user", "admin", first="Mike")
        self.assertEquals(doc1, expected1)
        self.assertEquals(doc2, expected2)

    def test_create(self):
        
        created = create("user", first='Mike')

        expected = {
            "first": "Mike",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Mike.Smith@test.com",
            "age": 21,
            "created": "now"
        }

        self.assertDictContainsSubset(expected, created)        

    def test_create_named_document(self):
        created = create("user", "admin", first='Mike')

        expected = {
            "first": "Mike",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Mike.Jones@test.com",
            "age": 21,
            "created": "now",
            "v": 4
        }

        self.assertDictContainsSubset(expected, created)        

    def test_build_list(self):
        expected_list = [{
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 21,
            "created": "now"
        }, {
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 22,
            "created": "now"
        }, {
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 23,
            "created": "now"
        }]

        docs = build_list(3, "user")

        self.assertEquals(expected_list, docs)

    def test_build_list_of_named_documents(self):
        expected_list = [{
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21,
            "created": "now",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 22,
            "created": "now",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 23,
            "created": "now",
            "v": 4
        }]

        docs = build_list(3, "user", "admin")

        self.assertEquals(expected_list, docs)


    def test_build_list_of_named_documents_with_overrides(self):
        expected_list = [{
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21,
            "created": "then",
            "favorite_color": "green",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 22,
            "created": "then",
            "favorite_color": "green",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 23,
            "created": "then",
            "favorite_color": "green",
            "v": 4
        }]

        docs = build_list(3, "user", "admin", created="then", favorite_color="green")

        self.assertEquals(expected_list, docs)


    def test_create_list(self):
        expected_docs = [{
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 21,
            "created": "now"
        }, {
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 22,
            "created": "now"
        }, {
            "first": "John",
            "last": "Smith",
            "prefs": {
                "receives_sms": True,
                "receives_email": False,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "John.Smith@test.com",
            "age": 23,
            "created": "now"
        }]
        
        created_docs = create_list(3, "user")
        
        for created, expected in zip(created_docs, expected_docs):
            self.assertDictContainsSubset(expected, created)

    def test_create_list_of_named_documents(self):
        expected_docs = [{
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21,
            "created": "now",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 22,
            "created": "now",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 23,
            "created": "now",
            "v": 4
        }]
        
        created_list = create_list(3, "user", "admin")

        for expected, actual in zip(expected_docs, created_list):
            self.assertDictContainsSubset(expected, actual)


    def test_create_list_of_named_documents_with_overrides(self):
        expected_docs = [{
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 21,
            "created": "then",
            "favorite_color": "green",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 22,
            "created": "then",
            "favorite_color": "green",
            "v": 4
        }, {
            "first": "Bill",
            "last": "Jones",
            "prefs": {
                "receives_sms": False,
                "receives_email": True,
                "v": 4
            },
            "company_id": self.company_id,
            "email": "Bill.Jones@test.com",
            "age": 23,
            "created": "then",
            "favorite_color": "green",
            "v": 4
        }]
        
        created_list = create_list(3, "user", "admin", created="then", favorite_color="green")

        for expected, actual in zip(expected_docs, created_list):
            self.assertDictContainsSubset(expected, actual)

    def test_cleanup(self):
        before_count = self.user_collection.count()
        create("user")
        cleanup()
        after_count = self.user_collection.count()
        self.assertEqual(before_count, after_count)
