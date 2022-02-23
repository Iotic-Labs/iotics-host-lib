# Copyright 2022 Iotic Labs Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
