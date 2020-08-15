from collections import defaultdict, MutableSequence
from typing import Iterable, List, Union
import uuid

from linalgo.annotate.bbox import BoundingBox

Selector = Union[BoundingBox]


class Target:

    def __init__(self, source: 'Document' = None,
                 selectors: Iterable[Selector] = []):
        self.source = source
        self.selectors = selectors


class RegistryMixin:

    def __new__(cls, *args, **kwargs):
        unique_id = kwargs.get('unique_id', uuid.uuid1())
        if not hasattr(cls, '_registry'):
            cls._registry = dict()
        if unique_id in cls._registry:
            return cls._registry[unique_id]
        else:
            obj = super().__new__(cls)
            obj.id = unique_id
            return obj

    def register(self):
        self._registry[self.id] = self


class FromIdFactoryMixin:

    @classmethod
    def factory(cls, arg):
        if arg is None:
            return None
        elif type(arg) == cls:
            return arg
        elif type(arg) == str:
            return cls(unique_id=arg)
        else:
            raise Exception(f'No factory method found for type {type(arg)}')


class Annotation(RegistryMixin, FromIdFactoryMixin):
    """
    Annotation class compatible with the W3C annotation data model.
    """

    def __init__(self, entity: 'Entity' = None, body: str = None,
                 annotator: 'Annotator' = None, task: 'Task' = None,
                 document: 'Document' = None, created=None,
                 target: Target = None, score: float = None, **kwargs):
        self.entity = Entity.factory(entity)
        self.score = score
        self.body = body
        self.task = Task.factory(task)
        self.annotator = Annotator.factory(annotator)
        self.document = Document.factory(document)
        self.target = target
        self.created = created
        self.register()

    @staticmethod
    def from_json(js):
        return Annotation(
            unique_id=js['id'],
            entity=Entity(unique_id=js['entity']),
            body=js['body'],
            annotator=Annotator(unique_id=js['annotator']),
            document=Document(unique_id=js['document']),
            task=Task(unique_id=js['task']),
            target=js['target'],
            created=js['created']
        )

    def __repr__(self):
        return f'{self.id.hex}::{self.entity.name}'


class Annotations(MutableSequence):
    """
    Class to list of annotations with custom indexing.
    """

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
        self._user_index[val.annotator].append(val)
        self._type_index[val.type_id].append(val)


class Annotator(RegistryMixin, FromIdFactoryMixin):
    """
    The Annotator class can create, delete or modify Annotations.
    """

    def __init__(self, name: str = None, model=None, task: 'Task' = None,
                 annotation_type_id=None, threshold: float = 0, **kwargs):
        self.name = name
        self.task = Task.factory(task)
        self.model = model
        self.type_id = annotation_type_id
        self.threshold = threshold
        self.register()

    def __repr__(self):
        return self.name or self.id.hex

    @staticmethod
    def from_json(js):
        return Annotator(
            unique_id=js['id'],
            name=js['name'],
            model=js['model']
        )

    def assign_task(self, task):
        self.task = task

    def _get_annotation(self, document):
        score = self.model.decision_function([document.content])[0]
        if score >= self.threshold:
            label = self.type_id
        else:
            label = 1  # Viewed
        annotation = Annotation(
            type_id=label,
            score=score,
            text=document.content,
            annotator=self.annotator_id,
            task_id=self.task.id,
            document_id=document.id
        )
        return annotation

    def annotate(self, document):
        annotation = self._get_annotation(document)
        if annotation is not None:
            self.task.annotations.append(annotation)
            document.annotations.append(annotation)
        return annotation


class Corpus(RegistryMixin, FromIdFactoryMixin):

    def __init__(self, name: str, description: str,
                 documents: Iterable['Document'] = [], **kwargs):
        self.name = name
        self.description = description
        self.documents = [Document.factory(d) for d in documents]
        self.register()

    def __repr__(self):
        return self.name or self.id.hex


class Document(RegistryMixin, FromIdFactoryMixin):
    """
    Base class that holds the document on which to perform annotations.
    """

    def __init__(self, content: str = None, uri: str = None,
                 corpus: Corpus = None, **kwargs):
        self.uri = uri
        self.content = content
        self.corpus = Corpus.factory(corpus)
        self._annotations = Annotations([])
        self.register()

    def __repr__(self):
        return self.id.hex

    @staticmethod
    def from_json(js):
        return Document(
            uri=js['uri'],
            content=js['content'],
            corpus=Corpus(js['corpus']),
            document_id=js['id']
        )

    @property
    def labels(self):
        return set(annotation.type_id for annotation in self.annotations)

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, values):
        self._annotations = Annotations(values)


class Entity(RegistryMixin, FromIdFactoryMixin):

    def __init__(self, name: str = None, color: str = None, **kwargs):
        self.name = name or self.id
        self.color = color
        self.register()

    def __repr__(self):
        return self.name or str(self.id)


class Task(RegistryMixin, FromIdFactoryMixin):
    """
    The Task class contains all information about a task: entities, corpora, 
    annotations.
    """

    def __init__(
            self, name: str = None, description: str = None,
            entities: List[Entity] = [], corpora: List[Corpus] = [],
            annotators: List[Annotator] = [], documents: List[Document] = [],
            annotations: Iterable[Annotation] = [], **kwargs):
        self.name = name
        self.description = description
        self.entities = [Entity.factory(e) for e in entities]
        self.corpora = [Corpus.factory(c) for c in corpora]
        self.annotators = [Annotator.factory(a) for a in annotators]
        self._annotations = [Annotation.factory(a) for a in annotations]
        self._documents = [Document.factory(d) for d in documents]
        self.register()

    def __repr__(self):
        return str(self.id)

    @staticmethod
    def from_json(js):
        return Task(
            name=js['name'],
            description=js['description'],
            entities=[Entity(e) for e in js['entities']],
            corpora=[Corpus(c) for c in js['corpora']],
            annotators=[Annotator(a) for a in js['annotators']],
            task_id=js['id']
        )

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
            if doc_id in self._documents:
                self._documents[doc_id].annotations.append(annotation)
            else:
                # TODO: Investigate the reason for this
                pass

    def transform(self, target='binary', label=None):
        docs = []
        labels = []
        if target == 'binary':
            for doc in self.documents:
                if len(doc.annotations) > 0:
                    docs.append(doc.content)
                    labels.append(1 if label in doc.labels else 0)
            return docs, labels
        elif target == 'multilabel':
            entities = {e['id']: e['title'] for e in self.entities}
            for document in self.documents:
                if len(document.annotations) > 0:
                    docs.append(document.content)
                    labels.append({entities[l]: 1 for l in document.labels})
            return docs, labels
        else:
            # TODO: raise proper exception
            raise Exception('target should be `binary` or `multiclass`')

    def get_name(self, some_id):
        for a in self.annotators:
            if a.id == some_id:
                return a.name

        for e in self.entities:
            if e['id'] == some_id:
                return e['title']
        return some_id

    def get_id(self, name):
        for a in self.annotators:
            if a.name == name:
                return a.id

        for e in self.entities:
            if e['title'] == name:
                return e['id']
        return name
