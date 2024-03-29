#!/usr/bin/env python3
"""
# 🛎 Test-import all modules 🛎

Individually and separately imports each Python module or file in a project and
reports warnings or failures at the end.

### Running impall as a unit test

Just inherit from the base class and it will
automatically find and import each file, like this.

    import impall

    class ImpAllTest(impall.ImpAllTest):
        pass

(You can copy
[this file](https://github.com/rec/impall/blob/master/all_test.py)
into your project if you like.)

Tests are customized by overriding one of these following properties in the
derived class.

    CLEAR_SYS_MODULES, EXCLUDE, FAILING, INCLUDE, MODULES, PATHS,
    RAISE_EXCEPTIONS, and WARNINGS_ACTION.

For example, to turn warnings into errors, set the property
WARNINGS_ACTION in the derived class definition, like this.

    class ImpAllTest(impall.ImpAllTest):
        WARNINGS_ACTION = 'error'

## Running impall as a command-line utility

    $ impall.py --warnings_action=error
    $ impall.py -w error

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

### A note on side-effects

to reduce side-effects, `sys.modules` is restored to its original
condition after each import if CLEAR_SYS_MODULES is true, but there might be
other side-effects from loading some specific module.

Use the EXCLUDE property to exclude modules with undesirable side
effects. In general, it is probably a bad idea to have significant
side-effects just from loading a module.
"""
import argparse
import fnmatch
import functools
import importlib
import os
import sys
import traceback
import typing as t
import unittest
import warnings
from types import ModuleType

__author__ = 'Tom Ritchford <tom@swirly.com>'
__all__ = 'ImpAllTest', 'path_to_import'

CLEAR_SYS_MODULES = """
If `CLEAR_SYS_MODULES` IS `True`, the default, `sys.modules` is reset after each import.

This takes more time but finds more problems.
"""

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
If MODULES is False, search all subdirectories.

If MODULES is True, the default, do not search subdirectories that do not contain an
__init__.py file.
"""

PATHS = """
A list of paths to search from.

If empty, guess the project paths from the current directory."""

RAISE_EXCEPTIONS = """
If True, stop importing at the first exception and print a stack trace.

If False, the default, all exceptions will be caught and reported on at the end."""

WARNINGS_ACTION = """
Possible choices are: default, error, ignore, always, module, once

