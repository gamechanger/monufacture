import unittest
from monufacture.dynamic import sequence, dependent


class TestSequence(unittest.TestCase):

    def test_basic_operation(self):
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


class TestDependent(unittest.TestCase):

    def test_basic_operation(self):
        func = dependent(lambda doc: "%s %s" % (doc['first'], doc['last']))
        doc_a = {'first': 'John', 'last': 'Smith'}
        doc_b = {'first': 'Bob', 'last': 'Jones'}
        self.assertEqual("John Smith", func(doc_a))
        self.assertEqual("Bob Jones", func(doc_b))
