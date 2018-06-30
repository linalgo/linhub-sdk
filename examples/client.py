

from linalgo.client import LinalgoClient
import os


def example():

    token = os.environ.get('ACCESS_TOKEN', None)

    if token is not None:
        c = LinalgoClient(token)
        c.authenticate()
        print(c.get_corpora())
        print(c.get_tasks())
    else:
        print("Please set access token!")


if __name__ == '__main__':
    example()
