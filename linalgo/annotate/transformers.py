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

    def transform(self, task: Task, strategy='latest', ignore=[]):
        if strategy != 'latest':
            raise NotImplementedError(f'{strategy} is not a valid strategy.')
        texts, labels = [], []
        for doc in task.documents:
            aa = [a for a in doc.annotations if a.task == task]
            aa = [a for a in aa if a.entity not in ignore]
            if len(aa) > 0:
                annotations = sorted(aa, key=lambda a: a.created, reverse=True)
                texts.append(doc.content)
                labels.append(annotations[0].entity.name)
        return texts, labels


class MultiLabelTransformer:

    def transform(self, task: Task, strategy='keep-all'):
        if strategy not in ('keep-all', 'keep-last-by-annotator'):
            raise NotImplementedError(f'{strategy} is not a valid strategy.')
        texts, labels = [], []
        for doc in task.documents:
            if len(doc.annotations) > 0:
                texts.append(doc.content)
                if strategy == 'keep-last-by-annotator':
                    d = {}
                    for a in doc.annotations:
                        try:
                            if d[a.annotator.id].created > a.created:
                                d[a.annotator.id] = a
                        except:
                            d[a.annotator.id] = a
                    labels.append({v.entity.name for k, v in d.items()})
                elif strategy == 'keep-all':
                    labels.append({e.name for e in doc.entities})
        return texts, labels
