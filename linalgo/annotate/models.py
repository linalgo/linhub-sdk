from collections import defaultdict, MutableSequence
from typing import Iterable, List, Union
import uuid

from linalgo.annotate.bbox import BoundingBox, Vertex

Selector = Union[BoundingBox]


class Target:

    def __init__(self, source: 'Document' = None,
                 selectors: List[Selector] = []):
        self.source = source
        self.selectors = selectors


class Annotation:
    """
    Annotation class compatible with the W3C annotation data model.
    """

    def __init__(
            self, type: 'Entity', body: str, annotator: 'Annotator' = None,
            task: 'Task' = None, document: 'Document' = None, created=None,
            unique_id: str = None, target: Target = None,
            score: float = None):
        self.id = unique_id or uuid.uuid4()
        self.type_id = type
        self.score = score
        self.body = body
        self.task = task
        self.annotator = annotator
        self.document = document
        self.target = target
        self.created = created

    @staticmethod
    def from_json(js):
        return Annotation(
            unique_id=js['id'] or None,
            entity=Entity(unique_id=js['entity']),
            body=js['body'],
            annotator=Annotator(unique_id=js['annotator']),
            document=Document(unique_id=js['document']),
            task=Task(unique_id=js['task']),
            target=js['target'],
            created=js['created']
        )

    def to_json(self):
        js = {
            'id': str(self.id),
            'entity': self.entity.id,
            'body': self.body,
            'task': self.task.id,
            'annotator': self.annotator.id,
            'document': self.document.id,
            'target': self.target,
            'created': self.created
        }
        return js

    def __repr__(self):
        return str(self.to_json())


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


class Annotator:
    """
    The Annotator class can create, delete or modify Annotations.
    """

    def __init__(self, name: str, model=None, task: Task = None,
                 annotation_type_id=None, threshold: float = 0,
                 unique_id: str = None):
        self.id = unique_id or uuid.uuid4()
        self.name = name
        self.task = task
        self.model = model
        self.type_id = annotation_type_id
        self.threshold = threshold
        self.annotator_id = None

    @staticmethod
    def from_json(js):
        return Annotator(
            name=js['name'],
            annotator_id=js['id'],
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


class Corpus:

    def __init__(self, name: str, description: str,
                 documents: Iterable['Document'] = []):
        self.name = name
        self.description = description
        self.documents = documents


class Document:
    """
    Base class that holds the document on which to perform annotations.
    """

    def __init__(self, uri: str, content: str, corpus: Corpus = None,
                 document_id: str = None):
        self.uri = uri
        self.content = content
        self.corpus = corpus
        self.id = document_id
        self._annotations = Annotations([])

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


class Entity:

    def __init__(self, name: str, entity_id: str = None):
        self.id = entity_id
        self.name = name


class Task:
    """
    The Task class contains all information about a task: entities, corpora, 
    annotations.
    """

    def __init__(
            self, name: str = None, description: str = None,
            entities: List[Entity] = [], corpora: List[Corpus] = [],
            annotators: List[Annotator] = [], documents: List[Document] = [],
            annotations: Iterable[Annotation] = [], task_id: str = None):
        self.id = task_id or uuid.uuid4()
        self.name = name
        self.description = description
        self.entities = entities
        self.corpora = corpora
        self.annotators = annotators
        self._annotations = annotations
        self._documents = documents

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

    def __repr__(self):
        rep = (f"name: {self.name}\ndescription: {self.description}\n# "
               f"documents: {len(self.documents)}\n# annotations: "
               f"{len(self.annotations)}")
        if self.id:
            rep = f"id: {self.id}\n" + rep
        return rep
