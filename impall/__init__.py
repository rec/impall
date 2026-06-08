#!/usr/bin/env python3
"""
# 🛎 Test-import all modules 🛎

Individually and separately imports each Python module or file in a project and
reports warnings or failures at the end.

## Running impall as a unit test

Just inherit from the base class and it will
automatically find and import each file, like this.

    import impall

    class ImpAllTest(impall.ImpAllTest):
        pass

(You can copy
[this file](https://github.com/rec/impall/blob/master/all_test.py)
into your project if you like.)

Tests are customized by overriding one of these following properties in the
derived class

    CLEAR_SYS_MODULES, EXCLUDE, FAILING, INCLUDE, MODULES, PATHS,
    RAISE_EXCEPTIONS, and WARNINGS_ACTION.

These properties have documentation strings in the code below.

For example, to turn warnings into errors, set the property
WARNINGS_ACTION in the derived class definition, like this.

    class ImpAllTest(impall.ImpAllTest):
        WARNINGS_ACTION = 'error'

## Running impall as a command-line utility

    $ impall.py --warnings_action=error
    $ impall.py -w error

## Selecting which files to test

The properties INCLUDE, EXCLUDE, and PATHS can be
lists of string entries, or a string separated with colons like
'foo.mod1:foo.mod2'

Entries in INCLUDE or EXCLUDE match paths using fnmatch.fnmatch.

### A note on side-effects

To reduce side-effects, `sys.modules` is restored to its original
condition after each import if CLEAR_SYS_MODULES is true, but there might be
other side-effects from loading some specific module.

Use the EXCLUDE property to exclude modules with undesirable side
effects.

NOTE: many important modules like numpy and pytorch cannot be reloaded and you
will get a clear exception if this happens.

Setting CLEAR_SYS_MODULES = False will work.
Perhaps this should have been the default, but I can't change it now. :-D

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
A list of patterns to be excluded. Uses fnmatch.fnmatch.
"""

FAILING = """
A list of modules that must fail.
"""

INCLUDE = """
If non-empty, exactly these patterns are included. Uses fnmatch.fnmatch
"""

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

_err = functools.partial(print, file=sys.stderr)


class ImpAllTest(unittest.TestCase):
    CLEAR_SYS_MODULES = True
    EXCLUDE = ()
    FAILING = ()
    INCLUDE = None
    MODULES = True
    PATHS = None
    RAISE_EXCEPTIONS = False
    WARNINGS_ACTION = 'default'
    VERBOSE = False

    @functools.cached_property
    def _exc(self) -> t.Callable[[t.Any], bool]:
        return _split_pattern(self.EXCLUDE, self.paths)

    @functools.cached_property
    def _inc(self) -> t.Callable[[t.Any], bool]:
        if self.INCLUDE is None:
            return lambda x: True
        return _split_pattern(self.INCLUDE, self.paths)

    def test_all(self) -> None:
        successes, failures = self.impall()
        self.assertTrue(successes or failures, 'No tests were found')
        expected = sorted(_split_colon(self.FAILING))

        failed = sorted((m, ex) for m, ex in failures if m not in expected)
        succeeded = sorted(m for m in successes if m in expected)

        if self.VERBOSE:
            for i, (module, ex) in enumerate(failed):
                if i:
                    _err()
                _err(module + ':')
                for line in ex.splitlines():
                    if 'File "<' not in line:
                        _err(' ', line)

        errors = []
        if failed:
            failures = ', '.join(m for (m, _ex) in failed)
            errors.append(f'These modules failed to import: {failures}')
        if succeeded:
            successes = ', '.join(succeeded)
            errors.append(f'These modules unexpectedly did import: {successes}')

        if errors:
            self.fail('\n'.join(errors))

    @functools.cached_property
    def paths(self) -> t.List[str]:
        return _split_colon(self.PATHS or path_to_import(os.getcwd())[0])

    def impall(self) -> t.Tuple[t.List[str], t.List[t.Tuple[str, str]]]:
        successes: t.List[str] = []
        failures: t.List[t.Tuple[str, str]] = []

        warnings.simplefilter(self.WARNINGS_ACTION)
        for file in self._all_imports(self.paths):
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

    def _import(
        self,
        file: str,
        successes: t.List[str],
        failures: t.List[t.Tuple[str, str]],
    ) -> None:
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


@functools.lru_cache
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


def _split_colon(s: t.Union[str, t.Sequence[str]]) -> t.List[str]:
    if not s:
        return []
    if isinstance(s, str):
        return s.split(':')
    return list(s)


def _split_pattern(
    s: t.Union[str, t.Sequence[str]], paths: t.List[str]
) -> t.Callable[[str], bool]:
    def matches(x: str, p: str) -> bool:
        parts = p.split('.')
        if all(s.isidentifier() for s in parts):
            pass  # TODO
        return fnmatch.fnmatch(x, p)

    segments = _split_colon(s)
    return lambda x: any(matches(x, p) for p in segments)


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
        _err('Successes', *successes, sep='\n  ')
        _err()

    if failures:
        fail = [f'{m} ({e})' for (m, e) in failures]
        _err('Failures', *fail, sep='\n  ', file=sys.stderr)
        _err(file=sys.stderr)


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
