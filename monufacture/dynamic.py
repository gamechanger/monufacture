from types import FunctionType


def getitem(self, index, superclass):
    """Override __getitem__ implementation shared by both dynamic dicts
    and lists."""

    inner = superclass.__getitem__(index)

    # If the value is a function, invoke it to get, set and return
    # the value.
    if isinstance(inner, FunctionType):
        self[index] = inner(self)

    # If the value is an embedded dict, we need to wrap it in a
    # DynamicDict instance.
    elif isinstance(inner, dict):
        self[index] = DynamicDict(inner, head=self.head)

    # If the value is an embedded list, we need to wrap it in a
    # DynamicList instance.
    elif isinstance(inner, list):
        self[index] = DynamicList(inner, head=self.head)

    return superclass.__getitem__(index)


class DynamicList(list):
    """ A subclass of dict which checks whether a given index's value is a
    function, and if so return the result of calling that function.
    Note that each function is only called once."""

    def __init__(self, inner_list, head=None, *args, **kwargs):
        super(DynamicList, self).__init__(*args, **kwargs)
        self.head = self if not head else head
        self.extend(inner_list)

    def __getitem__(self, index):
        return getitem(self, index, super(DynamicList, self))

    def resolve(self):
        """"Resolves the dynamic list into a static list with
        static values."""
        
        out = []
        for i in range(len(self)):
            value = self[i]
            if isinstance(value, DynamicDict) or isinstance(value, DynamicList):
                out.append(value.resolve())
            else:
                out.append(value)

        return out

class DynamicDict(dict):
    """ A subclass of dict which checks whether a given key's value is a
    function, and if so return the result of calling that function.
    Note that each function is only called once."""

    def __init__(self, inner_dict, head=None, *args, **kwargs):
        super(DynamicDict, self).__init__(*args, **kwargs)
        self.head = self if not head else head
        self.update(inner_dict)

    def __getitem__(self, key):
        return getitem(self, key, super(DynamicDict, self))

    def resolve(self):
        """"Resolves the dynamic dictionary into a static dictionary with
        static values."""
        
        out = {}
        for key in self:
            value = self[key]

            if isinstance(value, DynamicDict) or isinstance(value, DynamicList):
                out[key] = value.resolve()
            else:
                out[key] = value

        return out
