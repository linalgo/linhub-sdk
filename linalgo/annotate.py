from collections import defaultdict, MutableSequence
from mock.mock import self


class Annotation:

    def __init__(self, uri, type_id, task_id, text, owner, document_id,
                 annotation_id=None):
        self.id = annotation_id
        self.uri = uri
        self.type_id = type_id
        self.task_id = task_id
        self.text = text
        self.owner = owner
        self.document_id = document_id

    def __repr__(self):
        return str(self.type_id)


class Annotations(MutableSequence):

    def __init__(self, annotations=None):
        super(Annotations, self).__init__()
        self._list = []
        self._user_index = defaultdict(list)
        self._type_index = defaultdict(list)
        for annotation in annotations:
            self.append(annotation)

    def get_users(self):
        return self._user_index.keys()

    def by_user(self, name):
        return self._user_index[name]

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, ii):
        return self._list[ii]

    def __delitem__(self, ii):
        del self._list[ii]

    def __setitem__(self, ii, val):
        self._list[ii] = val

    def __str__(self):
        return str(self._list)

    def insert(self, ii, val):
        self._list.insert(ii, val)

    def append(self, val):
        self.insert(len(self._list), val)
        self._user_index[val.owner].append(val)
        self._type_index[val.type_id].append(val)


class Annotator:

    def __init__(self, name):
        self.name = name

    def annotate(self, document, annotation):
        document.annotations.add(annotation)


class Document:

    def __init__(self, name, content, corpus, metadata=None, document_id=None):
        self.name = name
        self.content = content
        self.corpus = corpus
        self.metadata = metadata
        self.id = document_id
        self._annotations = Annotations([])

    @property
    def labels(self):
        return set(annotation.type_id for annotation in self.annotations)

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, values):
        self._annotations = Annotations(values)


class Task:

    def __init__(self, name, description, entities=None, corpora=None,
                 annotators=None, annotations=[], documents=[], task_id=None):
        self.id = task_id
        self.name = name
        self.description = description
        self.entities = entities
        self.corpora = corpora
        self.annotators = annotators
        self._annotations = annotations
        self._documents = documents

    @property
    def documents(self):
        return list(self._documents.values())

    @documents.setter
    def documents(self, values):
        self._documents = dict((doc.id, doc) for doc in values)

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, values):
        self._annotations = Annotations(values)
        for annotation in self.annotations:
            doc_id = annotation.document_id
            self._documents[doc_id].annotations.append(annotation)

    def transform(self, target='binary', label=None):
        docs = []
        labels = []
        for doc in self.documents:
            docs.append(doc.content)
            labels.append(1 if label in doc.labels else 0)
        return docs, labels

    def __repr__(self):
        rep = (f"name: {self.name}\ndescription: {self.description}\n# "
               f"documents: {len(self.documents)}\n# annotations: "
               f"{len(self.annotations)}")
        if self.id:
            rep = f"id: {self.id}\n" + rep
        return rep
