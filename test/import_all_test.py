import import_all
import pathlib
import unittest


class PropertiesTest(import_all.ImportAllTest):
    MODULES = True
    PATHS = str(pathlib.Path(__file__).parent / 'edge' / 'edge')
    INCLUDE = 'edge.yes', 'edge.ok', 'edge.maybe', 'edge.sub.*'
    EXCLUDE = 'edge.no', 'edge.maybe', 'edge.sure'
    FAILING = 'edge.ok', 'edge.sub.one'


class ImportAllSubdirectoriesTest(import_all.ImportAllTest):
    FAILING = (
        'test.edge.edge.maybe',
        'test.edge.edge.no',
        'test.edge.edge.ok',
        'test.edge.edge.sub.one',
        'test.edge.edge.sub2.one',
        'test.edge.edge.sub2.sub',
        'test.edge.edge.sub2.sub.two',
    )


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
