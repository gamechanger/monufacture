from types import FunctionType


class DynamicList(list):

    def __init__(self, inner_list, head=None, *args, **kwargs):
        super(DynamicList, self).__init__(*args, **kwargs)
        self.head = self if not head else head
        self.extend(inner_list)

    def __getitem__(self, index):
        inner = super(DynamicList, self).__getitem__(index)

        # If the value is a function, invoke it to get, set and return
        # the value.
        if isinstance(inner, FunctionType):
            self[index] = inner(self, self.head)

        # If the value is an embedded dict, we need to wrap it in a
        # DynamicDict instance.
        elif isinstance(inner, dict):
            self[index] = DynamicDict(inner, head=self.head)

        elif isinstance(inner, list):
            self[index] = DynamicList(inner, head=self.head)

        return super(DynamicList, self).__getitem__(index)


class DynamicDict(dict):
    """ A subclass of dict which checks whether a given key's value is a
    function, and if so return the result of calling that function.
    Note that each function is only called once."""

    def __init__(self, inner_dict, head=None, *args, **kwargs):
        super(DynamicDict, self).__init__(*args, **kwargs)
        self.head = self if not head else head
        self.update(inner_dict)

    def __getitem__(self, key):
        inner = super(DynamicDict, self).__getitem__(key)

        # If the value is a function, invoke it to get, set and return
        # the value.
        if isinstance(inner, FunctionType):
            self[key] = inner(self, self.head)

        # If the value is an embedded dict, we need to wrap it in a
        # DynamicDict instance.
        elif isinstance(inner, dict):
            self[key] = DynamicDict(inner, head=self.head)

        elif isinstance(inner, list):
            self[key] = DynamicList(inner, head=self.head)

        return super(DynamicDict, self).__getitem__(key)
