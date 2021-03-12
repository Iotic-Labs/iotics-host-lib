import os

from setuptools import setup


def get_version():
    # The version environment variable can be used here because this module is not packaged but it is deployed
    # using Docker.
    # Do not use environment variables in setup.py for a packaged module. Those variables will be interpreted each time
    # the package will be installed from the sources (*.tar.gz)
    version = os.environ.get('VERSION')
    if not version:
        raise ValueError('The VERSION environment variable must be set and not empty')
    return version


if __name__ == '__main__':
    setup(version=get_version())
