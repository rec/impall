import os, unittest
from import_all import import_all

BASE = os.path.dirname(os.path.dirname(__file__))


class ImportAllTest(unittest.TestCase):
    def test_all(self):
        assert import_all
