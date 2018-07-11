import json
import requests

from .annotate import Annotation, Corpus, Document, Task


def json2anno(js):
    return Annotation(
            uri=js['uri'],
            type_id=js['type'],
            text=js['text'],
            owner=js['owner'],
            document_id=js['document'],
            task_id=js['group']
        )


def json2doc(js):
    return Document(
        name=js['uri'],
        content=js['content'],
        corpus=js['corpus'],
        metadata=js['metadata'],
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

    def __init__(self, token, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.access_token = token

    def request(self, url, data=None):
        url = self.api_url + url
        headers = {'Authorization': f"Token {self.access_token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 401:
            raise Exception(f"Authentication failed. Please check your token.")
        if res.status_code == 404:
            raise Exception(f"{url} not found.")
        elif res.status_code != 200:
            raise Exception(f"Request returned status {res.status_code}")
        return res.json()

    def get_corpora(self):
        url = f"/corpora/"
        corpora = []
        res = self.request(url)
        for js in res['results']:
            corpus_id = js['id']
            corpus = self.get_corpus(corpus_id)
            corpora.append(corpus)
        return corpora

    def get_corpus(self, corpus_id):
        url = f"/corpora/{corpus_id}/"
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
        url = "/tasks/"
        tasks = []
        res = self.request(url)
        if task_ids == []:
            for js in res['results']:
                task_ids.append(js['id'])
        for task_id in task_ids:
            task = self.get_task(task_id)
            tasks.append(task)
        return tasks

    def get_task_documents(self, task_id):
        docs_url = f"/tasks/{task_id}/documents/?page_size=100000"
        docs_json = self.request(docs_url)
        return [json2doc(doc_json) for doc_json in docs_json['results']]

    def get_task_annotations(self, task_id):
        annotations_url = f"/tasks/{task_id}/annotations/?page_size=100000"
        ann_json = self.request(annotations_url)
        return [json2anno(a_json) for a_json in ann_json['results']]

    def get_task(self, task_id):
        task_url = f"/tasks/{task_id}/"
        task_json = self.request(task_url)
        task = json2task(task_json)
        task.documents = self.get_task_documents(task_id)
        task.annotations = self.get_task_annotations(task_id)
        return task

    def upload(self, annotations):
        url = '/annotations/'
        url = self.api_url + url
        headers = {'Authorization': f"Token {self.access_token}"}
        res = requests.post(url, json=annotations, headers=headers)
        print(res)
