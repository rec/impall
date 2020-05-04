import impall
import pathlib


class PropertiesTest(impall.ImpAllTest):
    PATHS = str(pathlib.Path(__file__).parent / 'edge' / 'edge')
    INCLUDE = 'edge/yes', 'edge/ok', 'edge/maybe', 'edge/sub/*'
    EXCLUDE = 'edge/no', 'edge/maybe', 'edge/sure'
    FAILING = 'test/edge/edge/ok.py', 'test/edge/edge/sub/one.py'


class ImpAllSubdirectoriesTest(impall.ImpAllTest):
    MODULES = False
    PATHS = str(pathlib.Path(__file__).parent)
    FAILING = (
        'test/edge/edge/maybe.py',
        'test/edge/edge/no.py',
        'test/edge/edge/ok.py',
        'test/edge/edge/sub/one.py',
        'test/edge/edge/sub2/one.py',
        'test/edge/edge/sub2/sub',
        'test/edge/edge/sub2/sub/two.py',
    )
