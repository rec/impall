import contextlib, importlib, inspect, os, sys, unittest, warnings

__author__ = "Tom Ritchford <tom@swirly.com>"
__version__ = "0.9.2"


class TestCase(unittest.TestCase):
    WARNINGS_ACTION = 'error'
    PROJECT_PATHS = None
    FAILING_MODULES = ()

    def test_all(self):
        paths = self.PROJECT_PATHS or self._guess_paths()
        with warning_context(self.WARNINGS_ACTION):
            errors = import_all(*paths)
        failing_modules = tuple(module for module, ex in errors)
        self.assertEqual(failing_modules, self.FAILING_MODULES)

    def _guess_paths(self):
        sourcefile = inspect.getsourcefile(self.__class__)
        path = python_path(os.path.dirname(sourcefile))

        for c in os.listdir(path):
            if has_init_file(c) and not c.startswith('__'):
                yield c


def import_all(*paths):
    """
    Try to import all .py files and directories below each path in `paths`;
    yields an iterator of (module, exception) for each module that failed
    to import
    """
    return sorted(attempt_all(importlib.import_module, _all_imports(paths)))


def attempt_all(function, items):
    """
    Call `function` on each item in `items`, catching any exceptions.

    Yields an iterator of (item, exception) for each item that raised an
    exception.
    """
    for i in items:
        try:
            function(i)
        except Exception as e:
            yield i, e


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
        except:
            pass


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
