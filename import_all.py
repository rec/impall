#!/usr/bin/env python3

import importlib
import inspect
import os
import sys
import unittest
import warnings

__author__ = 'Tom Ritchford <tom@swirly.com>'
__version__ = '0.9.3'

"""A unit test that individually imports every module in a Python repository.
"""


class ImportAllTest(unittest.TestCase):
    """Import every Python module or file and fail on errors or warnings.

    Derive from this class within your own project and most of the time
    you are done.

    Tests can be customized by overriding one of these seven properties,
    documented individually below: ALL_SUBDIRECTORIES, CATCH_EXCEPTIONS,
    EXCLUDE, EXPECTED_TO_FAIL, INCLUDE, PROJECT_PATHS, SKIP_PREFIXES,
    and WARNINGS_ACTION.

    There are two ways to override a property:

    * You can permanently override it in your test class,

    * You can temporarily override it by setting an environment
    variable `_IMPORT_ALL_<property name>`

    For example, to turn warnings into errors, either set the property
    WARNINGS_ACTION it in your class definition like this:

        class ImportAllTest(import_all.ImportAllTest):
            WARNINGS_ACTION = 'error'

    or set the environment variable _IMPORT_ALL_WARNINGS_ACTION=True before
    running the tests - perhaps like this:

        _IMPORT_ALL_WARNINGS_ACTION=error pytest

    The properties INCLUDE, EXCLUDE, PROJECT_PATH and SKIP_PREFIXES can be
    lists of strings, or a string separated with colons like
        'foo.mod1:foo.mod2'

    NOTE: to reduce side-effects, `sys.modules` is restored to its
    original condition after each import, but there might be other
    side-effects from loading some specific module.

    Use the EXCLUDE property to exclude modules with undesirable side
    effects. In general, it is probably a bad idea to have significant
    side-effects just from loading a module.
    """

    ALL_SUBDIRECTORIES = False

    """If True, search all subdirectories.

    If False, stop searching with subdirectories that do not contain an
    __init__.py file.

    By default, the test attempts to import every Python module and file
    reachable from its Python root directory.  This means ``import_all``
    does not load .py files in subdirectories which contain .py files
    but not a __init__.py file.

    This turns out to be what you want most of the time, but if you want
    import absolutely everything, set the ALL_SUBDIRECTORIES property
    to be True.  If you want to import more specically, you can use the
    test properties EXCLUDE, INCLUDE or PROJECT_PATHS.
    """

    CATCH_EXCEPTIONS = False
    """If CATCH_EXCEPTIONS is False, the first exception will stop the
    test entirely and print a stack trace

    If True, all exceptions will be caught and reported on at the end.
    This is most useful when adding this to a new codebase with a lot of
    import problems.
    """

    EXCLUDE = None
    """A list of modules names, or None.

    Modules that appear in EXCLUDE will not be imported at all.
    EXCLUDE isn't recursive - you need to list each module you want to exclude.
    """

    EXPECTED_TO_FAIL = ()
    """A list of specific module names that are expected to fail.

    This differs from EXCLUDE because modules in EXCLUDE aren't
    imported at all, but the modules in EXPECTED_TO_FAIL must exist, are
    imported, and then must fail when imported.
    """

    INCLUDE = None
    """A list of module names, or None.

    If non-empty, exactly the modules in the list will be loaded.
    INCLUDE isn't recursive - you need to list each module you want to include.
    """

    PROJECT_PATHS = None
    """A list or tuple of path roots that will be recusively loaded.

    If empty, guess PROJECT_PATHS from the root Python directory that
    contains the definition of the class.
    """

    SKIP_PREFIXES = '__', '.'
    """Any directory which starts with a prefix from SKIP_PREFIXES is ignored
    """

    WARNINGS_ACTION = 'default'
    """A string telling what to do if a Python warning occurs.

    Possible choices are: default, error, ignore, always, module, once

    `warnings.simplefilter` is set to this value while testing: see
    https://docs.python.org/3/library/warnings.html#the-warnings-filter
    for more details.
    """

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._read_env_variables()

        self._exc = _list(self.EXCLUDE)
        self._inc = _list(self.INCLUDE)

    @staticmethod
    def properties():
        props = set(dir(ImportAllTest)) - set(dir(unittest.TestCase))
        return [a for a in props if a.isupper() and not a.startswith('_')]

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
        paths = self.PROJECT_PATHS
        paths = _list(paths or self._guess_paths())

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
                        if (
                            self.CATCH_EXCEPTIONS
                            or module in self.EXPECTED_TO_FAIL
                        ):
                            failures.append((module, e))
                        else:
                            raise
                    sys.modules.clear()
                    sys.modules.update(sys_modules)
        finally:
            warnings.filters.pop(0)
        return successes, failures

    def _guess_paths(self):
        sourcefile = inspect.getsourcefile(__class__)
        path = _python_path(os.path.dirname(sourcefile))

        for c in os.listdir(path):
            if _has_init_file(c) and not c.startswith('__'):
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
                and not _has_init_file(directory)
            ):
                sub_dirs.clear()
            else:
                yield directory, files

    def _accept(self, x):
        return (
            not x.startswith('.')
            and x not in self._exc
            and (not self._inc or x in self._inc)
        )

    def _read_env_variables(self):
        for name in self.properties():
            env_name = ENV_PREFIX + name
            value = os.environ.get(env_name)
            if not value:
                continue

            try:
                cvalue = self._convert_variable(name, value)
            except Exception:
                err = 'Cannot understand env var %s="%s"' % (name, value)
                raise ValueError(err)

            setattr(self, name, cvalue)

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


