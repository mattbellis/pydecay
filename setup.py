#!/usr/bin/env python

from distutils.core import setup

setup(name='pydecay',
    version='1.0',
    description='PyDecay HEP analysis package',
    author='Jesse Dunietz and Matt Bellis',
    author_email='matthew.bellis@gmail.com',
    url='http://code.google.com/p/pydecay/',
    packages=['pydecay','pydecay/db',\
            'pydecay/converters',\
            'pydecay/db/dict_impl',\
            'pydecay/db/django_impl',
            'pydecay/db/django_impl/pydecaydb'
            ],
    )
