

from linalgo.client import LinalgoClient
import os


def example():

    linalgo_client = LinalgoClient(token="c4c0aa238d2f92ad63ddc923927d022561fe1886")

    tasks = linalgo_client.get_tasks()
    for task in tasks:
        print(f"id: {task.id}, name: {task.name}")


if __name__ == '__main__':
    example()
