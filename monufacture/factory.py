from types import FunctionType

class Factory(object):
    def __init__(self, collection, **attrs):
        self.collection = collection
        self.attrs = attrs

    def build(self, **overrides):
        """Builds an instance of the document described by the attributes
        used to create this factory without actually persisting it to 
        the database. Any overrides provided are used in preference to 
        those attributes associated with the factory."""
        doc = {}

        # Do two passes, the first to set the static values, the second
        # to apply functions which may or not depend on static values.
        for key, value in self.attrs.items():
            if not isinstance(value, FunctionType):
                # Use the override if present
                if key in overrides:
                    doc[key] = overrides[key]
                    continue

                doc[key] = value

        for key, value in self.attrs.items():
            if isinstance(value, FunctionType):
                # Use the override if present
                if key in overrides:
                    doc[key] = overrides[key]
                    continue

                doc[key] = value(doc)

        return doc

    def create(self, **overrides):
        """Builds an instance of the document using the same approach as 
        `build` but also persists the document to the database."""
        doc = self.build(**overrides)
        doc_id = self.collection.insert(doc)
        return self.collection.find_one(doc_id)
