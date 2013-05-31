from dynamic import DynamicDict

class Document(object):
    def __init__(self, attrs, parent=None, traits=[]):
        self.attrs = attrs
        self.parent = parent
        self.traits = traits


class Trait(object):
    def __init__(self, attrs, parent=None):
        self.attrs = attrs
        self.parent = parent


class Fragment(object):
    def __init__(self, attrs, parent=None, traits=[]):
        self.attrs = attrs
        self.parent = parent
        self.traits = traits


class Factory(object):
    def __init__(self, collection=None, global_traits={}):
        self.collection = collection
        self.created_ids = []
        self.documents = {}
        self.traits = {}
        self.fragments = {}
        self.global_traits = global_traits


    def _apply_traits(self, doc, traits):
        for trait in traits:
            doc.update(self._build_trait(trait))

    def _build_fragment(self, name):
        fragment = self.fragments[name]
        if fragment.parent:
            spec = self._build_fragment(fragment.parent)
        else:
            spec = DynamicDict()

        if fragment.traits:
            self._apply_traits(spec, fragment.traits)

        spec.update(fragment.attrs)
        return spec

    def _build_trait(self, name):
        trait = self.traits.get(name) or self.global_traits.get(name)
        if trait.parent:
            spec = self._build_trait(trait.parent)
        else:
            spec = DynamicDict()

        spec.update(trait.attrs)
        return spec

    def _build_document(self, name):
        doc = self.documents[name]

        if doc.parent:
            spec = self._build_document(doc.parent)
        else:
            spec = DynamicDict()

        if doc.traits:
            self._apply_traits(spec, doc.traits)

        spec.update(doc.attrs)
        return spec

    def build(self, name_=None, **overrides):
        """Builds an instance of the document described by the attributes
        used to create this factory without actually persisting it to
        the database. Any overrides provided are used in preference to
        those attributes associated with the factory."""
        if not name_:
            name_ = "default"

        if name_ not in self.documents:
            raise NonExistentDocumentException(name_)

        spec = self._build_document(name_)

        spec.update(overrides)
        return spec.resolve()

    def create(self, name_=None, **overrides):
        """Builds an instance of the document using the same approach as
        `build` but also persists the document to the database."""
        if not self.collection:
            raise IOError("Cannot create an instance when no collection is provided.")

        doc = self.build(name_, **overrides)
        doc_id = self.collection.insert(doc, safe=True)
        self.created_ids.append(doc_id)
        return self.collection.find_one(doc_id)


    def cleanup(self):
        """Cleanup all instances created by this factory."""
        while len(self.created_ids) > 0:
            self.collection.remove(self.created_ids.pop(), safe=True)

    def default(self, attrs, traits=[]):
        """Sets the default document dict for the factory."""
        self.documents["default"] = Document(attrs, traits=traits)

    def document(self, name, attrs=None, parent=None, traits=[]):
        """Declares a named document type within the factory."""
        if name == 'default':
            raise FactoryDeclarationException("Cannot register a factory document with the name 'default'")

        self.documents[name] = Document(attrs or {}, parent, traits)

    def trait(self, name, attrs, parent=None):
        """Declares a reusable trait hash which can be referenced in
        documents."""
        self.traits[name] = Trait(attrs, parent)

    def fragment(self, name, attrs=None, parent=None, traits=[]):
        self.fragments[name] = Fragment(attrs or {}, parent, traits)

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
