from setuptools import setup
import import_all

_classifiers = [
    'Development Status :: 4 - Beta',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Topic :: Software Development :: Libraries',
    'Topic :: Utilities',
]

with open('README.rst', 'r') as fp:
    long_description = fp.read()

setup(name='import_all',
      version=import_all.__version__,
      author='Tom Ritchford',
      author_email='tom@swirly.com',
      url='https://github.com/timedata-org/import_all',
      tests_require=['pytest'],
      py_modules=['import_all'],
      description='Try to import all modules below a given root',
      long_description=long_description,
      license='MIT',
      classifiers=_classifiers,
      keywords=['testing', 'importing'],
      )
