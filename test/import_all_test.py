import import_all
import os
import pathlib
import unittest


class PropertiesTest(import_all.ImportAllTest):
    CATCH_EXCEPTIONS = True
    PROJECT_PATHS = str(pathlib.Path(__file__).parent / 'edge' / 'edge')
    INCLUDE = 'edge.yes', 'edge.ok', 'edge.maybe'
    EXCLUDE = 'edge.no', 'edge.maybe', 'edge.sure'
    EXPECTED_TO_FAIL = 'edge.ok'


class EnvironmentVariablesTest(import_all.ImportAllTest):
    def __init__(self, *args, **kwds):
        old_env = dict(os.environ)
        os.environ.update(
            _IMPORT_ALL_CATCH_EXCEPTIONS=str(PropertiesTest.CATCH_EXCEPTIONS),
            _IMPORT_ALL_PROJECT_PATHS=str(PropertiesTest.PROJECT_PATHS),
            _IMPORT_ALL_INCLUDE=':'.join(PropertiesTest.INCLUDE),
            _IMPORT_ALL_EXCLUDE=':'.join(PropertiesTest.EXCLUDE),
            _IMPORT_ALL_EXPECTED_TO_FAIL=PropertiesTest.EXPECTED_TO_FAIL,
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


class SplitArgsTest(unittest.TestCase):
    def split(self, s):
        return import_all._split_args(s.split())

    def test_empty(self):
        paths, values = self.split('')
        self.assertEqual(paths, [])
        self.assertEqual(values, {})

    def test_simple(self):
        paths, values = self.split('foo bar')
        self.assertEqual(paths, ['foo', 'bar'])
        self.assertEqual(values, {})

    def test_flags(self):
        paths, values = self.split('foo --catch_exceptions bar --include=a:b')
        self.assertEqual(paths, ['foo', 'bar'])
        expected = {'CATCH_EXCEPTIONS': 'True', 'INCLUDE': 'a:b'}
        self.assertEqual(values, expected)

        _, values = self.split('foo --catch-exceptions bar --include=a:b')
        self.assertEqual(values, expected)

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.split('foo --catch-exception')
        with self.assertRaises(ValueError):
            self.split('foo --include')
