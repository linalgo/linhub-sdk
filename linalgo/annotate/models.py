from collections import defaultdict, MutableSequence
from typing import Dict, Iterable, List, Union
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
        unique_id = kwargs.get('unique_id', uuid.uuid4().hex)
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

    def setattr(self, name, value):
        if not hasattr(self, name):
            self.__setattr__(name, value)
            return True
        attr = self.__getattribute__(name)
        if attr is None:
            self.__setattr__(name, value)
            return True
        elif value is not None:
            self.__setattr__(name, value)
            return True
        return False


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


class AnnotationFactory:

    @staticmethod
    def from_dict(d: Dict):
        return Annotation(
            unique_id=d['id'],
            entity=Entity(unique_id=d['entity']),
            body=d['body'],
            annotator=Annotator(unique_id=d['annotator']),
            document=Document(unique_id=d['document']),
            task=Task(unique_id=d['task']),
            target=d['target'],
            created=d['created']
        )


class Annotation(RegistryMixin, FromIdFactoryMixin, AnnotationFactory):
    """
    Annotation class compatible with the W3C annotation data model.
    """

    def __init__(self, entity: 'Entity', document: 'Document', body: str = None,
                 annotator: 'Annotator' = None, task: 'Task' = None,
                 created=None, target: Target = None, score: float = None,
                 **kwargs):
        self.setattr('entity', Entity.factory(entity))
        self.setattr('score', score)
        self.setattr('body', body)
        self.setattr('task', Task.factory(task))
        self.setattr('annotator', Annotator.factory(annotator))
        self.setattr('document', Document.factory(document))
        self.document.add_annotation(self)
        self.setattr('target', target)
        self.setattr('created', created)
        self.register()

    def __repr__(self):
        return f'{self.id}::{self.entity.name}'


class AnnotationList(MutableSequence):
    """
    Class to list of annotations with custom indexing.
    """

    def __init__(self, annotations=None):
        super(AnnotationList, self).__init__()
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
        self._type_index[val.entity.id].append(val)


class AnnotatorFactory:

    @staticmethod
    def from_dict(js):
        return Annotator(
            unique_id=js['id'],
            name=js['name'],
            model=js['model']
        )


class Annotator(RegistryMixin, FromIdFactoryMixin, AnnotatorFactory):
    """
    The Annotator class can create, delete or modify Annotations.
    """

    def __init__(self, name: str = None, model=None, task: 'Task' = None,
                 annotation_type_id=None, threshold: float = 0, **kwargs):
        self.setattr('name', name)
        self.setattr('task', Task.factory(task))
        self.setattr('model', model)
        self.setattr('type_id', annotation_type_id)
        self.setattr('threshold', threshold)
        self.register()

    def __repr__(self):
        return self.name or self.id

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
            annotator=self.id,
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

    def __init__(self, name: str = None, description: str = None,
                 documents: Iterable['Document'] = [], **kwargs):
        self.setattr('name', name)
        self.setattr('description', description)
        self.setattr('documents', [Document.factory(d) for d in documents])
        self.register()

    def __repr__(self):
        return self.name or self.id


class DocumentFactory:

    @staticmethod
    def from_dict(d):
        return Document(
            uri=d['uri'],
            content=d['content'],
            corpus=Corpus(d['corpus']),
            document_id=d['id']
        )


class Document(RegistryMixin, FromIdFactoryMixin, DocumentFactory):
    """
    Base class that holds the document on which to perform annotations.
    """

    def __init__(self, content: str = None, uri: str = None,
                 corpus: Corpus = None, **kwargs):
        self.setattr('uri', uri)
        self.setattr('content', content)
        self.setattr('corpus', Corpus.factory(corpus))
        self._annotations = AnnotationList([])
        self.register()

    def __repr__(self):
        return self.id

    @property
    def labels(self):
        return set(annotation.type_id for annotation in self.annotations)

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, values):
        self._annotations = AnnotationList(values)

    def add_annotation(self, annotation: Annotation):
        for a in self.annotations:
            if annotation.id == a.id:
                return False
        self.annotations.append(annotation)
        return True


class Entity(RegistryMixin, FromIdFactoryMixin):

    def __init__(self, name: str = None, color: str = None, **kwargs):
        self.setattr('name', name or self.id)
        self.setattr('color', color)
        self.register()

    def __repr__(self):
        return self.name or str(self.id)


class TaskFactory:
    @staticmethod
    def from_dict(d):
        return Task(
            unique_id=d['id'],
            name=d['name'],
            description=d['description'],
            entities=[Entity(e) for e in d['entities']],
            corpora=[Corpus(c) for c in d['corpora']],
            annotators=[Annotator(a) for a in d['annotators']],
        )


class Task(RegistryMixin, FromIdFactoryMixin, TaskFactory):
    """
    The Task class contains all information about a task: entities, corpora, 
    annotations.
    """

    def __init__(
            self, name: str = None, description: str = None,
            entities: List[Entity] = [], corpora: List[Corpus] = [],
            annotators: List[Annotator] = [], documents: List[Document] = [],
            annotations: Iterable[Annotation] = [], **kwargs):
        self.setattr('name', name)
        self.setattr('description', description)
        self.setattr('entities', [Entity.factory(e) for e in entities])
        self.setattr('corpora', [Corpus.factory(c) for c in corpora])
        self.setattr('annotators', [Annotator.factory(a) for a in annotators])
        self._annotations = [Annotation.factory(a) for a in annotations]
        self._documents = [Document.factory(d) for d in documents]
        self.register()

    def __repr__(self):
        return str(self.id)

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
        self._annotations = AnnotationList(values)
        for annotation in self.annotations:
            doc_id = annotation.document.id
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
