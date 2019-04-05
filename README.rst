``import_all``
-----------------

Automatically test that all modules import successfully
=========================================================

Not every file is covered by unit tests, particularly scripts;  and unit tests
won't report any new warnings that occur.

This tiny library contains a unit test that automatically loads each Python file
or module reachable from your root directory.  Warnings are by default treated
as errors, but you can customize this, and also whitelist certain modules to be
ignored.

I drop this into each new project.  It inevitably catches a host of problems,
particularly when I'm in rapid development and running a subset of tests.

In the most common usage, just add this tiny file
`all_test.py <https://raw.githubusercontent.com/rec/import_all/master/all_test.py/>`_.
anywhere in your unit test directory:

.. code-block:: python

    import import_all


    class ImportAllTest(import_all.TestCase):
        pass

You can customize this by overriding

`all_test.py <https://raw.githubusercontent.com/rec/import_all/master/all_test.py/>`_.
