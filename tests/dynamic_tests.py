import unittest
from monufacture.dynamic import sequence, dependent, subdoc, id_of, random_text
from mock import patch


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
