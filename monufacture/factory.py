from dynamic import DynamicDict

class Factory(object):
    def __init__(self, attrs, collection=None):
        self.collection = collection
        self.attrs = attrs
        self.created_ids = []

    def build(self, **overrides):
        """Builds an instance of the document described by the attributes
        used to create this factory without actually persisting it to 
        the database. Any overrides provided are used in preference to 
        those attributes associated with the factory."""
        spec = DynamicDict(self.attrs)
        spec.update(overrides)

        return spec.resolve()

    def create(self, **overrides):
        """Builds an instance of the document using the same approach as 
        `build` but also persists the document to the database."""
        if not self.collection:
            raise IOError("Cannot create an instance when no collection is provided.")

        doc = self.build(**overrides)
        doc_id = self.collection.insert(doc)
        self.created_ids.append(doc_id)
        return self.collection.find_one(doc_id)


    def cleanup(self):
        """Cleanup all instances created by this factory."""
        while len(self.created_ids) > 0:
            self.collection.remove(self.created_ids.pop())