ENV_PREFIX = '_IMPORT_ALL_'
ENV_SEPARATOR = ':'

"""ENV_PREFIX is used when setting test properties using environment
variables.  This is convenient for temporarily turning features on or
off while debugging.

For example, to turn off catching exceptions, set the environment
variable _IMPORT_ALL_CATCH_EXCEPTIONS=True

To set a boolean test property, use a string starting with t or T for
True, or a string starting with f or F for False; any other string gives
an error.

To set a test property that's a list of strings, separate those strings
with a colon - for example:

_IMPORT_ALL_EXCLUDE=my_project.broken:my_project.experimental
"""


def _has_init_file(path):
    """Return True if `path` is a directory containing an __init__.py file"""
    return os.path.exists(os.path.join(path, '__init__.py'))


def _list(s):
    return s.split(':') if isinstance(s, str) else s or []


def _python_path(path):
    """
    Find the lowest directory in `path` and its parents that does not contain
    an __init__.py file
    """
    while _has_init_file(path):
        path = os.path.dirname(path)

    return path


def _report(args, file=sys.stdout):
    test_case = ImportAllTest()
    paths, values = _split_args(args)
    test_case.__dict__.update(values)

    test_case.PROJECT_PATHS = list(test_case.PROJECT_PATHS or []) + paths

    successes, failures = test_case.import_all()
    if successes:
        print('Successes', *successes, sep='\n  ', file=file)
        print(file=file)

    if failures:
        failures = ['%s (%s)' % (m, e) for (m, e) in failures]
        print('Failures', *failures, sep='\n  ', file=file)
        print(file=file)


def _split_args(args):
    props = ImportAllTest.properties()

    paths = []
    values = {}
    for a in args:
        if a.startswith('-'):
            name, *rest = a.lstrip('-').split('=', 1)
            cname = name.upper().replace('-', '_')
            if cname not in props:
                print(props)
                raise ValueError('Cannot understand flag', a, cname)
            is_bool = isinstance(getattr(ImportAllTest, cname), bool)

            if rest:
                value = rest[0]
            elif is_bool:
                value = 'True'
            else:
                raise ValueError('Cannot understand flag', a)
            values[cname] = value
        else:
            paths.append(a)

    return paths, values


def _split_path(path):
    """Use os.path.split repeatedly to split a path into components"""
    old_path = None
    components = []

    while path != old_path:
        (path, tail), old_path = os.path.split(path), path
        tail and components.insert(0, tail)

    old_path and components.insert(0, old_path)
    return components


TestCase = ImportAllTest  # DEPRECATED


if __name__ == '__main__':
    args = sys.argv[1:] or [os.getcwd()]
    _report(args)
