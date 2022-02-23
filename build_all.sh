#!/usr/bin/env bash
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
set -x

if [ -z "$VERSION" ]; then
  echo "VERSION env variable must be set"
  exit 1
fi
set -u

pushd "$(cd -P -- "$(dirname -- "$0")" && pwd -P)" > /dev/null

DIST_DIR=$(pwd)/dist
mkdir -p "$DIST_DIR"
rm -rf "${DIST_DIR:?}"/*
PKG_DIR=$(pwd)/iotic.lib.qapi

# ensure we have a valid python package with __init__.py in all sub-directories
INIT_CONTENT='# For pkgutil namespace compatibility only. Must NOT contain anything else. See also:
# https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
'

for setup_file in $(find $(pwd) -name 'setup.py'); do
  PKG_DIR=$(dirname $setup_file)
  find $PKG_DIR/iotic -type d -exec sh -c "echo \"$INIT_CONTENT\" > {}/__init__.py" \;

  # Create the VERSION file
  echo $VERSION > $PKG_DIR/VERSION

  # Package Wheel and sdist
  pushd $PKG_DIR
  python3 setup.py -q clean -a 2> /dev/null
  python3 setup.py sdist -d $DIST_DIR
  python3 setup.py bdist_wheel -d $DIST_DIR
  popd
  twine check "$DIST_DIR"/*
done
popd > /dev/null
