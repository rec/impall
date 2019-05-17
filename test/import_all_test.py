import import_all
import pathlib


class ImportAllTest(import_all.TestCase):
    PROJECT_PATHS = str(pathlib.Path(__file__).parent / 'edge' / 'edge')
    INCLUDE = 'edge.yes', 'edge.ok', 'edge.maybe'
    EXCLUDE = 'edge.no', 'edge.maybe', 'edge.sure'
    EXPECTED_TO_FAIL = 'edge.ok'
