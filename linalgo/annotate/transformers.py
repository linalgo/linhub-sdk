from typing import List, Union

from .models import Entity, Task


class BinaryTransformer:

    def __init__(self, pos_labels: List[Entity]):
        self.positive = pos_labels

    def transform(self, task: Task):
        texts, labels = [], []
        for doc in task.documents:
            if len(doc.annotations) > 0:
                texts.append(doc.content)
                labels.append(max(l in doc.entities for l in self.positive))
        return texts, labels


class MultiClassTransformer:

    def transform(self, task: Task):
        texts, labels = [], []
        for doc in task.documents:
            if len(doc.annotations) > 0:
                texts.append(doc.content)
                labels.append(doc.annotations[0].entity.id)
        return texts, labels


class MultiLabelTransformer:

    def transform(self, task: Task):
        texts, labels = [], []
        for doc in task.documents:
            if len(doc.annotations) > 0:
                texts.append(doc.content)
                labels.append({e.id: 1 for e in doc.entities})
        return texts, labels
