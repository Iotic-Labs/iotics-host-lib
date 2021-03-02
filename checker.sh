#!/bin/bash -e

dep=$@
echo "Checking base"
    python -c "from iotics.host.conf.base import DataSourcesConfBase"
echo "base OK"

if [[ $dep =~ "testing" ]]
then
   echo "Checking testing dependency"
   python -c "from iotics.host.testing.qapi import TwinApiTest"
   echo "testing dependency OK"
fi
