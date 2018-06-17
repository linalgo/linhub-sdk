import json

from http.client import HTTPConnection, HTTPSConnection

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

    def __init__(self, client_id, client_secret, audience="annotate-api",
                 api_url="localhost:8000"):
        self.api_url = api_url
        self.audience = audience
        self.id = client_id
        self.secret = client_secret
        self.authenticate()

    def authenticate(self):
        conn = HTTPSConnection("linalgo.eu.auth0.com")
        headers = {'content-type': "application/json"}
        payload = json.dumps({
            'client_id': self.id,
            'client_secret': self.secret,
            'audience': self.audience,
            'grant_type': "client_credentials"
        })
        conn.request("POST", "/oauth/token", payload, headers)
        res = conn.getresponse()
        data = res.read()
        data = json.loads(data.decode("utf-8"))
        self.access_token = data['access_token']
        self.expires_in = data['expires_in']
        self.token_type = data['token_type']

    def request(self, url):
        conn = HTTPConnection(self.api_url)
        headers = {'authorization': f"Bearer {self.access_token}"}
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        data = res.read()
        return data

    def get_corpora(self):
        url = f"/corpora/"
        corpora = []
        res = json.loads(self.request(url))
        for js in res['results']:
            corpus_id = js['id']
            corpus = self.get_corpus(corpus_id)
            corpora.append(corpus)
        return corpora

    def get_corpus(self, corpus_id):
        url = f"/corpora/{corpus_id}/"
        res = json.loads(self.request(url))
        corpus = Corpus(name=res['name'], description=res['description'])
        documents = self.get_corpus_documents(corpus_id)
        corpus.documents = documents
        return corpus

    def get_corpus_documents(self, corpus_id):
        url = f"/corpora/{corpus_id}/documents/?page_size=100000"
        res = json.loads(self.request(url))
        documents = []
        for js in res['results']:
            document = json2doc(js)
            documents.append(document)
        return documents

    def get_tasks(self):
        url = "/tasks/"
        tasks = []
        res = json.loads(self.request(url))
        for js in res['results']:
            task_id = js['id']
            task = self.get_task(task_id)
            tasks.append(task)
        return tasks

    def get_task_documents(self, task_id):
        docs_url = f"/tasks/{task_id}/documents/?page_size=100000"
        docs_json = json.loads(self.request(docs_url))
        return [json2doc(doc_json) for doc_json in docs_json['results']]

    def get_task_annotations(self, task_id):
        annotations_url = f"/tasks/{task_id}/annotations/?page_size=100000"
        ann_json = json.loads(self.request(annotations_url))
        return [json2anno(a_json) for a_json in ann_json['results']]

    def get_task(self, task_id):
        task_url = f"/tasks/{task_id}/"
        task_json = json.loads(self.request(task_url))
        task = json2task(task_json)
        task.documents = self.get_task_documents(task_id)
        task.annotations = self.get_task_annotations(task_id)
        return task
