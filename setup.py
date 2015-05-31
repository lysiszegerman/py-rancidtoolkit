#!/usr/bin/env python

from setuptools import setup, find_packages
import os
import sys

version = "0.5"

if sys.argv[-1] == 'publish':
    os.system('python2.7 setup.py sdist upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

setup(name='rancidtoolkit',
      version=version,
      description='Functions to parse network devices config files and output \
specific data',
      author='Marcus Stoegbauer',
      author_email='ms@man-da.de',
      license='MIT',
      packages=find_packages(),
      classifiers=["Development Status :: 4 - Beta",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Programming Language :: Python"
                   ],
      zip_safe=False)
