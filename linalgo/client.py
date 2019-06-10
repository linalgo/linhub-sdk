import requests

from .annotate import Annotation, Annotator, Corpus, Document, Task


def json2annotator(js):
    return Annotator(
        name=js['name'],
        annotator_id=js['id']
    )


def json2annotation(js):
    return Annotation(
            entity_id=js['entity'],
            body=js['body'],
            annotator=js['annotator'],
            document_id=js['document'],
            task_id=js['task'],
        )


def json2doc(js):
    return Document(
        name=js['uri'],
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


class LinalgoClient:

    endpoints = {
        'annotators': 'annotators/',
        'corpora': 'corpora/',
        'documents': 'documents/',
        'entities': 'entities/',
        'task': 'tasks/',
    }

    def __init__(self, token, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.access_token = token

    def request(self, endpoint, query_params={}):
        url = '/'.join([self.api_url, endpoint])
        headers = {'Authorization': f"Token {self.access_token}"}
        res = requests.get(url, headers=headers, params=query_params)
        if res.status_code == 401:
            raise Exception(f"Authentication failed. Please check your token.")
        if res.status_code == 404:
            raise Exception(f"{url} not found.")
        elif res.status_code != 200:
            raise Exception(f"Request returned status {res.status_code}")
        return res.json()

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
        url = f"/corpora/{corpus_id}/documents/?page_size=100000"
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
            tasks.append(task)
        return tasks

    def get_task_documents(self, task_id):
        query_params = {'corpus__tasks': task_id, 'page_size': 100000}
        docs_json = self.request(self.endpoints['documents'], query_params)
        return [json2doc(doc_json) for doc_json in docs_json['results']]

    def get_task_annotations(self, task_id):
        annotations_url = f"annotations/"
        query_params = {'task': task_id, 'page_size': 100000}
        ann_json = self.request(annotations_url, query_params)
        return [json2annotation(a_json) for a_json in ann_json['results']]

    def get_task(self, task_id, verbose=False):
        task_url = f"tasks/{task_id}/"
        if verbose:
            print(f'Retrivieving task with id {task_id}...')
        task_json = self.request(task_url)
        task = json2task(task_json)
        if verbose:
            print('Retrieving entities...')
        params = {'tasks': task.id, 'page_size': 100000}
        entities_json = self.request(self.endpoints['entities'], params)
        task.entities = entities_json['results']
        if verbose:
            print('Retrieving documents...')
        task.documents = self.get_task_documents(task_id)
        if verbose:
            print('Retrieving annotations...')
        task.annotations = self.get_task_annotations(task_id)
        return task

    def get_annotators(self):
        annotators_url = f"annotators/"
        res = self.request(annotators_url)
        annotators = []
        for js in res['result']:
            annotator = json2annotator(js)
            annotators.append(annotator)
        return annotators

    def create_annotator(self, annotator):
        if annotator.annotator_id is not None:
            raise Exception("Annotator already has an ID.")
        annotator_url = f"/annotators/"
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
        url = 'annotations/'
        url = self.api_url + url
        headers = {'Authorization': f"Token {self.access_token}"}
        res = requests.post(url, json=annotations, headers=headers)
        return res
