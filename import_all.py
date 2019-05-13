import contextlib
import importlib
import inspect
import os
import re
import sys
import unittest
import warnings

__author__ = 'Tom Ritchford <tom@swirly.com>'
__version__ = '0.9.2'


"""
    A unit test that imports every module in a Python repository,
    treating warnings as errors by default.
"""


class TestCase(unittest.TestCase):
    """The base test, which imports every Python module in a directory"""

    WARNINGS_ACTION = 'error'
    """What action to take if a Python warning occurs.

       `warnings.simplefilter` will be set to this value while testing
    """

    PROJECT_PATHS = ()
    """A sequence of path roots that will be recusively loaded.

       If empty, guess the project paths from the root Python directory
       that containsthe definition of the class.
    """

    INCLUDE = None
    """A list or tuple of regular expressions, or None.

       If non-None, only modules whose full pathname matches one of these
       regular expressions will be imported. (This means that setting
       INCLUDE = () will effectively disable this test.)
    """

    EXCLUDE = None
    """A list or tuple of regular expressions, or None.

       If non-empty, modules whose name matches any of these regular
       expressions will not be imported.
    """

    EXPECTED_TO_FAIL = ()
    """A list of specific module names that are expected to fail.

       This differs from EXCLUDE because those modules aren't imported at all,
       but the modules in EXPECTED_TO_FAIL must exist, are imported, and then
       must fail when imported.
    """

    def test_all(self):
        paths = self.PROJECT_PATHS or self._guess_paths()
        with warning_context(self.WARNINGS_ACTION):
            _, failures = import_all(
                *paths, include=self.INCLUDE, exclude=self.EXCLUDE
            )

        failing_modules = [module for module, ex in failures]
        self.assertEqual(failing_modules, sorted(self.EXPECTED_TO_FAIL))

    def _guess_paths(self):
        sourcefile = inspect.getsourcefile(self.__class__)
        path = python_path(os.path.dirname(sourcefile))

        for c in os.listdir(path):
            if has_init_file(c) and not c.startswith('__'):
                yield c


def import_all(*paths, include=None, exclude=None):
    """
    Try to import all .py files and directories below each path in `paths`;

    Returns a pair of sorted lists `(successes, failures)`.
       `successes` is a list of module names that successfully imported

       `failures` is a list of (module name, exception) pairs for modules that
        failed to import
    """
    imports = sorted(_all_imports(paths))
    successes, failures = [], []
    for module in _filter_imports(imports, include, exclude):
        try:
            importlib.import_module(module)
            successes.append(module)
        except Exception as e:
            failures.append((module, e))

    return successes, failures


@contextlib.contextmanager
def warning_context(action):
    """A context manager to set `warnings.simplefilter` within a scope"""
    warnings.simplefilter(action)
    try:
        yield
    finally:
        warnings.filters.pop(0)


@contextlib.contextmanager
def sys_path_context(path):
    """A context manager to prepend to `sys.path` within a scope"""
    sys.path.insert(0, path)
    try:
        yield
    finally:
        try:
            sys.path.remove(path)
        except Exception:
            pass  # Someone else removed it - not an issue.


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


def walk_code(path, omit_prefixes=('__', '.')):
    """
    os.walk through subdirectories and files, ignoring any that begin
    with any of the strings in `omit_prefixes`
    """
    for directory, sub_dirs, files in os.walk(path):
        if any(directory.startswith(p) for p in omit_prefixes):
            sub_dirs.clear()
        else:
            yield directory, files


def _all_imports(paths):
    for path in paths:
        root = python_path(path)
        with sys_path_context(root):
            for directory, files in walk_code(path):
                rel = os.path.relpath(directory, root)
                module = '.'.join(split_all(rel))
                yield module

                for f in files:
                    if f.endswith('.py') and not f.startswith('__'):
                        yield '%s.%s' % (module, f[:-3])


def _filter_imports(imports, include, exclude):
    include_re = include and [re.compile(i) for i in include]
    exclude_re = exclude and [re.compile(i) for i in exclude]

    for i in imports:
        if exclude_re is not None and any(r.match(i) for r in exclude_re):
            continue
        if include_re is not None and not any(r.match(i) for r in include_re):
            continue
        yield i


if __name__ == '__main__':
    args = sys.argv[1:] or [os.getcwd()]
    successes, failures = import_all(*args)
    if successes:
        print('Successes', *successes, sep='\n  ')
        print()

    if failures:
        failures = ['%s (%s)' % (m, e) for (m, e) in failures]
        print('Failures', *failures, sep='\n  ')
        print()
