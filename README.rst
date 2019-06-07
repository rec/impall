``import_all``: Automatically import everything
-------------------------------------------------------------

A three-line unit test in your project automatically imports
every Python file and module in it, optionally testing for warnings.

Why?
=====

Not every file is covered by unit tests; and unit tests won't report any new
warnings that occur.

``import_all`` is a single-file library with a unit test that automatically
imports every Python file and module in your project.

I drop ``include_all`` into each new project.  It takes seconds, it inevitably
catches lots of dumb problems early, and it requires no maintenance.


How to use ``import_all``
==============================

Install it with ``pip install import_all``, and use it by adding
`this tiny file <https://github.com/rec/import_all/blob/master/all_test.py>`_
(`raw <https://raw.githubusercontent.com/rec/import_all/master/all_test.py>`_)
anywhere in your project - it looks like this:

.. code-block:: python

    import import_all


    class ImportAllTest(import_all.TestCase):
        pass

and most of the time that's all you need.

Overriding attributes
=============================

You can override these attributes in :

  * ALL_SUBDIRECTORIES:
  * CATCH_EXCEPTIONS:
  * EXCLUDE:
  * EXPECTED_TO_FAIL:
  * INCLUDE:
  * PROJECT_PATHS:
  * SKIP_PREFIXES:
  * WARNINGS_ACTION:


Also by default, `Python warnings
<https://docs.python.org/3/library/warnings.html#the-warnings-filter>`_ are
treated as errors.

You can easily customize those defaults and a few more by redefining one of the
variables listed `here
<https://github.com/rec/import_all/blob/master/import_all.py#L18-L41>`_ inside
your test class.

For example, to fail on warnings:

.. code-block:: python

    import import_all


    class ImportAllTest(import_all.TestCase):
        WARNINGS_ACTION = 'error'
