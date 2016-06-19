from setuptools import setup

from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(name='tabbed_backend',
      packages=['tabbed_backend', ],
      version='0.1.0',
      description='Tabbed backends for Matplotlib',
      long_description=long_description,
      author='Federico Ariza',
      author_email='ariza.federico@gmail.com',
      classifiers=['Programming Language :: Python :: 3.4'],
      )
