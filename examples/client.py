from linalgo.hub.client import LinalgoClient


def main():

    token = "62112085f16b6dc656f5a64029c286255fd286f6"
    api_url = "http://localhost:8000/hub"
    client = LinalgoClient(token=token, api_url=api_url)

    task = client.get_task('c91e77a8-85f0-4cd3-98e9-b9f2df62f36c', verbose=True)
    print(task)


if __name__ == '__main__':
    main()
