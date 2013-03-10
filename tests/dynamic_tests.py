from unittest import TestCase
from monufacture.dynamic import DynamicDict

class TestDynamicDict(TestCase):

    def test_non_dynamic_dict(self):
        d = DynamicDict({
            "astring": "some text",
            "anint": 33
        })

        self.assertEqual("some text", d["astring"])
        self.assertEqual(33, d["anint"])

    def test_dict_with_function_values(self):
        def some_func(node, root):
            self.assertEqual(d, node)
            self.assertEqual(d, root)
            return "func text"

        d = DynamicDict({
            "astring": "some text",
            "afunc": some_func
        })

        self.assertEqual("some text", d["astring"])
        self.assertEqual("func text", d["afunc"])

    def test_dict_with_nested_function_values(self):
        def some_func(node, root):
            self.assertEqual(d['sub'], node)
            self.assertEqual(d, root)
            return "func text"

        d = DynamicDict({
            "astring": "some text",
            "sub": {
                "afunc": some_func
            }
        })

        self.assertEqual("some text", d["astring"])
        self.assertEqual("func text", d["sub"]["afunc"])

    def test_dict_with_list_nested_function_values(self):
        def some_func(node, root):
            self.assertEqual(d, root)
            self.assertEqual(d["sub"], node)
            return "func text"

        d = DynamicDict({
            "astring": "some text",
            "sub": [some_func]
        })

        self.assertEqual("some text", d["astring"])
        self.assertEqual("func text", d["sub"][0])

    def test_dict_with_double_nested_list(self):
        def some_func(node, root):
            self.assertEqual(d, root)
            self.assertEqual(d["sub"][0], node)
            return "func text"

        d = DynamicDict({
            "astring": "some text",
            "sub": [[some_func]]
        })

        self.assertEqual("some text", d["astring"])
        self.assertEqual("func text", d["sub"][0][0])

    def test_uber_complex_structure(self):
        def a(node, root):
            self.assertEqual(doc, root)
            self.assertEqual(doc, node)
            return "value a"

        def d(node, root):
            self.assertEqual(doc, root)
            self.assertEqual(doc['b']['c'], node)
            return "value d"

        def g(node, root):
            self.assertEqual(doc, root)
            self.assertEqual(doc['b']['e'][0]['f'], node)
            return "value g"

        def h(node, root):
            self.assertEqual(doc, root)
            self.assertEqual(doc['b']['e'][0], node)
            return "value h"

        doc = DynamicDict({
            "a": a,
            "b": {
                "c": {
                    "d": d
                },
                "e": [
                    {
                        "f": [g],
                        "h": h
                    }
                ]
            }
        })

        self.assertEqual("value a", doc['a'])
        self.assertEqual("value d", doc['b']['c']['d'])
        self.assertEqual("value g", doc['b']['e'][0]['f'][0])
        self.assertEqual("value h", doc['b']['e'][0]['h'])

    def test_resolve(self):
        def a(node, root):
            return "value a"

        def d(node, root):
            return "value d"

        def g(node, root):
            return "value g"

        def h(node, root):
            return "value h"

        doc = DynamicDict({
            "a": a,
            "b": {
                "c": {
                    "d": d
                },
                "e": [
                    {
                        "f": [g],
                        "h": h
                    }
                ]
            }
        })

        expected = {
            "a": "value a",
            "b": {
                "c": {
                    "d": "value d"
                },
                "e": [
                    {
                        "f": ["value g"],
                        "h": "value h"
                    }
                ]
            }
        }

        self.assertEqual(expected, doc.resolve())
