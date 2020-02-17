import numpy as np

from django.utils.dateparse import parse_datetime


from .client import AssignmentStatus


class AnnotatorNotFound(Exception):
    pass


class NotEnoughReviews(Exception):
    pass


class Scheduler:

    def __init__(self, task, schedule):
        self.task = task
        self.schedule = schedule
        self.schedule['timestamp'] = schedule['timestamp'].apply(parse_datetime)

    def unseen_documents(self, n):
        """
        Parameters
        ----------

        n: int
            Number of unseen documents to return
        """
        annotated_docs = set(
            annotation.to_json()['document'] for annotation in self.task.annotations)
        docs = set(doc.id for doc in self.task.documents)
        new_docs = list(docs - annotated_docs)

        if len(new_docs) < n:
            raise NotEnoughReviews()

        return set(np.random.choice(new_docs, size=n, replace=False))

    def random_review(self, reviewer_id, reviewee_id, n=None, start_date=None,
                      end_date=None):
        """
        Parameters
        ----------
        reviewer_id: uuid
            The uuid of the reviewer
        reviewee_id: uuid
            The uuid of the reviewee
        n: int
            The number of documents to review
        start_date:
            Filter reviewee annotations after `start_date`
        end_date:
            Filters reviewee annotations after `end_date`

        Return
        ------
        A set of documents to review
        """
        schedule = self.schedule
        if start_date is not None:
            idx = (schedule['annotator'] == reviewee_id) & schedule['timestamp']
            schedule = schedule[idx]
        if end_date is not None:
            idx = (schedule['annotator'] == reviewee_id) & schedule['timestamp']
            schedule = schedule[idx]
        if (reviewer_id not in {a.id for a in self.task.annotators} or
            reviewee_id not in {a.id for a in self.task.annotators}):
            raise AnnotatorNotFound()
        reviewer_idx = schedule['annotator'] == reviewer_id
        reviewee_idx = schedule['annotator'] == reviewee_id
        seen_idx = schedule['status'] == AssignmentStatus.COMPLETED.value
        pending_idx = schedule['status'] == AssignmentStatus.ASSIGNED.value

        idx = reviewer_idx & (seen_idx | pending_idx)
        reviewer_docs = set(schedule.loc[idx, 'document'])
        idx = reviewee_idx & seen_idx
        reviewee_docs = set(schedule.loc[idx, 'document'])

        pool = list(reviewee_docs - reviewer_docs)
        if n is not None:
            if n > len(pool):
                print(pool)
                raise NotEnoughReviews()
            return set(np.random.choice(pool, size=n, replace=False))
        return pool

    def random_assign(self, assignee_id, n):
        """

        Parameters
        ----------

        assignee_id: uuid
            The uuid of the annotator
        n: int
            the number of documents

        Return
        ------
        A set of documents to assign
        """

        if assignee_id not in {a.id for a in self.task.annotators}:
            raise AnnotatorNotFound(
                '{} is not a known annotator'.format(assignee_id))

        all_docs = set(doc.id for doc in self.task.documents)
        all_seen_docs = set()
        for annotation in self.task.annotations:
            all_seen_docs.add(annotation.to_json()['document'])
        all_new_docs = all_docs - all_seen_docs

        assignee_idx = self.schedule['annotator'] == assignee_id
        seen_idx = self.schedule['status'] == AssignmentStatus.COMPLETED.value
        pending_idx = self.schedule['status'] == AssignmentStatus.ASSIGNED.value

        idx = assignee_idx & (seen_idx | pending_idx)
        assignee_docs = set(self.schedule.loc[idx, 'document'])

        pool = list(all_new_docs - assignee_docs)
        if n > len(pool):
            print(pool)
            raise NotEnoughReviews()
        return set(np.random.choice(pool, size=n, replace=False))

