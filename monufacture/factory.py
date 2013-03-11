from dynamic import DynamicDict

class Factory(object):
    def __init__(self, collection=None):
        self.collection = collection
        self.created_ids = []
        self.default_document = {}
        self.documents = {}
        self.parents = {}

    def _build_document(self, name=None):
        if not name or name == "default":
            doc = self.default_document
        else:
            doc = self.documents[name]

        if name in self.parents:
            spec = self._build_document(self.parents[name])
            spec.update(doc)
        else:
            spec = DynamicDict(doc)

        return spec

    def build(self, name=None, **overrides):
        """Builds an instance of the document described by the attributes
        used to create this factory without actually persisting it to 
        the database. Any overrides provided are used in preference to 
        those attributes associated with the factory."""
        if name and name not in self.documents:
            raise NonExistentDocumentException(name)
        
        spec = self._build_document(name)
        
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

    def document(self, name, attrs, parent=None):
        if name == 'default':
            raise FactoryDeclarationException("Cannot register a factory document with the name 'default'")

        if parent:
            self.parents[name] = parent

        self.documents[name] = attrs


class NonExistentDocumentException(Exception):
    """Raised when the caller attempts to access a non-existent
    document."""
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Document declaration not found: \"%s\"" % self.name

class FactoryDeclarationException(Exception):
    """Raised when an error has been detected in the declaration of a 
    factory."""
    pass
