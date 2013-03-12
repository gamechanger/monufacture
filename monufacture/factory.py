from dynamic import DynamicDict

class Factory(object):
    def __init__(self, collection=None):
        self.collection = collection
        self.created_ids = []
        self.documents = {}
        self.document_parents = {}
        self.document_traits = {}
        self.traits = {}
        self.trait_parents = {}
        self.fragments = {}
        self.fragment_traits = {}
        self.fragment_parents = {}

    def _apply_traits(self, doc, traits):
        for trait in traits:
            doc.update(self._build_trait(trait))

    def _build_fragment(self, name):
        if name in self.fragment_parents:
            spec = self._build_fragment(self.fragment_parents[name])
            spec.update(self.fragments[name])
        else:
            spec = self.fragments[name]

        if name in self.fragment_traits:
            self._apply_traits(spec, self.fragment_traits[name])

        return spec

    def _build_trait(self, name):
        if name in self.trait_parents:
            spec = self._build_trait(self.trait_parents[name])
            spec.update(self.traits[name])
        else:
            spec = self.traits[name]
        return spec

    def _build_document(self, name):
        doc = self.documents[name]

        if name in self.document_parents:
            spec = self._build_document(self.document_parents[name])
        else:
            spec = DynamicDict()
        
        if name in self.document_traits:
            self._apply_traits(spec, self.document_traits[name])

        spec.update(doc)

        return spec

    def build(self, name=None, **overrides):
        """Builds an instance of the document described by the attributes
        used to create this factory without actually persisting it to 
        the database. Any overrides provided are used in preference to 
        those attributes associated with the factory."""
        if not name:
            name = "default"

        if name not in self.documents:
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
        doc_id = self.collection.insert(doc, safe=True)
        self.created_ids.append(doc_id)
        return self.collection.find_one(doc_id)


    def cleanup(self):
        """Cleanup all instances created by this factory."""
        while len(self.created_ids) > 0:
            self.collection.remove(self.created_ids.pop(), safe=True)

    def default(self, attrs, traits=[]):
        """Sets the default document dict for the factory."""
        self.document_traits["default"] = traits
        self.documents["default"] = attrs

    def document(self, name, attrs, parent=None, traits=[]):
        """Declares a named document type within the factory."""
        if name == 'default':
            raise FactoryDeclarationException("Cannot register a factory document with the name 'default'")

        if parent:
            self.document_parents[name] = parent

        self.document_traits[name] = traits

        self.documents[name] = attrs

    def trait(self, name, attrs, parent=None):
        """Declares a reusable trait hash which can be referenced in
        documents."""
        self.traits[name] = attrs
        if parent:
            self.trait_parents[name] = parent

    def fragment(self, name, attrs, parent=None, traits=[]):
        if parent:
            self.fragment_parents[name] = parent

        self.fragment_traits[name] = traits
        self.fragments[name] = attrs

    def embed(self, name):
        def build(*args):
            return self._build_fragment(name)

        return build

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
