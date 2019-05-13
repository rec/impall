``import_all``: Automatically import everything
-------------------------------------------------------------

Not every file is covered by unit tests; and unit tests won't report any new
warnings that occur.

This single-file library contains a unit test that automatically loads every
Python file or module in your project.  Warnings are by default treated as
errors, but you can customize this and several other features.

I drop ``include_all`` into each new project.  It takes seconds, it inevitably
catches lots of dumb problems early, and I very rarely even think about it after
that.

I only have to maintain anything when I'm bringing in some broken or very
special-case module, which I should know about anyway.


Installing and using ``import_all``
--------------------------------------

You can install ``import_all`` with ``pip install import_all`` or if you don't
or can't use ``pip``, you can just copy
`this single file <https://github.com/rec/import_all/blob/master/import_all.py>`_
(`raw <https://raw.githubusercontent.com/rec/import_all/master/import_all.py>`_)
``import_all.py`` into your own project.

To use ``import_all`, you can add the unit test
`this tiny file <https://github.com/rec/import_all/blob/master/all_test.py>`_
(`raw <https://raw.githubusercontent.com/rec/import_all/master/all_test.py>`_)
``all_test.py`` anywhere in your project.  It looks like this:

.. code-block:: python

    import import_all


    class ImportAllTest(import_all.TestCase):
        pass


That test also works perfectly well if you just paste this code into an
existing unit test file.

Defaults and customization
--------------------------------

By default, the test attempts to import every Python module and file reachable
from its Python root directory, catching and saving any exceptions.
If any exceptions were thrown, it will report on all of them them, and the
unit test will fail.

By default, ``import_all` does not load .py files in "script directories":
subdirectories which contain .py files but no __init__.py.  This turns out to
be what you want nearly all the time.

By default, Python warnings are treated as errors.

In your test class, you can easily customize those defaults and more by
defining one of the variables listed
`here <https://github.com/rec/import_all/blob/master/import_all.py#L18-L41`_.

For example, to ignore warnings instead of failing, you would change the code
above to read:

.. code-block:: python

    class ImportAllTest(import_all.TestCase):
        WARNINGS_ACTION = 'ignore'
