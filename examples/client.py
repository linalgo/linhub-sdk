from linalgo.client import LinalgoClient


def main():

    token = "830889eb39fe9530f7268e256a1fa0fd8ce6a551"
    api_url = "http://localhost:8000"
    client = LinalgoClient(token=token, api_url=api_url)

    task = client.get_task(1)
    print(task)


if __name__ == '__main__':
    main()
