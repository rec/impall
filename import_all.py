#!/usr/bin/env python3

"""
Individually and separately imports each Python module or file in a project and
reports warnings or failures at the end.

import_all.py can be run as a unit test or as a command line utility.

To run as a unit test, just inherit from the base class.

For example, put the following code anywhere in your test directories:

    import import_all

    class ImportAllTest(import_all.ImportAllTest):
        pass

(or copy [this file](https://github.com/rec/import_all/blob/master/all_test.py)
somewhere into your project).

Tests are customized by overriding one of the following properties in the
derived class:

    EXCLUDE, FAILING, INCLUDE, MODULES, PATHS,
    RAISE_EXCEPTIONS, and WARNINGS_ACTION.

For example, to turn warnings into errors, set the property
WARNINGS_ACTION in the derived class definition, like this:

    class ImportAllTest(import_all.ImportAllTest):
        WARNINGS_ACTION = 'error'

or if running as a command utility:

    $ import_all.py --warnings_action=error
    $ import_all.py -w error

The properties INCLUDE, EXCLUDE, and PROJECT_PATH can be
lists of strings, or a string separated with colons like
'foo.mod1:foo.mod2'

INCLUDE and EXCLUDE match modules, and also allow * as a wildcard.
A single * matches any module segment, and a double ** matches any
remaining segments. For example,

INCLUDE = 'foo', 'bar.*', 'baz.**'

* matches `foo` but not `foo.foo`
* matches `bar.foo` but not `bar` or `bar.foo.bar`
* matches `baz.foo` as well as `baz.foo.bar` but not `baz`

NOTE: to reduce side-effects, `sys.modules` is restored to its
original condition after each import, but there might be other
side-effects from loading some specific module.

Use the EXCLUDE property to exclude modules with undesirable side
effects. In general, it is probably a bad idea to have significant
side-effects just from loading a module.
"""

import argparse
import importlib
import inspect
import itertools
import os
import sys
import unittest
import warnings

__author__ = 'Tom Ritchford <tom@swirly.com>'
__version__ = '0.9.5'

EXCLUDE = """
A list of modules that will not be imported at all."""

FAILING = """
A list of modules that must fail.

This differs from EXCLUDE because modules in EXCLUDE aren't imported at
all, but failing modules must exist, are imported, and then must fail
when imported."""

INCLUDE = """
If non-empty, exactly the modules in the list will be loaded.
This is not recursive - you need to list each module you want to include."""

MODULES = """
If False, search all subdirectories.

If True, stop searching with subdirectories that do not contain an
__init__.py file.
"""

PATHS = """
A list of paths to search from.

If empty, guess the project paths from the current directory."""

RAISE_EXCEPTIONS = """
If True, stop importing at the first exception and print a stack trace.

If False, all exceptions will be caught and reported on at the end."""

WARNINGS_ACTION = """
Possible choices are: default, error, ignore, always, module, once

`warnings.simplefilter` is set to this value while testing: see
https://docs.python.org/3/library/warnings.html#the-warnings-filter
for more details."""


class ImportAllTest(unittest.TestCase):
    MODULES = False
    EXCLUDE = None
    FAILING = ()
    INCLUDE = None
    PATHS = None
    RAISE_EXCEPTIONS = False
    WARNINGS_ACTION = 'default'

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

        self._exc = _ModuleMatcher(self.EXCLUDE)
        self._inc = _ModuleMatcher(self.INCLUDE)

    def test_all(self):
        successes, failures = self.import_all()
        self.assertTrue(successes or failures)
        expected = sorted(_list(self.FAILING))
        for module, ex in failures:
            if module not in expected:
                print('Failed ' + module, ex, '', sep='\n')

        actual = sorted(m for m, ex in failures)
        self.assertEqual(actual, expected)

    def import_all(self):
        successes, failures = [], []
        paths = self.PATHS
        paths = _list(paths or self._guess_paths())

        warnings.simplefilter(self.WARNINGS_ACTION)
        try:
            for module in self._all_imports(paths):
                if self._accept(module):
                    self._import(module, successes, failures)
        finally:
            warnings.filters.pop(0)
        return successes, failures

    def _import(self, module, successes, failures):
        sys_modules = dict(sys.modules)
        try:
            importlib.invalidate_caches()
            importlib.import_module(module)
            successes.append(module)

        except Exception as e:
            if self.RAISE_EXCEPTIONS:
                raise
            failures.append((module, e))

        finally:
            sys.modules.clear()
            sys.modules.update(sys_modules)

    def _guess_paths(self):
        sourcefile = inspect.getsourcefile(self.__class__)
        path = _python_path(os.path.dirname(sourcefile))

        for c in os.listdir(path):
            if _is_python_dir(c):
                yield c

    def _all_imports(self, paths):
        for path in paths:
            root = _python_path(path)
            sys_path = sys.path[:]
            sys.path.insert(0, root)

            try:
                for directory, files in self._walk_code(path):
                    rel = os.path.relpath(directory, root)
                    module = '.'.join(_split_path(rel))
                    yield module

                    for f in files:
                        if f.endswith('.py') and not _is_ignored(f):
                            yield '%s.%s' % (module, f[:-3])
            finally:
                sys.path[:] = sys_path

    def _walk_code(self, path):
        """os.walk through subdirectories and files"""
        for directory, sub_dirs, files in os.walk(path):
            if self._accept_dir(directory):
                yield directory, files
            else:
                sub_dirs.clear()

    def _accept_dir(self, directory):
        if self.MODULES:
            return _is_python_dir(directory)
        return not _is_ignored(directory)

    def _accept(self, x):
        return (
            not _is_ignored(x)
            and not self._exc(x)
            and (not self._inc or self._inc(x))
        )

    def _convert_variable(self, name, value):
        default = getattr(ImportAllTest, name)
        if type(default) is str:
            return value

        if isinstance(default, bool):
            value = value.lower()
            if value.startswith('t'):
                return True
            if value.startswith('f'):
                return False
            raise ValueError

        # It's a tuple of strings
        assert type(default) in (type(None), tuple)
        if value.lower() == 'None':  # Special case for convenience
            return ()
        return value.split(ENV_SEPARATOR)


