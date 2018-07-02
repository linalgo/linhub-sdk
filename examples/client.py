

from linalgo.client import LinalgoClient
import os


def example():

    token = '3cc643ce21e0ffdecbaa6d3eae833726227378ff'
    if token is not None:
        c = LinalgoClient(token)
        c.authenticate()
        print(c.get_corpora())
        print(c.get_tasks())
    else:
        print("Please set access token!")


if __name__ == '__main__':
    example()
