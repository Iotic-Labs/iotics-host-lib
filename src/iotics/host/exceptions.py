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
from iotic.web.rest.client.qapi import ApiException


class DataSourcesError(Exception):
    """
    Data sources base exception
    """


class DataSourcesAuthException(DataSourcesError):
    """
    Data sources auth agent exception
    """


class DataSourcesQApiError(DataSourcesError):
    """
    Data sources QAPI exception
    """


class DataSourcesQApiHttpError(DataSourcesQApiError):
    """
    Data sources QAPI Http exception
    """

    def __init__(self, http_error: ApiException):
        super().__init__(http_error.reason)
        self.http_error = http_error


class DataSourcesConfigurationError(DataSourcesError):
    """
    Data sources Configuration exception
    """


class DataSourcesSearchTimeout(DataSourcesError):
    """
    Search timeout exception
    """


class DataSourcesFollowTimeout(DataSourcesError):
    """
    Follow timeout exception
    """


class DataSourcesStompError(DataSourcesError):
    """
    Stomp error message received. This causes stomp to disconnect and reconnect
    """


class DataSourcesStompNotConnected(DataSourcesError):
    """
     Stomp not connected
    """
