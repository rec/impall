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
anywhere in a project - it looks like this:

.. code-block:: python

    import import_all


    class ImportAllTest(import_all.ImportAllTest):
        pass

and most of the time that's all you need.

Overriding properties
=============================

ImportAllTest has eight properties that can be overridden.

  * ALL_SUBDIRECTORIES: Whether to search all subdirectories
  * CATCH_EXCEPTIONS: Catch all exceptions and report at the end
  * EXCLUDE: Which modules to exclude
  * EXPECTED_TO_FAIL: Which modules are expected to fail
  * INCLUDE: Which modules to exclude
  * PROJECT_PATHS: Roots for searching subdirectories
  * SKIP_PREFIXES: Skip subdirectories that start with these prefixes
  * WARNINGS_ACTION: What to do on warnings

Documentation for all the properties is `here
<https://github.com/rec/import_all/blob/master/import_all.py#L18-L133>`_.

To permanently override a test property, set it in the derived class, like
this:

.. code-block:: python

    import import_all


    class ImportAllTest(import_all.ImportAllTest):
        WARNINGS_ACTION = 'error'


To temporarily override a test property, set an environment variable before
runnning the test, like this:

.. code-block:: bash

    $ _IMPORT_ALL_WARNINGS_ACTION=error pytest

Using ``import_all.py`` as a standalone program

The file ``import_all.py`` is executable and is installed in the path by
``pip``.  You can use it on projects that you are evaluation or debugging
like this:

.. code-block:: bash

    $ import_all.py [directory ..directory]

where if no directory is specified it uses the current directory.

You can use environment variables to set properties as above and for convenience
there are also command line flags for each property, so you can write:

.. code-block:: bash

    $ import_all.py --catch_exceptions --all_directories --exclude=foo/bar
