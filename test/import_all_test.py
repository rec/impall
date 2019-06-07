import import_all
import os
import pathlib


class ImportAllTest(import_all.ImportAllTest):
    CATCH_EXCEPTIONS = True
    PROJECT_PATHS = str(pathlib.Path(__file__).parent / 'edge' / 'edge')
    INCLUDE = 'edge.yes', 'edge.ok', 'edge.maybe'
    EXCLUDE = 'edge.no', 'edge.maybe', 'edge.sure'
    EXPECTED_TO_FAIL = 'edge.ok'


class ImportAllEnvironmentTest(import_all.ImportAllTest):
    def __init__(self, *args, **kwds):
        old_env = dict(os.environ)
        os.environ.update(
            _IMPORT_ALL_CATCH_EXCEPTIONS=str(ImportAllTest.CATCH_EXCEPTIONS),
            _IMPORT_ALL_PROJECT_PATHS=str(ImportAllTest.PROJECT_PATHS),
            _IMPORT_ALL_INCLUDE=':'.join(ImportAllTest.INCLUDE),
            _IMPORT_ALL_EXCLUDE=':'.join(ImportAllTest.EXCLUDE),
            _IMPORT_ALL_EXPECTED_TO_FAIL=ImportAllTest.EXPECTED_TO_FAIL,
        )
        try:
            super().__init__(*args, **kwds)
        finally:
            os.environ.clear()
            os.environ.update(old_env)


class ImportAllSubdirectoriesTest(import_all.ImportAllTest):
    CATCH_EXCEPTIONS = True
    ALL_SUBDIRECTORIES = True
    EXPECTED_TO_FAIL = (
        'test.edge.edge.maybe',
        'test.edge.edge.no',
        'test.edge.edge.ok',
    )
