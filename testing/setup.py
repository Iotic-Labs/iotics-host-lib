# Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
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
from os.path import abspath, dirname, join

from setuptools import setup

PKGDIR = abspath(dirname(__file__))
with open(join(PKGDIR, 'VERSION')) as version_file:
    VERSION = version_file.read().strip()


if __name__ == '__main__':
    setup(version=VERSION)
