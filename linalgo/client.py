import json

from http.client import HTTPConnection, HTTPSConnection


class LinalgoClient:

    def __init__(self, client_id, client_secret):
        self.id = client_id
        self.secret = client_secret

    def authenticate(self):
        conn = HTTPSConnection("linalgo.eu.auth0.com")
        headers = {'content-type': "application/json"}
        payload = json.dumps({
            'client_id': self.id,
            'client_secret': self.secret,
            'audience': "annotate-api",
            'grant_type': "client_credentials"
        })
        conn.request("POST", "/oauth/token", payload, headers)
        res = conn.getresponse()
        data = res.read()
        data = json.loads(data.decode("utf-8"))
        self.access_token = data['access_token']
        self.expires_in = data['expires_in']
        self.token_type = data['token_type']

    def get_tasks(self):
        conn = HTTPConnection("localhost:8000")
        headers = {'authorization': f"Bearer {self.access_token}"}
        conn.request("GET", "/tasks/4/documents/?page_size=100000", headers=headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
