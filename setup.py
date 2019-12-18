# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Mirek Simek, VSCHT Praha.
#
# oarepo-references-draft is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module for tracking and updating references in Invenio records."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

OAREPO_VERSION = os.environ.get('OAREPO_VERSION', '3.1.1')

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.3.3',
    'pydocstyle>=2.0.0',
    'pytest-cov>=2.5.1',
    'pytest-pep8>=1.0.6',
    'pytest-invenio>=1.0.5',
    'oarepo[deploy,tests]~={version}'.format(
        version=OAREPO_VERSION),
    'isort>=4.3.0'
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask-BabelEx>=0.9.3',
    'oarepo-invenio-records-draft>=3.0.0',
    'oarepo-references>=1.4.3'
]

packages = find_packages(exclude=['tests', 'sample', 'tests.*', 'sample.*'])

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('oarepo_references_draft', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
version = g['__version__']

setup(
    name='oarepo-references-draft',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    license='MIT',
    author='Mirek Simek, VSCHT Praha',
    author_email='miroslav.simek@vscht.cz',
    url='https://github.com/oarepo/oarepo-references-draft',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'oarepo_references_draft = oarepo_references_draft.ext:OARepoReferencesDraft',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 4 - Beta',
    ],
)
