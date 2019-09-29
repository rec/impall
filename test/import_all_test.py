import import_all
import os
import pathlib
import unittest


class PropertiesTest(import_all.ImportAllTest):
    PROJECT_PATHS = str(pathlib.Path(__file__).parent / 'edge' / 'edge')
    INCLUDE = 'edge.yes', 'edge.ok', 'edge.maybe', 'edge.sub.*'
    EXCLUDE = 'edge.no', 'edge.maybe', 'edge.sure'
    FAILING = 'edge.ok', 'edge.sub.one'


class EnvironmentVariablesTest(import_all.ImportAllTest):
    def __init__(self, *args, **kwds):
        old_env = dict(os.environ)
        os.environ.update(
            _IMPORT_ALL_RAISE_EXCEPTIONS=str(PropertiesTest.RAISE_EXCEPTIONS),
            _IMPORT_ALL_PROJECT_PATHS=str(PropertiesTest.PROJECT_PATHS),
            _IMPORT_ALL_INCLUDE=':'.join(PropertiesTest.INCLUDE),
            _IMPORT_ALL_EXCLUDE=':'.join(PropertiesTest.EXCLUDE),
            _IMPORT_ALL_FAILING=':'.join(PropertiesTest.FAILING),
        )
        try:
            super().__init__(*args, **kwds)
        finally:
            os.environ.clear()
            os.environ.update(old_env)


class ImportAllSubdirectoriesTest(import_all.ImportAllTest):
    ALL_SUBDIRECTORIES = True
    FAILING = (
        'test.edge.edge.maybe',
        'test.edge.edge.no',
        'test.edge.edge.ok',
        'test.edge.edge.sub.one',
        'test.edge.edge.sub2.one',
        'test.edge.edge.sub2.sub',
        'test.edge.edge.sub2.sub.two',
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
        paths, values = self.split('foo --raise_exceptions bar --include=a:b')
        self.assertEqual(paths, ['foo', 'bar'])
        expected = {'RAISE_EXCEPTIONS': 'True', 'INCLUDE': 'a:b'}
        self.assertEqual(values, expected)

        _, values = self.split('foo --raise-exceptions bar --include=a:b')
        self.assertEqual(values, expected)

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.split('foo --catch-exception')
        with self.assertRaises(ValueError):
            self.split('foo --include')


class ModMatcherTest(unittest.TestCase):
    def test_empty(self):
        matches = import_all._ModuleMatcher('')
        self.assertFalse(matches(''))
        self.assertFalse(matches('foo'))

    def test_simple(self):
        matches = import_all._ModuleMatcher('foo:bar.*:baz.**')
        self.assertTrue(matches('foo'))
        self.assertFalse(matches('foo.foo'))

        self.assertTrue(matches('bar.foo'))
        self.assertFalse(matches('bar'))
        self.assertFalse(matches('bar.foo.bar'))

        self.assertTrue(matches('baz.foo'))
        self.assertTrue(matches('baz.foo.baz'))
        self.assertFalse(matches('baz'))
