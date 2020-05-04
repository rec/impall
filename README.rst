``impall``: Automatically import everything
-------------------------------------------------------------

A three-line unit test in your project automatically imports
every Python file and module in it, optionally testing for warnings.

Why?
=====

Not every file is covered by unit tests; and unit tests won't report any new
warnings that occur.

``impall`` is a single-file library with a unit test that automatically
imports every Python file and module in your project.

I drop ``include_all`` into each new project.  It takes seconds, it inevitably
catches lots of dumb problems early, and it requires no maintenance.


How to use ``impall``
==============================

Install it with ``pip install impall``, and use it by adding
`this tiny file <https://github.com/rec/impall/blob/master/all_test.py>`_
(`raw <https://raw.githubusercontent.com/rec/impall/master/all_test.py>`_)
anywhere in a project - it looks like this:

.. code-block:: python

    import impall


    class ImpAllTest(impall.ImpAllTest):
        pass

and most of the time that's all you need.

Overriding properties
=============================

ImpAllTest has eight properties that can be overridden.

  * ALL_SUBDIRECTORIES: Whether to search all subdirectories
  * CATCH_EXCEPTIONS: Catch all exceptions and report at the end
  * EXCLUDE: Which modules to exclude
  * EXPECTED_TO_FAIL: Which modules are expected to fail
  * INCLUDE: Which modules to exclude
  * PROJECT_PATHS: Roots for searching subdirectories
  * SKIP_PREFIXES: Skip subdirectories that start with these prefixes
  * WARNINGS_ACTION: What to do on warnings

Full documentation for each property is `here
<https://github.com/rec/impall/blob/master/impall.py#L18-L133>`_.

To permanently override a test property, set it in the derived class, like
this:

.. code-block:: python

    import impall


    class ImpAllTest(impall.ImpAllTest):
        WARNINGS_ACTION = 'error'


To temporarily override a test property, set an environment variable before
runnning the test, like this:

.. code-block:: bash

    $ _IMPALL_WARNINGS_ACTION=error pytest

Using ``impall.py`` as a standalone program

The file ``impall.py`` is executable and is installed in the path by
``pip``.  You can use it on projects that you are evaluating or debugging
like this:

.. code-block:: bash

    $ impall.py [directory ..directory]

where if no directory is specified it uses the current directory.

You can use environment variables to set properties as above and for convenience
there are also command line flags for each property, so you can write:

.. code-block:: bash

    $ impall.py --catch_exceptions --all_directories --exclude=foo/bar
