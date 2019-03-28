import importlib, os, warnings
__all__ = 'import_all', 'python_root'


__author__ = "Tom Ritchford <tom@swirly.com>"
__version__ = "0.9.0"


def import_all(root, ignore_warnings=False):
    """
    Try to import all .py files and directories below `root` and return a list
    of successes and a list of failures.

    Arguments:
      root:
        Root directory for the top-level Python module

      ignore_warnings:
          If `ignore_warnings` is True, ignore all warnings.
          If `ignore_warnings` is False, turn warnings into errors.
          Otherwise, turn warnings into errors unless the module
          name is in `ignore_warnings`

    """
    successes, failures = [], []

    for name in _all_imports(root):
        warnings.simplefilter('ignore' if name in ignore_warnings else 'error')

        try:
            importlib.import_module(name)
        except Exception as e:
            failures.append((name, e))
        else:
            successes.append(name)

        warnings.filters.pop(0)

    return successes, failures


def python_root(path):
    """
    Return the lowest directory containing path that does not contain
    an __init__.py file
    """

    while os.path.exists(os.path.join(path, '__init__.py')):
        path = os.path.dirname(path)

    return path


def _split_all(path):
    result = []
    old_path = None
    while path != old_path:
        (path, tail), old_path = os.path.split(path), path
        tail and result.insert(0, tail)
    return result


def _all_imports(path):
    root = python_root(path)
    sys.path.insert(0, root)

    try:
        for directory, sub_folders, files in os.walk(path):
            if os.path.basename(directory).startswith('__'):
                continue

            relative = os.path.relpath(directory, root)
            root_import = '.'.join(_split_all(relative))

            yield root_import

            for f in files:
                if f.endswith('.py') and not f.startswith('__'):
                    yield '%s.%s' % (root_import, f[:-3])
    finally:
        try:
            sys.path.remove(root)
        except:
            pass