class _ModuleMatcher:
    """
    Match glob-like patterns like foo, bar.*, or baz.**
    """

    def __init__(self, patterns):
        self.parts_list = [p.split('.') for p in _list(patterns)]

    def __bool__(self):
        return bool(self.parts_list)

    def __call__(self, module):
        mparts = module.split('.')

        def match(parts):
            for part, mod in itertools.zip_longest(parts, mparts):
                if mod is None:
                    return False
                if part == '**':
                    return True
                if part != '*' and part != mod:
                    return False
            return True

        return any(match(p) for p in self.parts_list)


PROPERTIES = set(dir(ImportAllTest)) - set(dir(unittest.TestCase))
PROPERTIES = sorted(a for a in PROPERTIES if a.isupper())

ENV_SEPARATOR = ':'


def _is_ignored(path):
    b = os.path.basename(path)
    return b.startswith('.') or b.startswith('__')


def _is_python_dir(path):
    """Return True if `path` is a directory containing an __init__.py file"""
    init = os.path.join(path, '__init__.py')
    return os.path.exists(init) and not _is_ignored(path)


def _list(s):
    if not s:
        return []
    return s.split(':') if isinstance(s, str) else s


def _python_path(path):
    """
    Find the lowest directory in `path` and its parents that does not contain
    an __init__.py file
    """
    while _is_python_dir(path):
        path = os.path.dirname(path)

    return path


def _report():
    args = _parse_args()
    test_case = ImportAllTest()

    for attr, value in vars(args).items():
        if value:
            default = getattr(test_case, attr.upper())
            if isinstance(default, (list, tuple)):
                value = value.split(ENV_SEPARATOR)
            setattr(test_case, attr.upper(), value)

    successes, failures = test_case.import_all()
    if successes:
        print('Successes', *successes, sep='\n  ')
        print()

    if failures:
        failures = ['%s (%s)' % (m, e) for (m, e) in failures]
        print('Failures', *failures, sep='\n  ', file=sys.stderr)
        print(file=sys.stderr)


def _split_path(path):
    """Use os.path.split repeatedly to split a path into components"""
    old_path = None
    components = []

    while path != old_path:
        (path, tail), old_path = os.path.split(path), path
        tail and components.insert(0, tail)

    old_path and components.insert(0, old_path)
    return components


def _parse_args():
    parser = argparse.ArgumentParser(description=_USAGE)
    parser.add_argument('paths', nargs='*', default=[os.getcwd()])

    for prop in PROPERTIES:
        default = getattr(ImportAllTest, prop)

        if isinstance(default, bool):
            kwds = {'action': 'store_true'}
        else:
            if isinstance(default, (tuple, list)):
                default = ':'.join(default)
            kwds = {'default': default}

        help = globals()[prop]
        short, long = '-' + prop[0], '--' + prop
        parser.add_argument(short, long, help=help, **kwds)

    return parser.parse_args()


_USAGE = """
import_all.py [path ...path]

   Individually and separately imports each Python file found on or below these
   paths and reports on any failures.

   With no arguments, import_all imports all Python files found in
   any Python directory (i.e. with a __init__.py file) below the current
   directory.
"""


if __name__ == '__main__':
    _report()
