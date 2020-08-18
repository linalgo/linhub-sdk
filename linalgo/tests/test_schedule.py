import os, unittest

import pandas as pd


from linalgo.hub.client import LinalgoClient
from linalgo.hub.scheduler import Scheduler


class TestSchedule(unittest.TestCase):

    def test_random_review(self):
        token = os.getenv('LINHUB_TOKEN')
        client = LinalgoClient(
            token=token, api_url='https://api.linalgo.com/hub')
        task_id = '20c436de-f4d1-4b40-b9e9-ee2fb9087ea9'
        task = client.get_task(task_id, verbose=True)
        schedule = pd.DataFrame(client.get_schedule(task))
        scheduler = Scheduler(task, schedule)
        docs = scheduler.random_review(
            task.get_id('precious.figueroa'), task.get_id('wallie'), n=20)


if __name__ == '__main__':
    unittest.main()
