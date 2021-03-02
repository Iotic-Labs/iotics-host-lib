# Copyright (c) 2020 Iotic Labs Ltd. All rights reserved.
import glob
from os.path import abspath, dirname, join

from setuptools import setup

PKGDIR = abspath(dirname(__file__))
with open(join(PKGDIR, 'VERSION')) as version_file:
    VERSION = version_file.read().strip()

if __name__ == '__main__':
    setup(version=VERSION,
          package_data={'iotics': glob.glob("template/**", recursive=True)})
