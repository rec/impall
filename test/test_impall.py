import impall
import pathlib
import unittest


class PropertiesTest(impall.ImpAllTest):
    PATHS = str(pathlib.Path(__file__).parent / 'edge' / 'edge')
    INCLUDE = 'edge.yes', 'edge.ok', 'edge.maybe', 'edge.sub.*'
    EXCLUDE = 'edge.no', 'edge.maybe', 'edge.sure'
    FAILING = 'edge.ok', 'edge.sub.one'


class ImpAllSubdirectoriesTest(impall.ImpAllTest):
    MODULES = False
    PATHS = str(pathlib.Path(__file__).parent)
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
        matches = impall._ModuleMatcher('')
        self.assertFalse(matches(''))
        self.assertFalse(matches('foo'))

    def test_simple(self):
        matches = impall._ModuleMatcher('foo:bar.*:baz.**')
        self.assertTrue(matches('foo'))
        self.assertFalse(matches('foo.foo'))

        self.assertTrue(matches('bar.foo'))
        self.assertFalse(matches('bar'))
        self.assertFalse(matches('bar.foo.bar'))

        self.assertTrue(matches('baz.foo'))
        self.assertTrue(matches('baz.foo.baz'))
        self.assertFalse(matches('baz'))
