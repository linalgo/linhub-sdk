from collections import defaultdict, MutableSequence
from mock.mock import self


class Annotation:
    """
    Annotation class compatible with the W3C annotation data model.
    """

    def __init__(self, uri, type_id, text, owner, task_id=None,
                 document_id=None, annotation_id=None):
        self.id = annotation_id
        self.uri = uri
        self.type_id = type_id
        self.text = text
        self.task_id = task_id
        self.owner = owner
        self.document_id = document_id

    def to_json(self):
        data = {
            "type_name": "UNKNOWN",
            "group": self.task_id,
            "target": [{
                "source": f"/tasks/{self.task_id}/annotate/{self.document_id}",
                "selector": [{
                    "conformsTo": "https://tools.ietf.org/html/rfc3236",
                    "type": "FragmentSelector",
                    "value": "annotate_append_area"
                }, {
                    "endContainer": "/anno-root[1]/anno-layout[1]/main[1]/mat-sidenav-container[1]/mat-sidenav-content[1]/div[1]/anno-task-annotation[1]/anno-task-document[1]/div[1]/mat-card[1]/mat-card-content[1]/pre[1]/p[1]",
                    "endOffset": 3,
                    "type": "RangeSelector",
                    "startOffset": 0,
                    "startContainer": "/anno-root[1]/anno-layout[1]/main[1]/mat-sidenav-container[1]/mat-sidenav-content[1]/div[1]/anno-task-annotation[1]/anno-task-document[1]/div[1]/mat-card[1]/mat-card-content[1]/pre[1]/p[1]"
                }]
            }],
            "type_id": self.type_id,
            "text": "",
            "created": "2018-05-16T02:00:40.854Z",
            "display_options": {},
            "uri": f"/tasks/{self.task_id}/annotate/{self.document_id}",
            "tags": [],
            "user": f"acct:{self.name}@linalgo",
            "permissions": {
                "read": [f"acct:{self.name}@linalgo"],
                "update": [f"acct:{self.name}@linalgo"],
                "delete": [f"acct:{self.name}@linalgo"]
            },
            "id": 1,
            "type_action": "showType",
            "type_flashcard_type": "default"
        }
        js = {
            'uri': self.uri,
            'type_id': self.type_id,
            'text': self.text,
            'group': self.task_id,
            'owner_id': self.owner,
            'document_id': self.document_id,
            'data': data
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
        self._user_index[val.owner].append(val)
        self._type_index[val.type_id].append(val)


class Annotator:
    """
    The Annotator class can create, delete or modify Annotations.
    """

    def __init__(self, name, task=None, model=None, annotation_type_id=None,
                 threshold=0.5):
        self.name = name
        self.task = task
        self.model = model
        self.type_id = annotation_type_id
        self.threshold = threshold

    def assign_task(self, task):
        self.task = task

    def _get_annotation(self, document):
        prob = self.model.decision_function([document.content])[0]
        print(prob)
        if prob >= self.threshold:
            label = self.type_id
            annotation = Annotation(
                uri='',
                type_id=label,
                text=document.content,
                owner=self.name,
                task_id=self.task.id,
                document_id=document.id
            )
            return annotation
        else:
            return None

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

    def __init__(self, name, content, corpus=None, metadata=None,
                 document_id=None):
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
