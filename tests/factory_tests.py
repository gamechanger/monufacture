import unittest
from monufacture.factory import Factory, NonExistentDocumentException, FactoryDeclarationException
from mock import Mock, call
from bson.objectid import ObjectId
from copy import copy
from datetime import datetime


class TestFactory(unittest.TestCase):

    def setUp(self):
        self.collection = Mock()

    def test_build_default_document(self):
        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        self.assertDictEqual(factory.build(), {
            "first_name": "John",
            "last_name": "Smith",
            "age": 32
        })

    def test_build_with_function_attrs(self):
        def full_name(doc, *args):
            return "%s %s" % (doc['first_name'], doc['last_name'])

        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "full_name": full_name,
            "age": 32
        })

        self.assertDictEqual(factory.build(), {
            "first_name": "John",
            "last_name": "Smith",
            "full_name": "John Smith",
            "age": 32
        })

    def test_build_with_overrides(self):
        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        self.assertDictEqual(factory.build(first_name='Mike', age=45), {
            "first_name": "Mike",
            "last_name": "Smith",
            "age": 45
        })

    def test_build_with_function_and_overrides(self):
        def full_name(doc, *args):
            return "%s %s" % (doc['first_name'], doc['last_name'])

        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "full_name": full_name,
            "age": 32
        })

        self.assertDictEqual(factory.build(first_name='Mike', age=45), {
            "first_name": "Mike",
            "last_name": "Smith",
            "full_name": "Mike Smith",
            "age": 45
        })

    def test_build_with_inheritance(self):
        factory = Factory(self.collection)
        factory.default({
            "location": lambda doc: "pittsburgh"
        })

        factory.document("smith", {"last_name": "Smith"}, parent="default")
        factory.document("bob", {
            "first_name": lambda doc: "Bob"},
            parent="smith")
        factory.document("mike", {
            "first_name": "Mike"},
            parent="smith")

        self.assertDictEqual(factory.build(), {"location":"pittsburgh"})
        self.assertDictEqual(factory.build("smith"), {
            "location": "pittsburgh",
            "last_name": "Smith"
        })
        self.assertDictEqual(factory.build("bob"), {
            "location": "pittsburgh",
            "last_name": "Smith",
            "first_name": "Bob"
        })
        self.assertDictEqual(factory.build("mike"), {
            "location": "pittsburgh",
            "last_name": "Smith",
            "first_name": "Mike"
        })

        # Lets also test the overrides still work
        self.assertDictEqual(factory.build("bob", last_name="jones"), {
            "location": "pittsburgh",
            "last_name": "jones",
            "first_name": "Bob"
        })
        self.assertDictEqual(factory.build("mike", other="thing"), {
            "location": "pittsburgh",
            "last_name": "Smith",
            "first_name": "Mike",
            "other": "thing"
        })
        

    def test_build_with_traits(self):
        factory = Factory(self.collection)
        factory.trait("timestamped", {
            "created": lambda doc: datetime(2001, 1, 1, 1, 1, 1)
        })
        factory.trait("versioned", {
            "v": 3
        })
        factory.document("car", {
            "wheels": 4, 
            "make": lambda doc: "Mazda"
        }, traits=["timestamped", "versioned"])

        expected = {
            "wheels": 4,
            "make": "Mazda",
            "created": datetime(2001, 1, 1, 1, 1, 1),
            "v": 3
        }

        self.assertDictEqual(expected, factory.build("car"))


    def test_build_default_with_traits(self):
        factory = Factory(self.collection)
        factory.trait("timestamped", {
            "created": lambda doc: datetime(2001, 1, 1, 1, 1, 1)
        })
        factory.trait("versioned", {
            "v": 3
        })
        factory.default({
            "wheels": 4, 
            "make": lambda doc: "Mazda"
        }, traits=["timestamped", "versioned"])

        expected = {
            "wheels": 4,
            "make": "Mazda",
            "created": datetime(2001, 1, 1, 1, 1, 1),
            "v": 3
        }

        self.assertDictEqual(expected, factory.build())


    def test_build_with_inheritance_and_traits(self):
        factory = Factory(self.collection)
        factory.trait("timestamped", {
            "created": lambda doc: datetime(2001, 1, 1, 1, 1, 1)
        })
        factory.trait("versioned", {
            "v": 3
        })
        factory.document("car", {
            "wheels": 4
        }, traits=["timestamped", "versioned"])
        factory.document("mazda", {
            "make": lambda doc: "Mazda"
        }, parent="car")

        expected = {
            "wheels": 4,
            "make": "Mazda",
            "created": datetime(2001, 1, 1, 1, 1, 1),
            "v": 3
        }

        self.assertDictEqual(expected, factory.build("mazda"))


    def test_build_with_trait_inheritance(self):
        # this is testing inheritance of traits, not traits plus doc inheritance
        factory = Factory(self.collection)
        factory.trait("timestamped", {
            "created": lambda doc: datetime(2001, 1, 1, 1, 1, 1)
        })
        
        factory.trait("versioned", {
            "v": 3
        }, parent="timestamped")

        factory.document("car", {
            "wheels": 4
        }, traits=["versioned"])
        
        factory.document("mazda", {
            "make": lambda doc: "Mazda"
        }, parent="car")

        expected = {
            "wheels": 4,
            "make": "Mazda",
            "created": datetime(2001, 1, 1, 1, 1, 1),
            "v": 3
        }

        self.assertDictEqual(expected, factory.build("mazda"))


    def test_successive_builds_with_different_overrides(self):
        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        self.assertDictEqual(factory.build(first_name='Mike', age=45), {
            "first_name": "Mike",
            "last_name": "Smith",
            "age": 45
        })

        self.assertDictEqual(factory.build(last_name='Jones'), {
            "first_name": "John",
            "last_name": "Jones",
            "age": 32
        })


    def test_fragments(self):
        factory = Factory(self.collection)
        factory.fragment("alert_prefs", {
            "emails": True
        })
        factory.document("user", {
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32, 
            "alerts": factory.embed("alert_prefs")
        })
        self.assertDictEqual(factory.build("user"), {
            "first_name": "John",
            "last_name": "Smith",
            "age": 32,
            "alerts": {
                "emails": True
            }
        })


    def test_fragments_with_traits(self):
        factory = Factory(self.collection)
        factory.trait('versioned', {"v": 5})
        factory.fragment("alert_prefs", {
            "emails": True
        }, traits=['versioned'])
        factory.document("user", {
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32, 
            "alerts": factory.embed("alert_prefs")
        })
        self.assertDictEqual(factory.build("user"), {
            "first_name": "John",
            "last_name": "Smith",
            "age": 32,
            "alerts": {
                "emails": True,
                "v": 5
            }
        })


    def test_fragments_with_inheritance(self):
        factory = Factory(self.collection)
        factory.fragment('versioned', {"v": 5})
        factory.fragment("alert_prefs", {
            "emails": True
        }, parent='versioned')
        factory.document("user", {
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32, 
            "alerts": factory.embed("alert_prefs")
        })
        self.assertDictEqual(factory.build("user"), {
            "first_name": "John",
            "last_name": "Smith",
            "age": 32,
            "alerts": {
                "emails": True,
                "v": 5
            }
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

        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        created = factory.create()

        self.collection.insert.assert_called_with({
            "first_name": "John",
            "last_name": "Smith",
            "age": 32
        }, safe=True)
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

        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        created = factory.create(first_name='Mike')

        self.collection.insert.assert_called_with({
            "first_name": "Mike",
            "last_name": "Smith",
            "age": 32
        }, safe=True)
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

        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        created = factory.create(gender='male')

        self.collection.insert.assert_called_with({
            "first_name": "John",
            "last_name": "Smith",
            "age": 32,
            "gender": "male"
        }, safe=True)
        self.collection.find_one.assert_called_with(to_return["_id"])
        self.assertDictEqual(created, to_return)


    def test_build_without_declaring_default_document(self):
        factory = Factory(self.collection)
        with self.assertRaises(NonExistentDocumentException):
            factory.build()
        

    def test_build_named_document(self):
        def full_name(doc):
            return "%s %s" % (doc['first_name'], doc['last_name'])

        factory = Factory(self.collection)
        factory.document('admin', {
            "first_name": 'John',
            "last_name": 'Smith',
            "full_name": full_name,
            "age": 32
        })

        self.assertDictEqual(factory.build('admin', first_name='Mike', age=45), {
            "first_name": "Mike",
            "last_name": "Smith",
            "full_name": "Mike Smith",
            "age": 45
        })

    def test_document_cannot_be_named_default(self):
        factory = Factory(self.collection)
        with self.assertRaises(FactoryDeclarationException):
            factory.document('default', {"some": 'thing'})

    def test_build_nonexistent_document(self):
        factory = Factory(self.collection)
        with self.assertRaises(NonExistentDocumentException):
            factory.build('nonexistent')


    def test_create_named_document(self):
        to_return = {
            "_id": ObjectId(),
            "first_name": "John",
            "last_name": "Smith",
            "age": 45,
            "gender": "male"
        }

        self.collection.insert = Mock(return_value=to_return["_id"])
        self.collection.find_one = Mock(return_value=to_return)

        factory = Factory(self.collection)
        factory.document('admin', {
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        created = factory.create('admin', gender='male', age=45)

        self.collection.insert.assert_called_with({
            "first_name": "John",
            "last_name": "Smith",
            "age": 45,
            "gender": "male"
        }, safe=True)
        self.collection.find_one.assert_called_with(to_return["_id"])
        self.assertDictEqual(created, to_return)


    def test_cleanup_nothing_to_do(self):
        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })

        factory.cleanup()

        expected_calls = []
        self.assertEqual(self.collection.remove.mock_calls, expected_calls)

    def test_cleanup(self):
        ids = [ObjectId() for x in range(3)]
        cleanup_ids = copy(ids)
        cleanup_ids.reverse()

        def insert_results(*args, **kwargs):
            return ids.pop(0)

        self.collection.insert = Mock(side_effect=insert_results)

        factory = Factory(self.collection)
        factory.default({
            "first_name": 'John',
            "last_name": 'Smith',
            "age": 32
        })
        factory.document('admin', {
            "first_name": 'Mick',
            "last_name": 'Jones',
            "age": 33
        })

        for x in range(2):
            factory.create()
        factory.create('admin')

        factory.cleanup()

        expected_calls = [call(oid, safe=True) for oid in cleanup_ids]
        self.assertEqual(self.collection.remove.mock_calls, expected_calls)
        self.collection.reset_mock()
        factory.cleanup()
        self.assertFalse(self.collection.remove.called)