`warnings.simplefilter` is set to this value while testing: see
https://docs.python.org/3/library/warnings.html#the-warnings-filter
for more details."""


class ImpAllTest(unittest.TestCase):
    CLEAR_SYS_MODULES = True
    EXCLUDE = None
    FAILING = ()
    INCLUDE = None
    MODULES = True
    PATHS = None
    RAISE_EXCEPTIONS = False
    WARNINGS_ACTION = 'default'

    @functools.cached_property
    def _exc(self) -> t.Callable[[t.Any], bool]:
        return _split_pattern(self.EXCLUDE or ())

    @functools.cached_property
    def _inc(self) -> t.Callable[[t.Any], bool]:
        if self.INCLUDE is None:
            return lambda s: True
        else:
            return _split_pattern(self.INCLUDE)

    def test_all(self) -> None:
        successes, failures = self.impall()
        self.assertTrue(successes or failures, 'No tests were found')
        expected = sorted(_split(self.FAILING))

        failed = [(m, ex) for m, ex in failures if m not in expected]
        failed_to_fail = [m for m in successes if m in expected]

        if failed_to_fail:
            print('Didn\'t fail when expected:', *sorted(failed_to_fail))

        first = True
        for module, ex in failed:
            if first:
                first = False
            else:
                print()
            print(module + ':')
            for line in ex.splitlines():
                if 'File "<' not in line:
                    print(' ', line)

        self.assertTrue(not failed, 'Some tests failed')
        self.assertTrue(not failed_to_fail, 'Some tests failed to fail')

    def impall(self) -> t.Tuple[t.List[str], t.List[t.Tuple[str, str]]]:
        successes: t.List[str] = []
        failures: t.List[t.Tuple[str, str]] = []
        paths = _split(self.PATHS or path_to_import(os.getcwd())[0])

        warnings.simplefilter(self.WARNINGS_ACTION)  # type: ignore[arg-type]
        for file in self._all_imports(paths):
            self._import(file, successes, failures)

        warnings.filters.pop(0)  # type: ignore[attr-defined]
        return successes, failures

    def _all_imports(self, paths: t.Sequence[str]) -> t.Iterator[str]:
        for path in paths:
            for directory, sub_dirs, files in os.walk(path):
                if directory != path and not self._accept_dir(directory):
                    sub_dirs.clear()
                    continue

                if _is_python_dir(directory):
                    yield directory

                for f in files:
                    if f.endswith('.py') and not _is_ignored(f):
                        yield os.path.join(directory, f)

    def _import(self, file: str, successes: t.List[str], failures: t.List[t.Tuple[str, str]]) -> None:
        root, module = path_to_import(file)
        path = file[:-3] if file.endswith('.py') else file

        rel = os.path.relpath(path, os.getcwd())
        if not self._inc(rel) or self._exc(rel):
            return

        importlib.invalidate_caches()
        file_path = os.path.relpath(file, os.getcwd())

        if self.CLEAR_SYS_MODULES:
            saved_modules = dict(sys.modules)

        saved_path = sys.path[:]
        sys.path.insert(0, root)

        try:
            importlib.import_module(module)
        except Exception:
            if self.RAISE_EXCEPTIONS:
                raise
            failures.append((file_path, traceback.format_exc()))
        else:
            successes.append(file_path)
        finally:
            if self.CLEAR_SYS_MODULES:
                for k in set(sys.modules).difference(saved_modules):
                    del sys.modules[k]
                sys.modules.update(saved_modules)
            sys.path[:] = saved_path

    def _accept_dir(self, directory: str) -> bool:
        if self.MODULES:
            return _is_python_dir(directory)
        return not _is_ignored(directory)


@functools.lru_cache()
def path_to_import(path: str) -> t.Tuple[str, str]:
    """
    Return a (path, module) pair that allows you to import the Python file or
    directory at location path
    """
    parts = []

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    path = str(path)  # Might be a Path
    if path.endswith('.py'):
        path = path[:-3]

    def isdir(p: str) -> bool:
        return os.path.isdir(p) and not os.path.exists(p + '.py')

    while not isdir(path) or _is_python_dir(path):
        path, part = os.path.split(path)
        if not part:
            if path:
                parts.append(path)
            break
        parts.append(part)

    return path, '.'.join(reversed(parts))


def import_file(path: str) -> ModuleType:
    """
    Given a path to a file or directory, imports it from the correct root
    and returns the module
    """

    root, module_path = path_to_import(path)
    old_path = sys.path[:]
    sys.path.insert(0, root or '.')

    try:
        return importlib.import_module(module_path)
    finally:
        sys.path[:] = old_path


_PROPERTIES = set(dir(ImpAllTest)) - set(dir(unittest.TestCase))
PROPERTIES = sorted(a for a in _PROPERTIES if a.isupper())

ENV_SEPARATOR = ':'

_NO = 'NO_'


def _is_ignored(path: str) -> bool:
    b = os.path.basename(path)
    return b.startswith('.') or (
        b.startswith('__') and os.path.isdir(path) or b == '__init__.py'
    )


def _is_python_dir(path: str) -> bool:
    """Return True if `path` is a directory containing an __init__.py file"""
    init = os.path.join(path, '__init__.py')
    return os.path.exists(init) and not _is_ignored(path)


def _split(s: t.Union[str, t.Sequence[str]]) -> t.Sequence[str]:
    if not s:
        return []
    if isinstance(s, str):
        return s.split(':')
    return s


def _split_pattern(s: t.Union[str, t.Sequence[str]]) -> t.Callable[[t.Any], bool]:
    parts = _split(s)
    return lambda x: any(fnmatch.fnmatch(x, p) for p in parts)


def report() -> None:
    """Test all files in a directory from the command line"""
    args = _parse_args()
    test_case = ImpAllTest()

    for attr, value in vars(args).items():
        attr = attr.upper()
        if attr.startswith(_NO):
            attr = attr[len(_NO) :]
            value = not value

        default = getattr(test_case, attr, _NO)
        if default is not _NO and (isinstance(value, bool) or value):
            if isinstance(default, (list, tuple)) and isinstance(value, str):
                value = value.split(ENV_SEPARATOR)
            setattr(test_case, attr, value)

    successes, failures = test_case.impall()
    if successes:
        print('Successes', *successes, sep='\n  ')
        print()

    if failures:
        fail = ['%s (%s)' % (m, e) for (m, e) in failures]
        print('Failures', *fail, sep='\n  ', file=sys.stderr)
        print(file=sys.stderr)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=_USAGE)
    parser.add_argument('paths', nargs='*', default=[os.getcwd()])
    kwds: t.Dict[str, t.Any]

    for prop in PROPERTIES:
        default = getattr(ImpAllTest, prop)
        help = globals()[prop]

        if isinstance(default, bool):
            kwds = {'action': 'store_true'}
            if default:
                prop = _NO + prop
        elif isinstance(default, (tuple, list)):
            kwds = {'default': ':'.join(default)}
        else:
            kwds = {'default': default}

        short, long = '-' + prop[0], '--' + prop
        if short == '-N':
            parser.add_argument(long, help=help, **kwds)
        else:
            parser.add_argument(short, long, help=help, **kwds)

    return parser.parse_args()


_USAGE = """
impall.py [path ...path]

   Individually and separately imports each Python file found on or below these
   paths and reports on any failures.

   With no arguments, impall imports all Python files found in
   any Python directory (i.e. with a __init__.py file) below the current
   directory.
"""


if __name__ == '__main__':
    report()
