from dynamic import DynamicDict

class Factory(object):
    def __init__(self, collection=None):
        self.collection = collection
        self.created_ids = []
        self.default_document = {}
        self.documents = {}

    def build(self, name=None, **overrides):
        """Builds an instance of the document described by the attributes
        used to create this factory without actually persisting it to 
        the database. Any overrides provided are used in preference to 
        those attributes associated with the factory."""
        doc = self.default_document
        if name:
            if name not in self.documents:
                raise NonExistentDocumentException(name)

            doc = self.documents[name]

        spec = DynamicDict(doc)
        spec.update(overrides)
        return spec.resolve()

    def create(self, name=None, **overrides):
        """Builds an instance of the document using the same approach as 
        `build` but also persists the document to the database."""
        if not self.collection:
            raise IOError("Cannot create an instance when no collection is provided.")

        doc = self.build(name, **overrides)
        doc_id = self.collection.insert(doc)
        self.created_ids.append(doc_id)
        return self.collection.find_one(doc_id)


    def cleanup(self):
        """Cleanup all instances created by this factory."""
        while len(self.created_ids) > 0:
            self.collection.remove(self.created_ids.pop())

    def default(self, attrs):
        self.default_document = attrs

    def document(self, name, attrs):
        self.documents[name] = attrs


class NonExistentDocumentException(Exception):
    """Raised when the caller attempts to access a non-existent
    document."""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Document declaration not found: \"%s\"" % self.name
