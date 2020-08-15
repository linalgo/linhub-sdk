import unittest
import uuid

from linalgo.annotate.models import Annotation


class TestModels(unittest.TestCase):

    def test_unique_id_mixin(self):
        a1 = Annotation(unique_id='a')
        a2 = Annotation(unique_id='a')
        b = Annotation()
        self.assertEqual(a1, a2)
        self.assertEqual(len(Annotation._registry), 2)



if __name__ == '__main__':
    unittest.main()
