from unittest import TestCase
from monufacture.dynamic_dict import DynamicDict


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
