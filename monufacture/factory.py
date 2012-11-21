from types import FunctionType


class Factory(object):
    def __init__(self, database, collection, **attrs):
        self.database = database
        self.collection = collection
        self.attrs = attrs

    def build(self):
        """Builds an instance of the document described by the sttributes
        provided to this factory without actually persisting it to 
        the database."""
        doc = {}
        for key, value in self.attrs.items():
            if isinstance(value, FunctionType):
                doc[key] = value()
            else:
                doc[key] = value
        return doc

