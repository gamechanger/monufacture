import os
from pymongo.connection import Connection
from unittest import TestCase, TestLoader, TestResult
from monufacture import factory, create, create_list, reset, default
from monufacture.unittest import enable_factories
from monufacture.helpers import dependent, sequence, subdoc, id_of

host = os.environ.get("DB_IP", "localhost")
port = int(os.environ.get("DB_PORT", 27017))

conn = Connection(host, port).monufacture_test
company_collection = conn.company
user_collection = conn.user


class TestUnittestSupport(TestCase):
    """Uses a phony test case to ensure that when we enable_factories in tests
    we the generated records get cleared up."""

    class TestTestCase(TestCase):
        def __init__(self, *args, **kwargs):
            super(TestUnittestSupport.TestTestCase, self).__init__(*args, **kwargs)
            enable_factories(self)

        def test_some_functionality(self):
            users = create_list(10, "user")
            self.assertEqual(user_collection.count(), 10)
            self.assertEqual("John", users[0]['first'])

        def test_some_other_functionality(self):
            user = create("user", first="Joe")
            self.assertEqual(user_collection.count(), 1)
            self.assertEqual("Joe", user['first'])

    def setUp(self):
        with factory("user", user_collection):
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
        
        with factory("company", company_collection):
            default({
                "name": "GloboCorp"
            })

    def tearDown(self):
        reset()

    def test_data_cleaned_up(self):
        user_collection.remove()
        company_collection.remove()
        loader = TestLoader()
        suite = loader.loadTestsFromTestCase(TestUnittestSupport.TestTestCase)
        result = TestResult()
        suite.run(result)
        self.assertTrue(result.wasSuccessful(), result)
        self.assertEquals(user_collection.count(), 0)
        self.assertEquals(company_collection.count(), 0)
