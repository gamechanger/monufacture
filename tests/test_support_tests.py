import os
from pymongo.connection import Connection
from unittest import TestCase, TestLoader, TestResult
from monufacture.test_support import enable_factories
from monufacture import factory, dependent, sequence, subdoc, id_of, create, create_list, reset

host = os.environ.get("DB_IP", "localhost")
port = int(os.environ.get("DB_PORT", 27017))

conn = Connection(host, port).monufacture_test
company_collection = conn.company
user_collection = conn.user


class TestTestSupport(TestCase):
    """Uses a phony test case to ensure that when we enable_factories in tests
    we the generated records get cleared up."""

    class TestTestCase(TestCase):
        def __init__(self, *args, **kwargs):
            super(TestTestSupport.TestTestCase, self).__init__(*args, **kwargs)
            enable_factories(self)

        def test_some_functionality(self):
            users = create_list("user", 10)
            self.assertEqual(user_collection.count(), 10)
            self.assertEqual("John", users[0]['first'])

        def test_some_other_functionality(self):
            user = create("user", first="Joe")
            self.assertEqual(user_collection.count(), 1)
            self.assertEqual("Joe", user['first'])

    def setUp(self):
        factory("prefs", {
            "receives_sms":     True,
            "receives_email":   False
        })

        factory("company", {
            "name": "GloboCorp"
        }, company_collection)

        factory("user", {
            "first":        "John",
            "last":         "Smith",
            "prefs":        subdoc("prefs"),
            "company_id":   id_of("company"),
            "email":        dependent(lambda doc: "%s.%s@test.com" % (doc['first'], doc['last'])),
            "age":          sequence(lambda n: n + 20)
        }, user_collection)

    def tearDown(self):
        reset()

    def test_data_cleaned_up(self):
        user_collection.remove()
        company_collection.remove()
        loader = TestLoader()
        suite = loader.loadTestsFromTestCase(TestTestSupport.TestTestCase)
        result = TestResult()
        suite.run(result)
        self.assertTrue(result.wasSuccessful(), result)
        self.assertEquals(user_collection.count(), 0)
        self.assertEquals(company_collection.count(), 0)
