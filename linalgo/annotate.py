from collections import defaultdict, MutableSequence
import uuid


class Annotation:
    """
    Annotation class compatible with the W3C annotation data model.
    """

    def __init__(self, entity_id, body, annotator=None, task_id=None,
                 score=None, document_id=None, annotation_id=None,
                 target={}, created=None):
        self.id = annotation_id
        if self.id is None:
            self.id = uuid.uuid4()
        self.type_id = entity_id
        self.score = score
        self.body = body
        self.task_id = task_id
        self.annotator = annotator
        self.document_id = document_id
        self.target = target
        self.created = created

    def to_json(self):
        js = {
            'id': str(self.id),
            'entity': self.type_id,
            # 'uri': self.uri,
            'type': self.type_id,
            # 'text': self.text,
            'task': self.task_id,
            'annotator': self.annotator,
            'document': self.document_id,
            'target': self.target,
            }
        return js

    def __repr__(self):
        return str(self.type_id)


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

    def __init__(self, name, task=None, model=None, annotation_type_id=None,
                 threshold=0, annotator_id=None):
        self.id = annotator_id
        self.name = name
        self.task = task
        self.model = model
        self.type_id = annotation_type_id
        self.threshold = threshold
        self.annotator_id = None

    def assign_task(self, task):
        self.task = task

    def _get_annotation(self, document):
        score = self.model.decision_function([document.content])[0]
        if score >= self.threshold:
            label = self.type_id
        else:
            label = 1  # Viewed
        annotation = Annotation(
            uri=f'/tasks/{self.task.id}/annotate/{document.id}',
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

    def __init__(self, name, description, documents=[]):
        self.name = name
        self.description = description
        self.documents = documents


class Document:
    """
    Base class that holds the document on which to perform annotations.
    """

    def __init__(self, uri, content, corpus=None, document_id=None):
        self.uri = uri
        self.content = content
        self.corpus = corpus
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


class Entity:

    def __initi__(self, name, entity_id=None):
        self.id = entity_id
        self.name = name


class Task:
    """
    The Task class contains all information about a task: entities, corpora, 
    annotations.
    """

    def __init__(self, name, description, entities=None, corpora=None,
                 annotators=None, annotations=Annotations([]), documents=[],
                 task_id=None):
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
