#!/usr/bin/env python3

import importlib
import inspect
import os
import re
import sys
import unittest
import warnings

__author__ = 'Tom Ritchford <tom@swirly.com>'
__version__ = '0.9.2'

""" A unit test that imports every module in a Python repository.

    It prints all errors and warnings then fails, if there are any.
    Otherwise prints nothing and suceeds.
"""

ENV_PREFIX = '_IMPORT_ALL_'
ENV_SEPARATOR = ':'

""" ENV_PREFIX is used when setting test attributes using environment
    variables.  This is convenient for temporarily turning features on or
    off while debugging.

    For example, to turn off catch exceptions, set the environment variable
    _IMPORT_ALL_CATCH_EXCEPTIONS=False

    To set a boolean test attribute, use a string starting with t or T for
    True, or a string starting with f or F for False; any other string gives
    an error.

    To set a test attribute that's a list of strings, separate those strings
    with a colon (ENV_SEPARATOR) - for example:

    _IMPORT_ALL_EXCLUDE=my_project.broken:my_project.exper
"""


class TestCase(unittest.TestCase):
    """ Import every Python module or file and fail on errors or warnings
    """

    ALL_SUBDIRECTORIES = False
    """ If True, search all subdirectories.

        If False, stop searching with subdirectories that do not contain
        an __init__.py file.
    """

    PROJECT_PATHS = None
    """ A list or tuple of path roots that will be recusively loaded.

        If empty, guess PROJECT_PATHS from the root Python directory
        that contains the definition of the class.
    """

    WARNINGS_ACTION = 'error'
    """ What to do if a Python warning occurs.

        `warnings.simplefilter` is be set to this value while testing: see
        https://docs.python.org/3/library/warnings.html#the-warnings-filter
        for more details.
    """

    CATCH_EXCEPTIONS = True
    """ If True, catch all exceptions and report them at the end.

        Otherwise, the first exception will stop the program with a stack trace
    """

    SKIP_PREFIXES = '__', '.'
    """ Any directory which starts with any prefix in SKIP_PREFIXES and its
        subdirectories are ignored.
    """

    INCLUDE = None
    """ A list or tuple of regular expressions, or None.

        If non-empty, only modules whose full pathname matches one of these
        regular expressions will be imported.
    """

    EXCLUDE = None
    """ A list or tuple of regular expressions, or None.

        If non-empty, modules whose name matches any of these regular
        expressions will not be imported.
    """

    EXPECTED_TO_FAIL = ()
    """ A list of specific module names that are expected to fail.

        This differs from EXCLUDE because those modules aren't imported at all,
        but the modules in EXPECTED_TO_FAIL must exist, are imported, and then
        must fail when imported.
    """

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._inc = [re.compile(i) for i in _list(self.INCLUDE)]
        self._exc = [re.compile(i) for i in _list(self.EXCLUDE)]

    def test_all(self):
        successes, failures = self.import_all()
        self.assertTrue(successes or failures)
        expected = sorted(_list(self.EXPECTED_TO_FAIL))
        for module, ex in failures:
            if module not in expected:
                print('Failed ' + module, ex, '', sep='\n')

        actual = sorted(m for m, ex in failures)
        self.assertEqual(actual, expected)

    def import_all(self):
        successes, failures = [], []
        paths = _list(self.PROJECT_PATHS or self._guess_paths())

        warnings.simplefilter(self.WARNINGS_ACTION)
        try:
            for module in self._all_imports(paths):
                if self._accept(module):
                    sys_modules = dict(sys.modules)
                    try:
                        importlib.invalidate_caches()
                        importlib.import_module(module)
                        successes.append(module)
                    except Exception as e:
                        if not self.CATCH_EXCEPTIONS:
                            raise
                        failures.append((module, e))
                    sys.modules.clear()
                    sys.modules.update(sys_modules)
        finally:
            warnings.filters.pop(0)
        return successes, failures

    def _guess_paths(self):
        sourcefile = inspect.getsourcefile(__class__)
        path = python_path(os.path.dirname(sourcefile))

        for c in os.listdir(path):
            if has_init_file(c) and not c.startswith('__'):
                yield c

    def _all_imports(self, paths):
        for path in paths:
            root = python_path(path)
            sys_path = sys.path[:]
            sys.path.insert(0, root)

            try:
                for directory, files in self._walk_code(path):
                    rel = os.path.relpath(directory, root)
                    module = '.'.join(split_all(rel))
                    yield module

                    for f in files:
                        if f.endswith('.py') and not f.startswith('__'):
                            yield '%s.%s' % (module, f[:-3])
            finally:
                sys.path[:] = sys_path

    def _walk_code(self, path):
        """
        os.walk through subdirectories and files, ignoring any that begin
        with any of the strings in `skip_prefixes`
        """
        for directory, sub_dirs, files in os.walk(path):
            if any(directory.startswith(p) for p in self.SKIP_PREFIXES) or (
                not self.ALL_SUBDIRECTORIES
                and directory != path
                and not has_init_file(directory)
            ):
                sub_dirs.clear()
            else:
                yield directory, files

    def _accept(self, x):
        return (
            not x.startswith('.')
            and not any(i.match(x) for i in self._exc)
            and (not self._inc or any(i.match(x) for i in self._inc))
        )

    def _read_env_variables(self):
        for i in set(dir(TestCase)) - set(dir(unittest.TestCase)):
            if not i.isupper() or i.startwith('_'):
                continue

            name = ENV_PREFIX + i
            value = os.environ.get(name)
            if not value:
                continue

            try:
                cvalue = self._convert_variable(name, value)
            except Exception:
                err = 'Cannot understand env var %s="%s"' % (name, value)
                raise ValueError(err)

            setattr(self, name, cvalue)

    def _convert_variable(self, name, value):
        default = getattr(TestCase, name)
        if type(default) is str:
            return value

        # This is hacky and might need to change if more
        # configuration variables are added.
        if isinstance(default, bool):
            value = value.lower()
            if value.startswith('t'):
                return True
            if value.startswith('f'):
                return False
            raise ValueError

        # It's a tuple of strings, split by :s
        assert type(default) in (type(None), tuple)
        if value.lower() == 'None':
            return None
        return value.split(ENV_SEPARATOR)


def split_all(path):
    """Use os.path.split repeatedly to split a path into components"""
    old_path = None
    components = []

    while path != old_path:
        (path, tail), old_path = os.path.split(path), path
        tail and components.insert(0, tail)

    old_path and components.insert(0, old_path)
    return components


def python_path(path):
    """
    Find the lowest directory in `path` and its parents that does not contain
    an __init__.py file
    """
    while has_init_file(path):
        path = os.path.dirname(path)

    return path


def has_init_file(path):
    """Return True if `path` is a directory containing an __init__.py file"""
    return os.path.exists(os.path.join(path, '__init__.py'))


def _list(s):
    return [s] if isinstance(s, str) else s or []


def report(args, file=sys.stdout):
    test_case = TestCase()
    test_case.PROJECT_PATHS = args
    successes, failures = test_case.import_all()
    if successes:
        print('Successes', *successes, sep='\n  ', file=file)
        print(file=file)

    if failures:
        failures = ['%s (%s)' % (m, e) for (m, e) in failures]
        print('Failures', *failures, sep='\n  ', file=file)
        print(file=file)


if __name__ == '__main__':
    args = sys.argv[1:] or [os.getcwd()]
    report(args)
