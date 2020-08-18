import unittest

from linalgo.annotate.models import Annotation
from .fixtures import ANNOTATIONS


class TestModels(unittest.TestCase):

    def test_unique_id_mixin(self):
        fixture = ANNOTATIONS[0]
        a1 = Annotation(
            unique_id=fixture['id'],
            entity=fixture['entity'],
            document=fixture['document']
        )
        a2 = Annotation(
            unique_id=fixture['id'],
            entity=fixture['entity'],
            document=fixture['document']
        )
        self.assertEqual(a1, a2)
        self.assertEqual(len(Annotation._registry), 1)

    def test_create_annotation_from_dict(self):
        fixture = ANNOTATIONS[0]
        a = Annotation.from_dict(fixture)
        self.assertEqual(fixture['document'], a.document.id)

    def test_override_annotation(self):
        fixture = ANNOTATIONS[0]
        a1 = Annotation(
            unique_id=fixture['id'],
            entity=fixture['entity'],
            document=fixture['document']
        )
        a2 = Annotation.from_dict(fixture)
        self.assertEqual(a1, a2)


if __name__ == '__main__':
    unittest.main()
