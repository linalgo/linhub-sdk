import io
from enum import Enum
from contextlib import closing
import csv
import gzip
import requests

from .annotate import Annotation, Annotator, Corpus, Document, Task


def json2annotator(js):
    return Annotator(
        name=js['name'],
        annotator_id=js['id'],
        model=js['model']
    )


def json2annotation(js):
    return Annotation(
            entity_id=js['entity'],
            body=js['body'],
            annotator=js['annotator'],
            document_id=js['document'],
            task_id=js['task'],
            target=js['target'],
            created=js['created']
        )


def json2doc(js):
    return Document(
        uri=js['uri'],
        content=js['content'],
        corpus=js['corpus'],
        document_id=js['id']
    )


def json2task(js):
    return Task(
        name=js['name'],
        description=js['description'],
        entities=js['entities'],
        corpora=js['corpora'],
        annotators=js['annotators'],
        task_id=js['id']
    )


class AssignmentType(Enum):
    REVIEW = 'R'
    LABEL = 'A'


class AssignmentStatus(Enum):
    ASSIGNED = 'A'
    COMPLETED = 'C'


class LinalgoClient:

    endpoints = {
        'annotators': 'annotators',
        'annotations': 'annotations',
        'corpora': 'corpora',
        'documents': 'documents',
        'entities': 'entities',
        'task': 'tasks',
        'annotations-export': 'annotations/export',
        'documents-export': 'documents/export',
    }

    def __init__(self, token, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.access_token = token

    def request(self, url, query_params={}):
        headers = {'Authorization': f"Token {self.access_token}"}
        res = requests.get(url, headers=headers, params=query_params)
        if res.status_code == 401:
            raise Exception(f"Authentication failed. Please check your token.")
        if res.status_code == 404:
            raise Exception(f"{url} not found.")
        elif res.status_code != 200:
            raise Exception(f"Request returned status {res.status_code}")
        return res.json()

    def request_csv(self, url, query_params={}):
        headers = {'Authorization': f"Token {self.access_token}"}
        # stream the file
        with closing(requests.get(url, stream=True,  headers=headers,
                                  params=query_params)) as res:
            if res.status_code == 401:
                raise Exception(
                    f"Authentication failed. Please check your token.")
            if res.status_code == 404:
                raise Exception(f"{url} not found.")
            elif res.status_code != 200:
                raise Exception(
                    f"Request returned status {res.status_code}")
            with gzip.GzipFile(fileobj=io.BytesIO(res.content)) as f:
                records = list(csv.DictReader(io.TextIOWrapper(f, 'utf-8')))
            return records

    def get_corpora(self):
        res = self.request(self.endpoints['corpora'])
        corpora = []
        for js in res['results']:
            corpus_id = js['id']
            corpus = self.get_corpus(corpus_id)
            corpora.append(corpus)
        return corpora

    def get_corpus(self, corpus_id):
        url = f"{self.enpoints['corpora']}/{corpus_id}/"
        res = self.request(url)
        corpus = Corpus(name=res['name'], description=res['description'])
        documents = self.get_corpus_documents(corpus_id)
        corpus.documents = documents
        return corpus

    def get_corpus_documents(self, corpus_id):
        url = f"/corpora/{corpus_id}/documents/?page_size=1000"
        res = self.request(url)
        documents = []
        for js in res['results']:
            document = json2doc(js)
            documents.append(document)
        return documents

    def get_tasks(self, task_ids=[]):
        url = "tasks/"
        tasks = []
        res = self.request(url)
        if len(task_ids) == 0:
            for js in res['results']:
                task_ids.append(js['id'])
        for task_id in task_ids:
            task = self.get_task(task_id)
            tasks.extend(task)
        return tasks

    def get_task_documents(self, task_id):
        query_params = {'task_id': task_id, 'output_format': 'zip', 'only_documents': True}
        api_url = "{}/{}/".format(self.api_url, self.endpoints['documents-export'])
        records = self.request_csv(api_url, query_params)
        data = [json2doc(row) for row in records]
        return data

    def get_task_annotations(self, task_id):
        query_params = {'task_id': task_id, 'output_format': 'zip'}
        api_url = "{}/{}/".format(self.api_url, self.endpoints['annotations-export'])
        records = self.request_csv(api_url, query_params)
        data = [json2annotation(row) for row in records]
        return data

    def get_task(self, task_id, verbose=False):
        task_url = "{}/{}/{}/".format(
            self.api_url, self.endpoints['task'], task_id)
        if verbose:
            print(f'Retrivieving task with id {task_id}...')
        task_json = self.request(task_url)
        task = json2task(task_json)
        if verbose:
            print('Retrieving annotators...')
        task.annotators = self.get_annotators(task)
        if verbose:
            print('Retrieving entities...')
        params = {'tasks': task.id, 'page_size': 1000}
        entities_url = "{}/{}".format(self.api_url, self.endpoints['entities'])
        entities_json = self.request(entities_url, params)
        task.entities = entities_json['results']
        if verbose:
            print('Retrieving documents...')
        task.documents = self.get_task_documents(task_id)
        if verbose:
            print('Retrieving annotations...')
        task.annotations = self.get_task_annotations(task_id)
        return task

    def get_annotators(self, task=None):
        params = {'tasks': task.id, 'page_size': 1000}
        annotators_url = "{}/{}/".format(
            self.api_url, self.endpoints['annotators'])
        res = self.request(annotators_url, params)
        annotators = []
        for js in res['results']:
            annotator = json2annotator(js)
            annotators.append(annotator)
        return annotators

    def create_annotator(self, annotator):
        if annotator.annotator_id is not None:
            raise Exception("Annotator already has an ID.")
        annotator_url = "{}/{}/".format(
            self.api_url, self.endpoints['annotators'])
        url = self.api_url + annotator_url
        headers = { 'Authorization': f"Token {self.access_token}"}
        annotator_json = {
            'name': annotator.name,
            'model': str(annotator.model)
        }
        res = requests.post(url, json=annotator_json, headers=headers).json()
        annotator.annotator_id = res['id']
        annotator.owner = res['owner']
        return annotator

    def create_annotations(self, annotations):
        url = "{}/{}/".format(self.api_url, self.endpoints['annotations'])
        headers = {'Authorization': f"Token {self.access_token}"}
        res = requests.post(url, json=annotations, headers=headers)
        return res

    def assign(self, document, annotator, task, reviewee=None,
               assignment_type=AssignmentType.LABEL.value):
        doc_status = {
            'status': AssignmentStatus.ASSIGNED.value,
            'type': assignment_type,
            'document': document,
            'annotator': annotator,
            'task': task,
            'reviewee': reviewee
        }
        url = self.api_url + '/document-status/'
        headers = {'Authorization': f"Token {self.access_token}"}
        res = requests.post(url, doc_status, headers=headers)
        return res

    def unassign(self, status_id):
        headers = {'Authorization': f"Token {self.access_token}"}
        url = "{}/{}/{}/".format(self.api_url, '/document-status/', status_id)
        res = requests.delete(url, headers=headers)
        return res

    def get_schedule(self, task):
        query_params = {'task': task.id, 'page_size': 1000}
        docs = []
        next_url = "{}/{}/".format(self.api_url, '/document-status/')
        while next_url:
            res = self.request(next_url, query_params=query_params)
            next_url = res['next']
            docs.extend(res['results'])
        return docs
