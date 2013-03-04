from freezegun import freeze_time
import unittest
import monufacture.dynamic
from monufacture.dynamic import sequence, dependent, subdoc, id_of, random_text, dbref_to, date, ago, from_now, list_of, object_id
from mock import patch
from datetime import datetime
from bson.objectid import ObjectId

# Reload monufacture to ensure we're testing against the
# freezegun-patched version of datetime.
reload(monufacture.dynamic)

class TestDynamicFunctions(unittest.TestCase):

    def test_sequence(self):
        func = sequence(lambda n: "Position {0}".format(n))
        self.assertEqual("Position 1", func())
        self.assertEqual("Position 2", func())
        self.assertEqual("Position 3", func())

    def test_sequences_count_independently(self):
        func_a = sequence(lambda n: "Position {0}".format(n))
        func_b = sequence(lambda n: "Item {0}".format(n + 10))
        self.assertEqual("Position 1", func_a())
        self.assertEqual("Position 2", func_a())
        self.assertEqual("Item 11", func_b())
        self.assertEqual("Position 3", func_a())
        self.assertEqual("Item 12", func_b())

    def test_dependent(self):
        func = dependent(lambda doc: "%s %s" % (doc['first'], doc['last']))
        doc_a = {'first': 'John', 'last': 'Smith'}
        doc_b = {'first': 'Bob', 'last': 'Jones'}
        self.assertEqual("John Smith", func(doc_a))
        self.assertEqual("Bob Jones", func(doc_b))

    @patch('monufacture.build')
    def test_subdoc(self, build):
        build.return_value = {"key": "value"}
        func = subdoc("prefs")
        self.assertEqual({"key": "value"}, func())
        build.assert_called_with("prefs")

    @patch('monufacture.create')
    def test_id_of(self, create):
        create.return_value = {"_id": 1234}
        func = id_of("bob")
        self.assertEqual(1234, func())
        create.assert_called_with("bob")

    def test_random_text(self):
        func = random_text()
        text = func()
        self.assertRegexpMatches(text, r'^[a-zA-Z]{10}$')
        text2 = func()
        self.assertNotEqual(text, text2)

    def test_random_text_of_length(self):
        func = random_text(15)
        text = func()
        self.assertEqual(15, len(text))

    def test_random_text_with_spaces(self):
        func = random_text(1000, spaces=True)
        text = func()
        self.assertNotRegexpMatches(text, r'^[a-zA-Z]{1000}$')
        self.assertRegexpMatches(text, r'^[a-zA-Z\s]{1000}$')

    def test_random_text_with_digits(self):
        func = random_text(1000, digits=True)
        text = func()
        self.assertNotRegexpMatches(text, r'^[a-zA-Z]{1000}$')
        self.assertRegexpMatches(text, r'^[a-zA-Z0-9]{1000}$')

    def test_random_text_with_other_chars(self):
        func = random_text(1000, other_chars=[',','.'])
        text = func()
        self.assertNotRegexpMatches(text, r'^[a-zA-Z]{1000}$')
        self.assertRegexpMatches(text, r'^[a-zA-Z.,]{1000}$')

    def test_random_text_with_no_lowercase(self):
        func = random_text(1000, lower=False)
        text = func()
        self.assertRegexpMatches(text, r'^[A-Z]{1000}$')

    def test_random_text_with_no_uppercase(self):
        func = random_text(1000, upper=False)
        text = func()
        self.assertRegexpMatches(text, r'^[a-z]{1000}$')

    @patch('monufacture.create')
    def test_dbref_to(self, create):
        create.return_value = {"_id": 1234}
        func = dbref_to("bob")
        self.assertEqual({"$id": 1234, "$ref": "bob"}, func())
        create.assert_called_with("bob")

    @patch('monufacture.create')
    def test_dbref_to_with_type_override(self, create):
        create.return_value = {"_id": 1234}
        func = dbref_to("bob", type="user")
        self.assertEqual({"$id": 1234, "$ref": "user"}, func())
        create.assert_called_with("bob")

    @freeze_time('2012-01-14 03:21:34')
    def test_date_now(self):
        func = date()
        d = func()
        self.assertEqual(datetime(2012, 1, 14, 3, 21, 34), d)

    def test_date_specified(self):
        func = date(2013, 1, 2, 3, 4, 5, 6)
        d = func()
        self.assertEqual(datetime(2013, 1, 2, 3, 4, 5, 6), d)

    def test_date_specified_with_just_minutes(self):
        func = date(2013, 1, 2, minute=40)
        d = func()
        self.assertEqual(datetime(2013, 1, 2, 0, 40, 0, 0), d)

    def test_valueerror_when_incomplete_date(self):
        with self.assertRaises(ValueError):
            date(2013, 1)

    @freeze_time('2012-01-14 03:21:34')
    def test_5_minutes_ago(self):
        func = ago(minutes=5)
        d = func()
        self.assertEqual(datetime(2012, 1, 14, 3, 16, 34), d)

    @freeze_time('2012-01-14 03:21:34')
    def test_2_days_50_seconds_ago(self):
        func = ago(days=2, seconds=50)
        d = func()
        self.assertEqual(datetime(2012, 1, 12, 3, 20, 44), d)

    @freeze_time('2012-01-14 03:21:34')
    def test_5_minutes_from_now(self):
        func = from_now(minutes=5)
        d = func()
        self.assertEqual(datetime(2012, 1, 14, 3, 26, 34), d)

    @freeze_time('2012-01-14 03:21:34')
    def test_2_days_50_seconds_from_now(self):
        func = from_now(days=2, seconds=50)
        d = func()
        self.assertEqual(datetime(2012, 1, 16, 3, 22, 24), d)

    def test_list_of(self):
        func = lambda x: x
        self.assertEqual(list_of(func, 5)('a'), ['a'] * 5)

    def test_object_id(self):
        func = object_id()
        d = func()
        self.assertIsInstance(d, ObjectId)
