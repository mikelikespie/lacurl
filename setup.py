#!/usr/bin/env python

from setuptools import setup, find_packages, Extension, Feature

import sys

VERSION = '0.0.5'
DESCRIPTION = "Lazy Asynchronous Wrapper for cURL"
LONG_DESCRIPTION = """
lacurl is a simple wrapper for MultiCurl which also provides an
interface similar to to urlopen. It is lightweight and can handle
tens or hundreds of sumltaneous requests.

It also includes a lazy evaluation wrapper, and a simple json.load
wrapper which allows not only asynchronous url loading, but lazy
function evaluation as well.

The goal of this library was to make asynchronous URL fetching easy
and almost a drop-in replacement for urllib.
"""
CLASSIFIERS="""
License :: OSI Approved :: BSD License
Intended Audience :: Developers
Development Status :: 3 - Alpha
Topic :: Software Development :: Libraries :: Python Modules
""".splitlines()

setup(
        name="lacurl",
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        author="Daniel Robert Farina",
        author_email="dfarina@gmail.com",
        url="http://lolrus.org",
        license="BSD License",
        packages=find_packages(exclude=['ez_setup']),
        platforms=['any'],
        install_requires = ['pycurl>=7.19.0'],
        )

